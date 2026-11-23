"""Entry GUI: server thread + cửa sổ pywebview (fallback trình duyệt) + icon khay. R-RUN-1, R-SEC-1/2, M8.

Tham số:
  --browser   mở bằng trình duyệt thay vì cửa sổ riêng
  --tray      chạy ẩn trong khay hệ thống (dùng khi tự khởi động cùng Windows); bấm icon để mở
"""

import os
import socket
import sys
import threading
import time
import webbrowser

if sys.stdout is None:  # pythonw.exe: không có console → tránh lỗi khi print/log
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115

import stockai  # noqa: E402,F401  — nạp trước uvicorn (vá _multiprocessing nếu bị Application Control chặn)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def free_port(preferred: int = 8765) -> int:
    for p in [preferred] + list(range(preferred + 1, preferred + 50)):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main(port: int = 8765, use_webview: bool = True, open_browser: bool = True, tray_only: bool = False) -> None:
    from stockai import desktop

    running = desktop.existing_instance()
    if running:  # đã có phiên chạy → chỉ mở giao diện, không tạo server/lịch thứ hai
        print(f"StockAI Studio đã chạy: {running}")
        if not tray_only:
            webbrowser.open(running)
        return

    import uvicorn

    from stockai.server import security
    from stockai.server.api import app

    port = free_port(port)
    security.PORT["value"] = port
    url = f"http://127.0.0.1:{port}/?t={security.APP_TOKEN}"
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning", log_config=None))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(150):
        if server.started:
            break
        time.sleep(0.1)
    desktop.write_lock(port, url)
    print(f"StockAI Studio đang chạy: {url}")
    print("Lịch chỉ chạy khi ứng dụng đang mở (icon ở khay hệ thống).")
    stop = threading.Event()

    def quit_app():
        server.should_exit = True
        stop.set()

    tray = desktop.start_tray(lambda: webbrowser.open(url), quit_app)
    try:
        if not tray_only and use_webview and os.environ.get("STOCKAI_NO_WEBVIEW") != "1":
            try:
                import webview

                webview.create_window("StockAI Studio", url, width=1400, height=900, min_size=(1000, 700))
                webview.start()  # main thread (R-RUN-1). Đóng cửa sổ → vẫn chạy nền trong khay nếu có khay
                if tray is None:
                    return
                open_browser = False
            except Exception as e:  # noqa: BLE001
                print(f"Không mở được cửa sổ pywebview ({type(e).__name__}: {e}) → mở bằng trình duyệt")
        if open_browser and not tray_only:
            webbrowser.open(url)
        while th.is_alive() and not stop.is_set():
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.should_exit = True
        if tray is not None:
            try:
                tray.stop()
            except Exception:  # noqa: BLE001
                pass
        desktop.clear_lock()
        th.join(timeout=5)


if __name__ == "__main__":
    main(use_webview="--browser" not in sys.argv, tray_only="--tray" in sys.argv)
