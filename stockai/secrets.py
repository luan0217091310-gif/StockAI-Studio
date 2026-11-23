"""Wrapper keyring (R-SEC-3). Bí mật KHÔNG bao giờ nằm trong SQLite."""

import re

import keyring
from keyring.errors import KeyringError

SERVICE = "StockAI Studio"
_mem: dict[str, str] = {}  # dự phòng khi máy không có keyring backend


def set_secret(key: str, value: str) -> None:
    try:
        keyring.set_password(SERVICE, key, value)
    except KeyringError:
        _mem[key] = value


def get_secret(key: str) -> str | None:
    try:
        v = keyring.get_password(SERVICE, key)
    except KeyringError:
        v = None
    return v or _mem.get(key)


def delete_secret(key: str) -> None:
    _mem.pop(key, None)
    try:
        keyring.delete_password(SERVICE, key)
    except Exception:
        pass


def mask(v: str | None) -> str | None:
    if not v:
        return None
    return v[:4] + "••••••" + v[-4:] if len(v) > 10 else "••••"


_PATTERNS = [re.compile(r"bot\d+:[\w-]+"), re.compile(r"AIza[\w-]+"), re.compile(r"Bearer \S+"),
             re.compile(r"access_token=\S+")]


def redact(text: str) -> str:
    """R-SEC-5: che token trong log/payload."""
    for p in _PATTERNS:
        text = p.sub("[REDACTED]", text)
    return text


def keyring_backend_name() -> str:
    try:
        return type(keyring.get_keyring()).__name__
    except Exception:
        return "unknown"
