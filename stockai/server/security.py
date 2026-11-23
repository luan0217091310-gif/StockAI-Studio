"""Token phiên + kiểm tra Origin (R-SEC-1, R-SEC-2, R-SEC-4)."""

import secrets as pysecrets
from pathlib import Path

from fastapi import HTTPException, Request

APP_TOKEN = pysecrets.token_urlsafe(32)
PORT = {"value": 8765}


def allowed_origins() -> set[str]:
    p = PORT["value"]
    return {f"http://127.0.0.1:{p}", f"http://localhost:{p}"}


def check_origin(origin: str | None) -> None:
    if origin and origin not in allowed_origins():
        raise HTTPException(status_code=403, detail="Origin không được phép")


async def require_token(request: Request) -> None:
    check_origin(request.headers.get("origin"))
    tok = request.headers.get("x-app-token") or request.query_params.get("token")
    if not tok or not pysecrets.compare_digest(tok, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Thiếu hoặc sai X-App-Token")


def safe_path(base: Path, *parts: str) -> Path:
    """Chống path traversal: đường dẫn phải nằm trong base."""
    p = base.joinpath(*parts).resolve()
    if not p.is_relative_to(base.resolve()):
        raise HTTPException(status_code=403, detail="Đường dẫn không hợp lệ")
    return p
