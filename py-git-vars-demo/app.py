# app.py
# 一般腳本入口：python app.py --multiplier 4
import argparse, json
from pathlib import Path
from mypkg import (
    sum_by_category,
    set_global_multiplier,
    GLOBAL_MULTIPLIER,
    SCOPE_DEMO,
    scope_shadowing,
    scope_modify_global,
)

DATA_PATH = Path(__file__).resolve().parent / "data.json"

def load_data(path=DATA_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    parser = argparse.ArgumentParser(description="Demo app.py with globals & locals")
    parser.add_argument("--multiplier", type=int, default=None)
    args = parser.parse_args()

    data = load_data()
    print(f"[app] Initially GLOBAL_MULTIPLIER={GLOBAL_MULTIPLIER}, SCOPE_DEMO={SCOPE_DEMO!r}")

    if args.multiplier is not None:
        set_global_multiplier(args.multiplier)
        print(f"[app] After set_global_multiplier: GLOBAL_MULTIPLIER={GLOBAL_MULTIPLIER}")

    print("[app] scope_shadowing() ->", scope_shadowing())
    print("[app] After shadowing: SCOPE_DEMO still =", SCOPE_DEMO)
    print("[app] scope_modify_global() ->", scope_modify_global())
    print("[app] After modify_global: SCOPE_DEMO =", SCOPE_DEMO)

    result = sum_by_category(data)
    print("[app] Aggregated:", result)

if __name__ == "__main__":
    main()
