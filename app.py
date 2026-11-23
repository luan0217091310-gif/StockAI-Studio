"""Entry GUI: khởi động server thread + pywebview (fallback trình duyệt). R-RUN-1, R-SEC-1/2."""

import os
import socket
import sys
import threading
import time
import webbrowser

import stockai  # noqa: F401  — nạp trước uvicorn (vá _multiprocessing nếu bị Application Control chặn)

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


def main(port: int = 8765, use_webview: bool = True, open_browser: bool = True) -> None:
    import uvicorn

    from stockai.server import security
    from stockai.server.api import app

    port = free_port(port)
    security.PORT["value"] = port
    url = f"http://127.0.0.1:{port}/?t={security.APP_TOKEN}"
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    print(f"StockAI Studio đang chạy: {url}")
    print("Lịch chỉ chạy khi ứng dụng đang mở. Nhấn Ctrl+C để thoát.")
    if use_webview and os.environ.get("STOCKAI_NO_WEBVIEW") != "1":
        try:
            import webview

            webview.create_window("StockAI Studio", url, width=1400, height=900, min_size=(1000, 700))
            webview.start()  # main thread (R-RUN-1)
            server.should_exit = True
            return
        except Exception as e:  # noqa: BLE001
            print(f"Không mở được cửa sổ pywebview ({type(e).__name__}: {e}) → mở bằng trình duyệt")
    if open_browser:
        webbrowser.open(url)
    try:
        while th.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.should_exit = True


if __name__ == "__main__":
    main(use_webview="--browser" not in sys.argv)
