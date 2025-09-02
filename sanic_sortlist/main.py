from sanic import Sanic, Blueprint, Request, json as sanic_json, exceptions
from sanic_ext import validate
from pydantic import BaseModel, Field
from typing import Literal, List, Optional
from pathlib import Path
import sqlite3, json, csv, re

# -----------------------------
# 初始化應用與資料載入（Extract）
# -----------------------------
app = Sanic("ETLBackend")
etl_api = Blueprint("etl_api", url_prefix="/etl")

# 用 __file__ 解決「相對路徑」在不同工作目錄啟動會找不到檔的問題
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data.json"

# 將檔案裡的 countries/persons 載入到記憶體（模擬 Staging Layer）
with DATA_PATH.open("r", encoding="utf-8") as f:
    _raw = json.load(f)
COUNTRIES: list[str] = list(_raw.get("countries", []))
PERSONS:   list[str] = list(_raw.get("persons",   []))

# 文字正規化（清理：trim + 大小寫調整）
def norm_text(s: str, mode: Literal["none", "lower", "title"] = "none") -> str:
    s = s.strip()
    if mode == "lower":
        return s.lower()
    if mode == "title":
        return s.title()
    return s

# -----------------------------------
# 模型：用於驗證各 API 的輸入參數（Pydantic）
# -----------------------------------
class GetInfo(BaseModel):
    # 可選：只看哪個集合
    target: Optional[Literal["countries", "persons", "both"]] = "both"

class NormalizeBody(BaseModel):
    target: Literal["countries", "persons", "both"] = "both"
    case: Literal["none", "lower", "title"] = "none"  # 大小寫轉換
    dedup: bool = True                                # 是否去重
    sort: bool = True                                 # 是否排序

class IngestBody(BaseModel):
    new_countries: List[str] = Field(default_factory=list)
    new_persons:   List[str] = Field(default_factory=list)
    case: Literal["none", "lower", "title"] = "none"  # 進料即正規化

class FilterQuery(BaseModel):
    target: Literal["countries", "persons"]           # 要查哪個集合
    prefix: Optional[str] = None                      # 以某字首過濾（大小寫不敏感）
    regex: Optional[str] = None                       # 用正則過濾
    limit: int = 20

class ExportBody(BaseModel):
    target: Literal["countries", "persons", "both"] = "both"
    fmt: Literal["json", "csv"] = "json"              # 匯出格式
    filename: Optional[str] = None                    # 自訂檔名（可不填，系統會生成）

class LoadSqliteBody(BaseModel):
    db_path: Optional[str] = None                     # 自訂 DB 路徑；預設: ./out/etl.db
    clean: bool = True                                # 先清空舊表再重新匯入

class ReloadBody(BaseModel):
    # 從磁碟重讀 data.json（把記憶體的 COUNTRIES / PERSONS 還原）
    confirm: Literal["YES"]


# -----------------------------------
# 1) 檢視資訊（E：Extract 後的快照）
# -----------------------------------
@app.route("/etl/info", methods=["GET"])
@validate(query=GetInfo)  # 使用 GET 時建議用 query
async def etl_info(request: Request, query: GetInfo):
    """
    回傳目前 COUNTRIES / PERSONS 的筆數與前幾個樣本。
    """
    def view(lst: list[str]):
        return {"size": len(lst), "sample": lst[:5]}
    if query.target == "countries":
        return sanic_json({"countries": view(COUNTRIES)})
    if query.target == "persons":
        return sanic_json({"persons": view(PERSONS)})
    return sanic_json({"countries": view(COUNTRIES), "persons": view(PERSONS)})

# -----------------------------------
# 2) 清理 / 去重 / 排序（T：Transform）
# -----------------------------------
@app.route("/etl/normalize", methods=["POST"])
@validate(json=NormalizeBody)
async def etl_normalize(request: Request, body: NormalizeBody):
    """
    對指定集合做正規化（trim + 大小寫），可選去重與排序。
    """
    changed = {"countries": 0, "persons": 0}

    def apply_ops(lst: list[str]) -> list[str]:
        # 文字正規化
        out = [norm_text(x, body.case) for x in lst]
        # 去重（保留相對穩定的順序，可改用 set 但順序會變）
        if body.dedup:
            seen, uniq = set(), []
            for x in out:
                k = x  # 也可用 k = x.lower() 做大小寫不敏感去重
                if k not in seen:
                    seen.add(k)
                    uniq.append(x)
            out = uniq
        # 排序
        if body.sort:
            out = sorted(out, key=str)
        return out

    if body.target in ("countries", "both"):
        before = len(COUNTRIES)
        newlst = apply_ops(COUNTRIES)
        COUNTRIES[:] = newlst
        changed["countries"] = before - len(newlst)

    if body.target in ("persons", "both"):
        before = len(PERSONS)
        newlst = apply_ops(PERSONS)
        PERSONS[:] = newlst
        changed["persons"] = before - len(newlst)

    return sanic_json({"ok": True, "changed": changed})

# -----------------------------------
# 3) 進料 / 合併（T：Transform 的 upsert 口味）
# -----------------------------------
@app.route("/etl/ingest", methods=["POST"])
@validate(json=IngestBody)
async def etl_ingest(request: Request, body: IngestBody):
    """
    將新資料併入既有清單；回傳：新增了哪些、哪些是重複。
    """
    inserted, duplicate = {"countries": [], "persons": []}, {"countries": [], "persons": []}

    # 先建立「正規化視圖」以利快速判斷重複
    c_norm = {norm_text(x, body.case) for x in COUNTRIES}
    p_norm = {norm_text(x, body.case) for x in PERSONS}

    for c in body.new_countries:
        nc = norm_text(c, body.case)
        if nc in c_norm:
            duplicate["countries"].append(c)   # 用原始輸入值回報
        else:
            COUNTRIES.append(nc)               # 以正規化後值入庫
            c_norm.add(nc)
            inserted["countries"].append(nc)

    for p in body.new_persons:
        np = norm_text(p, body.case)
        if np in p_norm:
            duplicate["persons"].append(p)
        else:
            PERSONS.append(np)
            p_norm.add(np)
            inserted["persons"].append(np)

    return sanic_json({"inserted": inserted, "duplicate": duplicate})

