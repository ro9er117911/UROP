#!/usr/bin/env bash
set -e

# 1) 啟用你列出的 venv
source "/Users/ro9air/Desktop/UROP/.venv/bin/activate"

echo "===== Python & pip ====="
which python
python --version
which pip
pip --version

echo "===== 路徑與平台 ====="
python - <<'PY'
import sys,site,platform
print("sys.executable:", sys.executable)
print("sys.version:", sys.version.split()[0])
print("site.getsitepackages:", site.getsitepackages() if hasattr(site,"getsitepackages") else "N/A")
print("platform:", platform.platform())
PY

echo "===== 執行你的腳本 ====="
python "/Users/ro9air/Desktop/UROP/Untitled-1.py"

echo "✅ 檢查完成"
