# mypkg/__main__.py
# 當你執行: python -m mypkg 時，這個檔案會被當作入口。
import argparse, json
from pathlib import Path
from . import sum_by_category, set_global_multiplier, GLOBAL_MULTIPLIER

DATA_PATH = Path(__file__).resolve().parent.parent / "data.json"

def main():
    parser = argparse.ArgumentParser(description="Run mypkg as a module")
    parser.add_argument("--multiplier", type=int, default=None)
    args = parser.parse_args()

    data = json.loads(Path(DATA_PATH).read_text(encoding="utf-8"))
    if args.multiplier is not None:
        print(f"[__main__] Before: GLOBAL_MULTIPLIER={GLOBAL_MULTIPLIER}")
        set_global_multiplier(args.multiplier)
        print(f"[__main__] After : GLOBAL_MULTIPLIER={GLOBAL_MULTIPLIER}")

    print("[__main__] Aggregated:", sum_by_category(data))

if __name__ == "__main__":
    main()
