# mypkg/__init__.py
# 此檔在 "import mypkg" 時會執行。這裡匯出套件要給外界使用的函數/變數。
from .core import (
    sum_by_category,
    set_global_multiplier,
    GLOBAL_MULTIPLIER,
    SCOPE_DEMO,
    scope_shadowing,
    scope_modify_global,
)

__all__ = [
    "sum_by_category",
    "set_global_multiplier",
    "GLOBAL_MULTIPLIER",
    "SCOPE_DEMO",
    "scope_shadowing",
    "scope_modify_global",
]
