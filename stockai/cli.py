"""CLI: preflight | run | render-sample | serve | db migrate | youtube-login | cleanup."""

import asyncio
import os
import sys

import typer

from stockai import config

app = typer.Typer(help="StockAI Studio — dòng lệnh", no_args_is_help=True, add_completion=False)
db_app = typer.Typer(help="Cơ sở dữ liệu")
app.add_typer(db_app, name="db")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

config.setup_logging()

COLORS = {"INFO": "white", "SUCCESS": "green", "WARN": "yellow", "ERROR": "red", "DEBUG": "bright_black"}


def echo(level: str, msg: str) -> None:
    typer.secho(f"[{level:7}] {msg}", fg=COLORS.get(level, "white"))


def preflight_report() -> tuple[list[tuple[str, bool, str]], bool]:
    from stockai.db.repo import get_repo
    from stockai.render import ffmpeg
    from stockai.secrets import keyring_backend_name

    rows: list[tuple[str, bool, str]] = []
    ff = ffmpeg.preflight_sync()
    rows.append(("FFmpeg", bool(ff["ffmpeg"]), ff.get("version") or ff["hint"]))
    rows.append(("FFprobe", bool(ff["ffprobe"]), ff["ffprobe"] or ff["hint"]))
    for k, v in {**ff["filters"], **ff["encoders"]}.items():
        rows.append((f"  filter/encoder {k}", v, "" if v else ff["hint"]))
    for f in (config.FONT_REGULAR, config.FONT_SEMIBOLD, config.FONT_BOLD):
        rows.append((f"Font {f.name}", f.exists(), "" if f.exists() else "Thiếu file trong assets/fonts"))
    d = config.data_dir()
    try:
        (d / ".probe").write_text("ok")
        (d / ".probe").unlink()
        ok = True
    except OSError:
        ok = False
    rows.append(("Thư mục dữ liệu", ok, str(d)))
    repo = get_repo()
    rows.append(("SQLite", len(repo.tables()) >= 10, f"{len(repo.tables())} bảng · {repo.path}"))
    kb = keyring_backend_name()
    rows.append(("Keyring", "fail" not in kb.lower(), kb))
    from stockai import secrets
    for k in ("gemini_api_key", "telegram_bot_token"):
        v = secrets.get_secret(k)
        rows.append((f"Khóa {k}", bool(v), "đã cấu hình" if v else "chưa cấu hình (tùy chọn)"))
    critical = all(r[1] for r in rows if not r[0].startswith("Khóa"))
    return rows, critical


@app.command()
def preflight():
    """Kiểm tra môi trường: FFmpeg + filter, font, thư mục dữ liệu, keyring."""
    rows, ok = preflight_report()
    for name, good, note in rows:
        typer.secho(f"{'✔' if good else '✖'} {name:32} {note}", fg="green" if good else ("yellow" if name.startswith("Khóa") else "red"))
    typer.secho("\nMôi trường SẴN SÀNG" if ok else "\nMôi trường CHƯA đủ — xem các dòng đỏ", fg="green" if ok else "red", bold=True)
    raise typer.Exit(0 if ok else 1)


@app.command()
def run(mode: str = typer.Option("demo", help="demo | production"),
        session: str = typer.Option("ADHOC", help="PRE_MARKET | POST_MARKET | ADHOC"),
        step: str = typer.Option(None, help="collect | edit | voice | render (dừng sau bước này)"),
        offline: bool = typer.Option(False, help="Không dùng mạng; mọi provider dùng fixture"),
        no_publish: bool = typer.Option(False, "--no-publish", help="Bỏ qua bước xuất bản"),
        platforms: str = typer.Option("telegram", help="Danh sách nền tảng, ngăn cách dấu phẩy")):
    """Chạy pipeline 5 bước."""
    if offline:
        os.environ["STOCKAI_OFFLINE"] = "1"
    from stockai.pipeline.orchestrator import get_orchestrator

    stop = {"collect": 1, "edit": 2, "voice": 3, "render": 4}.get(step or "")

    async def main():
        o = get_orchestrator()
        o.repo.mark_interrupted()
        o.echo = echo
        jid = await o.start(session_type=session.upper(), mode=mode.upper(), offline=offline, skip_publish=no_publish,
                            stop_after=stop, platforms=platforms.split(","))
        await o.wait()
        return o.repo.get_job(jid)

    job = asyncio.run(main())
    typer.secho(f"\nJob {job['id']} · {job['status']}", bold=True, fg="green" if job["status"] in ("COMPLETED", "WAITING_APPROVAL") else "red")
    typer.echo(f"Thư mục: {job['artifacts_dir']}")
    if job["final_video_path"]:
        typer.echo(f"Video:   {job['final_video_path']}")
    raise typer.Exit(0 if job["status"] in ("COMPLETED", "WAITING_APPROVAL") else 1)


@app.command("render-sample")
def render_sample():
    """Render mẫu 8 giây để kiểm tra filtergraph (offline)."""
    from datetime import date

    from stockai.render.sample import render_sample as rs

    out = asyncio.run(rs(date.today()))
    typer.secho(f"OK: {out}", fg="green")


@app.command()
def serve(port: int = 8765, browser: bool = True):
    """Chạy backend + mở giao diện trong trình duyệt (không cần pywebview)."""
    from app import main as app_main

    app_main(port=port, use_webview=False, open_browser=browser)


@app.command()
def cleanup(older_than_days: int = 30):
    """Xóa outputs cũ hơn N ngày."""
    from stockai.server.api import cleanup_outputs

    typer.echo(cleanup_outputs(older_than_days))


@app.command("youtube-login")
def youtube_login(client_secret: str):
    """Đăng nhập YouTube (OAuth installed-app), lưu token vào keyring."""
    from stockai.providers.publish.youtube import login

    typer.echo(login(client_secret))


@db_app.command("migrate")
def db_migrate():
    """Tạo/nâng cấp cơ sở dữ liệu."""
    from stockai.db.repo import get_repo

    r = get_repo()
    typer.secho(f"OK · {len(r.tables())} bảng · {r.path}", fg="green")


if __name__ == "__main__":
    app()
