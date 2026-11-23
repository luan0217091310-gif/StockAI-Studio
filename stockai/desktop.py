"""M8 — tích hợp desktop Windows: icon, khay hệ thống, một phiên duy nhất, lối tắt, tự khởi động cùng Windows.

Không dùng PyInstaller: máy có Application Control chặn exe không ký → chạy bằng pythonw.exe gốc của uv
(đã ký, không bị chặn) + launcher.pyw nạp site-packages của .venv. Xem DECISIONS.md.
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from stockai import config

ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "StockAI Studio"


def icon_path() -> Path:
    """Tạo (một lần) icon .ico: nền xanh đậm + nến tăng xanh lá + chữ S."""
    p = config.data_dir() / "stockai.ico"
    if p.exists():
        return p
    from PIL import Image, ImageDraw

    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 8, 248, 248), 48, fill=(15, 32, 64))
    for x, top, bot, col in ((60, 140, 200, (229, 72, 77)), (118, 90, 180, (34, 197, 94)), (176, 50, 150, (34, 197, 94))):
        d.line((x + 10, top - 20, x + 10, bot + 20), fill=col, width=6)
        d.rectangle((x, top, x + 20, bot), fill=col)
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    return p


# ---------- một phiên duy nhất ----------
def _lock_file() -> Path:
    return config.data_dir() / "running.json"


def existing_instance() -> str | None:
    """Trả URL của phiên đang chạy (nếu còn sống), ngược lại None."""
    f = _lock_file()
    if not f.exists():
        return None
    try:
        info = json.loads(f.read_text(encoding="utf-8"))
        with urllib.request.urlopen(info["url"], timeout=3) as r:
            if r.status == 200 and b"StockAI" in r.read(4000):
                return info["url"]
        return None
    except Exception:  # noqa: BLE001
        return None


def write_lock(port: int, url: str) -> None:
    _lock_file().write_text(json.dumps({"port": port, "url": url, "pid": os.getpid()}), encoding="utf-8")


def clear_lock() -> None:
    try:
        f = _lock_file()
        if f.exists() and json.loads(f.read_text(encoding="utf-8")).get("pid") == os.getpid():
            f.unlink()
    except Exception:  # noqa: BLE001
        pass


# ---------- lối tắt + tự khởi động ----------
def pythonw() -> Path:
    """pythonw.exe của Python gốc (home trong .venv/pyvenv.cfg) — không phải bản trong .venv (bị App Control chặn)."""
    cfg = ROOT / ".venv" / "pyvenv.cfg"
    if cfg.exists():
        for ln in cfg.read_text(encoding="utf-8").splitlines():
            if ln.strip().startswith("home"):
                p = Path(ln.split("=", 1)[1].strip()) / "pythonw.exe"
                if p.exists():
                    return p
    return Path(sys.executable).with_name("pythonw.exe")


def startup_dir() -> Path:
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _make_shortcut(lnk: Path, args: str) -> None:
    lnk.parent.mkdir(parents=True, exist_ok=True)
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
          f"$s.TargetPath='{pythonw()}';$s.Arguments='\"{ROOT / 'launcher.pyw'}\" {args}';"
          f"$s.WorkingDirectory='{ROOT}';$s.IconLocation='{icon_path()}';$s.Description='{APP_NAME}';$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def autostart_lnk() -> Path:
    return startup_dir() / f"{APP_NAME}.lnk"


def autostart_enabled() -> bool:
    return autostart_lnk().exists()


def set_autostart(on: bool) -> None:
    if on:
        _make_shortcut(autostart_lnk(), "--tray")  # khởi động ẩn trong khay để lịch chạy đúng giờ
    elif autostart_lnk().exists():
        autostart_lnk().unlink()


def install_shortcuts(autostart: bool = False) -> list[Path]:
    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop" / f"{APP_NAME}.lnk"
    menu = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / f"{APP_NAME}.lnk"
    for lnk in (desktop, menu):
        _make_shortcut(lnk, "")
    set_autostart(autostart)
    return [desktop, menu] + ([autostart_lnk()] if autostart else [])


# ---------- khay hệ thống ----------
def start_tray(open_ui, quit_app):
    """Chạy icon khay ở luồng riêng (backend win32 của pystray chạy được ngoài main thread)."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        return None

    def toggle(icon, item):
        set_autostart(not autostart_enabled())

    menu = pystray.Menu(
        pystray.MenuItem("Mở StockAI Studio", lambda i, it: open_ui(), default=True),
        pystray.MenuItem("Tự khởi động cùng Windows", toggle, checked=lambda it: autostart_enabled()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Thoát (dừng lịch tự động)", lambda i, it: (i.stop(), quit_app())),
    )
    icon = pystray.Icon("stockai", Image.open(icon_path()), f"{APP_NAME} — lịch đang chạy", menu)
    icon.run_detached()
    return icon
