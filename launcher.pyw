"""Khởi động không cửa sổ console bằng pythonw.exe gốc của uv (lối tắt Desktop/Start Menu/Startup trỏ vào đây).

Nạp site-packages của .venv bằng site.addsitedir (xử lý cả file .pth của gói editable stockai).
"""

import os
import site
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
site.addsitedir(str(ROOT / ".venv" / "Lib" / "site-packages"))
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
os.environ.setdefault("STOCKAI_DATA_DIR", str(ROOT / "data"))
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

try:
    import app

    app.main(use_webview="--browser" not in sys.argv, tray_only="--tray" in sys.argv)
except Exception:  # ghi lỗi khởi động ra file vì không có console
    import traceback

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "launcher_error.log").write_text(traceback.format_exc(), encoding="utf-8")
    raise
