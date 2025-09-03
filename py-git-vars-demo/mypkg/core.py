# mypkg/core.py
# 示範全域與區域變數，以及資料彙總函數。
from collections import defaultdict

GLOBAL_MULTIPLIER = 2   # 全域變數
SCOPE_DEMO = "global"   # 用於示範遮蔽與 global 關鍵字

def set_global_multiplier(m: int) -> None:
    """用 global 關鍵字修改全域變數。"""
    global GLOBAL_MULTIPLIER
    GLOBAL_MULTIPLIER = int(m)

def scope_shadowing() -> str:
    """區域變數與全域同名（遮蔽），不影響外部 SCOPE_DEMO。"""
    SCOPE_DEMO = "local"
    return SCOPE_DEMO

def scope_modify_global() -> str:
    """真正修改全域 SCOPE_DEMO。"""
    global SCOPE_DEMO
    SCOPE_DEMO = "changed in function"
    return SCOPE_DEMO

def sum_by_category(items, *, multiplier=None):
    """把清單資料依 category 彙總 value，乘上 multiplier（預設用全域）。"""
    m = GLOBAL_MULTIPLIER if multiplier is None else multiplier
    agg = defaultdict(int)
    for it in items:
        cat = it.get("category", "Unknown")
        val = int(it.get("value", 0))
        agg[cat] += val * m
    return dict(agg)
