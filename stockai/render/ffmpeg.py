"""Chạy ffmpeg/ffprobe (async, có timeout, hủy được) + preflight (Blueprint 9.7)."""

import asyncio
import json
import os
import shutil
from pathlib import Path

from stockai.errors import ConfigError, StockAIError

REQUIRED_FILTERS = ["ass", "zoompan", "showwaves", "xfade", "loudnorm", "overlay", "colorchannelmixer"]
REQUIRED_ENCODERS = ["libx264", "aac"]
INSTALL_HINT = "Windows: winget install Gyan.FFmpeg · macOS: brew install ffmpeg"
_override: dict[str, str] = {}
_procs: set[asyncio.subprocess.Process] = set()


def set_paths(ffmpeg: str | None = None, ffprobe: str | None = None) -> None:
    if ffmpeg:
        _override["ffmpeg"] = ffmpeg
    if ffprobe:
        _override["ffprobe"] = ffprobe


def which(name: str) -> str | None:
    if name in _override and Path(_override[name]).exists():
        return _override[name]
    p = shutil.which(name)
    if p:
        return p
    links = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
    if links.exists():
        return str(links)
    pk = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if pk.exists():
        for exe in pk.glob(f"Gyan.FFmpeg*/**/bin/{name}.exe"):
            return str(exe)
    return None


def _bin(name: str) -> str:
    p = which(name)
    if not p:
        raise ConfigError(f"Không tìm thấy {name}", code="FFMPEG_MISSING", hint=INSTALL_HINT)
    return p


async def run(args: list[str], cwd: Path | None = None, timeout: float = 300, tool: str = "ffmpeg") -> str:
    full = [_bin(tool)] + (["-y", "-hide_banner", "-loglevel", "error"] if tool == "ffmpeg" else []) + args
    proc = await asyncio.create_subprocess_exec(*full, cwd=str(cwd) if cwd else None,
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    _procs.add(proc)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout)
    except (TimeoutError, asyncio.CancelledError):
        proc.kill()
        raise
    finally:
        _procs.discard(proc)
    if proc.returncode != 0:
        raise StockAIError(f"{tool} lỗi (mã {proc.returncode}): {err.decode('utf-8', 'replace')[-800:]}", code="FFMPEG_FAILED")
    return out.decode("utf-8", "replace")


def kill_all() -> None:
    for p in list(_procs):
        try:
            p.kill()
        except ProcessLookupError:
            pass


async def probe(path: Path) -> dict:
    out = await run(["-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], tool="ffprobe", timeout=60)
    return json.loads(out)


async def probe_duration(path: Path) -> float:
    return round(float((await probe(path))["format"]["duration"]), 3)


def preflight_sync() -> dict:
    """Kiểm tra ffmpeg + filter + encoder. Trả dict cho CLI/API."""
    import subprocess

    res = {"ffmpeg": which("ffmpeg"), "ffprobe": which("ffprobe"), "filters": {}, "encoders": {}, "ok": False,
           "hint": INSTALL_HINT}
    if not res["ffmpeg"] or not res["ffprobe"]:
        return res
    flt = subprocess.run([res["ffmpeg"], "-hide_banner", "-filters"], capture_output=True, text=True, encoding="utf-8").stdout
    enc = subprocess.run([res["ffmpeg"], "-hide_banner", "-encoders"], capture_output=True, text=True, encoding="utf-8").stdout
    names = {ln.split()[1] for ln in flt.splitlines() if len(ln.split()) > 2}
    encs = {ln.split()[1] for ln in enc.splitlines() if len(ln.split()) > 2}
    res["filters"] = {f: f in names for f in REQUIRED_FILTERS}
    res["encoders"] = {e: e in encs for e in REQUIRED_ENCODERS}
    ver = subprocess.run([res["ffmpeg"], "-version"], capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    res["version"] = ver[0] if ver else ""
    res["ok"] = all(res["filters"].values()) and all(res["encoders"].values())
    return res