# -----------------------------------
# 4) 篩選（T：Transform 的查詢輔助）
# -----------------------------------
@app.route("/etl/filter", methods=["GET"])
@validate(query=FilterQuery)
async def etl_filter(request: Request, query: FilterQuery):
    """
    用 prefix 或 regex 過濾；預設大小寫不敏感；回傳最多 limit 筆。
    """
    src = COUNTRIES if query.target == "countries" else PERSONS
    out = src

    if query.prefix:
        pat = query.prefix.lower()
        out = [x for x in out if x.lower().startswith(pat)]

    if query.regex:
        try:
            rgx = re.compile(query.regex, flags=re.IGNORECASE)
        except re.error as e:
            raise exceptions.InvalidUsage(f"regex 無效：{e}")
        out = [x for x in out if rgx.search(x)]

    return sanic_json({"target": query.target, "count": len(out), "items": out[:query.limit]})

# -----------------------------------
# 5) 匯出（L：Load 到檔案）
# -----------------------------------
@app.route("/etl/export", methods=["POST"])
@validate(json=ExportBody)
async def etl_export(request: Request, body: ExportBody):
    """
    匯出為 JSON/CSV 檔，存放在 ./out/ 目錄；回傳檔名與筆數。
    """
    out_dir = BASE_DIR / "out"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 組合輸出資料
    if body.target == "countries":
        payload = {"countries": COUNTRIES}
    elif body.target == "persons":
        payload = {"persons": PERSONS}
    else:
        payload = {"countries": COUNTRIES, "persons": PERSONS}

    # 檔名
    name = body.filename or f"export_{body.target}.{body.fmt}"
    path = out_dir / name

    if body.fmt == "json":
        with path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        count = sum(len(v) for v in payload.values())
    else:  # csv：每一列一個值，加入欄位 "kind"
        count = 0
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["kind", "value"])
            if "countries" in payload:
                for x in payload["countries"]:
                    writer.writerow(["country", x]); count += 1
            if "persons" in payload:
                for x in payload["persons"]:
                    writer.writerow(["person", x]);   count += 1

    return sanic_json({"ok": True, "saved": str(path), "count": count})

# -----------------------------------
# 6) 匯入 SQLite（L：Load 到資料庫）
# -----------------------------------
@app.route("/etl/load_sqlite", methods=["POST"])
@validate(json=LoadSqliteBody)
async def etl_load_sqlite(request: Request, body: LoadSqliteBody):
    """
    將 COUNTRIES / PERSONS 寫入 SQLite：
    - countries(name TEXT PRIMARY KEY)
    - persons(name TEXT PRIMARY KEY)
    """
    out_dir = BASE_DIR / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    db_path = Path(body.db_path) if body.db_path else (out_dir / "etl.db")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        if body.clean:
            cur.execute("DROP TABLE IF EXISTS countries")
            cur.execute("DROP TABLE IF EXISTS persons")
        cur.execute("CREATE TABLE IF NOT EXISTS countries (name TEXT PRIMARY KEY)")
        cur.execute("CREATE TABLE IF NOT EXISTS persons   (name TEXT PRIMARY KEY)")

        cur.executemany("INSERT OR IGNORE INTO countries(name) VALUES (?)", [(x,) for x in COUNTRIES])
        cur.executemany("INSERT OR IGNORE INTO persons(name)   VALUES (?)", [(x,) for x in PERSONS])
        conn.commit()
    finally:
        conn.close()

    return sanic_json({"ok": True, "db": str(db_path), "sizes": {"countries": len(COUNTRIES), "persons": len(PERSONS)}})

# -----------------------------------
# 7) 從磁碟重載原始 JSON（還原到初始狀態）
# -----------------------------------
@app.route("/etl/reload", methods=["POST"])
@validate(json=ReloadBody)
async def etl_reload(request: Request, body: ReloadBody):
    """
    將記憶體中的 COUNTRIES / PERSONS 還原成 data.json 的內容。
    """
    if body.confirm != "YES":
        raise exceptions.InvalidUsage("請帶入 {'confirm': 'YES'} 以避免誤觸")

    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    COUNTRIES[:] = list(data.get("countries", []))
    PERSONS[:]   = list(data.get("persons",   []))
    return sanic_json({"ok": True, "sizes": {"countries": len(COUNTRIES), "persons": len(PERSONS)}})

# -----------------------------------
# 既有 get_item 範例（照你的風格）
# -----------------------------------
class GetItem(BaseModel):
    index: int

# 寫法不一樣 功能一樣
# @app.get("/get_item")
@app.route("/get_item", methods=["GET"])
@validate(query=GetItem)  # 使用 GET 時建議用 query 
async def get_item(request: Request, query: GetItem):
    _index = int(query.index)
    country, person = None, None

    if 0 <= _index < len(COUNTRIES):
        country = COUNTRIES[_index]
    if 0 <= _index < len(PERSONS):
        person = PERSONS[_index]
    return sanic_json({"country": country, "person": person})

# 啟動
if __name__ == "__main__":
    app.blueprint(etl_api)
    app.run(host="0.0.0.0", port=2020, auto_reload=True, debug=True)
