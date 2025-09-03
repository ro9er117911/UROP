# viz.py
# 讀取 data.json，彙總後用 matplotlib 畫出 bar chart。
import json
from pathlib import Path
import matplotlib.pyplot as plt

DATA_PATH = Path(__file__).resolve().parent / "data.json"
OUT_PATH = Path(__file__).resolve().parent / "category_totals.png"

def main():
    items = json.loads(Path(DATA_PATH).read_text(encoding="utf-8"))
    # 簡單彙總
    totals = {}
    for it in items:
        c = it.get("category", "Unknown")
        totals[c] = totals.get(c, 0) + int(it.get("value", 0))

    # 單一圖表（不指定顏色與樣式）
    labels = list(totals.keys())
    values = [totals[k] for k in labels]

    plt.figure()
    plt.bar(labels, values)
    plt.title("Category Totals")
    plt.xlabel("Category")
    plt.ylabel("Total Value")
    plt.tight_layout()
    plt.savefig(OUT_PATH)

if __name__ == "__main__":
    main()
