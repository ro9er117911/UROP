# py-git-vars-demo

練習要點：
- `__init__.py`：匯出套件 API（被 `import mypkg` 時執行）。
- `__main__.py`：以模組形式執行 `python -m mypkg` 的入口。
- `app.py`：一般腳本，使用 `if __name__ == "__main__":` 作為執行入口。
- 區域變數 vs 全域變數：在 `mypkg/core.py` 示範。

## 指令速查
```bash
# 執行腳本
python app.py --multiplier 2

# 以模組執行（觸發 mypkg/__main__.py）
python -m mypkg --multiplier 3
```
