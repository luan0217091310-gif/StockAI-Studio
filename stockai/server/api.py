"""FastAPI app + routers (Blueprint Mục 11)."""

import asyncio
import hashlib
import json
import shutil
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from stockai import config, secrets
from stockai.errors import StockAIError
from stockai.pipeline.events import bus
from stockai.pipeline.orchestrator import PLATFORMS, get_orchestrator
from stockai.scheduler import Scheduler
from stockai.server.security import APP_TOKEN, check_origin, require_token, safe_path

VN = ZoneInfo(config.TZ)
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.setup_logging()
    orch = get_orchestrator()
    n = orch.repo.mark_interrupted()  # R-RUN-4
    state["orch"], state["interrupted"] = orch, n
    sch = Scheduler(orch)
    if not state.get("no_scheduler"):
        sch.start()
    state["scheduler"] = sch
    state["preflight"] = await asyncio.to_thread(_preflight)
    yield
    sch.shutdown()


app = FastAPI(title="StockAI Studio", lifespan=lifespan)


@app.exception_handler(StockAIError)
async def _err(_: Request, e: StockAIError):
    status = 409 if e.code == "JOB_RUNNING" else 404 if e.code == "NOT_FOUND" else 400
    return JSONResponse(e.to_dict(), status_code=status)


@app.exception_handler(HTTPException)
async def _http(_: Request, e: HTTPException):
    return JSONResponse({"error": {"code": str(e.status_code), "message": e.detail, "hint": None}}, status_code=e.status_code)


def _preflight() -> dict:
    from stockai.cli import preflight_report

    rows, ok = preflight_report()
    return {"ok": ok, "items": [{"name": n.strip(), "ok": g, "note": note} for n, g, note in rows]}


def orch():
    return state["orch"]


def repo():
    return state["orch"].repo


auth = [Depends(require_token)]


# ---------------- trang chính ----------------
@app.get("/", response_class=HTMLResponse)
async def index():
    # Token KHÔNG nhúng vào HTML; cửa sổ mở /?t={token} và UI đọc từ URL (R-SEC-2)
    return HTMLResponse((config.UI_DIR / "index.html").read_text(encoding="utf-8"))


app.mount("/ui", StaticFiles(directory=str(config.UI_DIR)), name="ui")
app.mount("/fonts", StaticFiles(directory=str(config.FONTS_DIR)), name="fonts")


# ---------------- trạng thái ----------------
@app.get("/api/status", dependencies=auth)
async def status():
    r = repo()
    nxt = state["scheduler"].next_run() if state.get("scheduler") else None
    last = r.one("SELECT * FROM content_jobs WHERE market_snapshot_id IS NOT NULL OR data_quality IS NOT NULL ORDER BY created_at DESC LIMIT 1")
    market = None
    if last and last["artifacts_dir"] and (Path(last["artifacts_dir"]) / "market.json").exists():
        m = json.loads((Path(last["artifacts_dir"]) / "market.json").read_text(encoding="utf-8"))
        bars = m.pop("bars", None) or []
        m["spark"] = [b["close"] for b in bars[-30:]]  # sparkline 30 phiên cho thẻ VN-Index
        market = m
    return {
        "mode": r.get_setting("mode"), "running_job": orch().current_job,
        "next_run_at": nxt.isoformat() if nxt else None,
        "next_run_in_s": int((nxt - datetime.now(VN)).total_seconds()) if nxt else None,
        "preflight_ok": state.get("preflight", {}).get("ok"), "market": market,
        "videos": r.one("SELECT COUNT(*) n FROM content_jobs WHERE final_video_path IS NOT NULL")["n"],
        "waiting": r.one("SELECT COUNT(*) n FROM content_jobs WHERE status='WAITING_APPROVAL'")["n"],
        "cost_month_usd": r.one("SELECT COALESCE(SUM(est_cost_usd),0) s FROM content_jobs WHERE run_date >= ?",
                                (datetime.now(VN).strftime("%Y-%m-01"),))["s"],
        "interrupted": state.get("interrupted", 0),
    }


@app.get("/api/preflight", dependencies=auth)
async def preflight():
    state["preflight"] = await asyncio.to_thread(_preflight)
    return state["preflight"]


# ---------------- pipeline ----------------
class RunBody(BaseModel):
    mode: str | None = None
    session_type: str = "ADHOC"
    platforms: list[str] = ["telegram"]
    dry_run: bool = False
    skip_publish: bool = False
    offline: bool | None = None


@app.post("/api/pipeline/run", dependencies=auth, status_code=202)
async def run(b: RunBody):
    jid = await orch().start(session_type=b.session_type, mode=b.mode, platforms=b.platforms, dry_run=b.dry_run,
                             skip_publish=b.skip_publish, offline=b.offline)
    return {"job_id": jid}


@app.post("/api/pipeline/cancel", dependencies=auth)
async def cancel():
    return {"cancelled": await orch().cancel()}


# ---------------- jobs ----------------
def _job_out(j: dict) -> dict:
    j = dict(j)
    for k in ("script_json", "news_ids_json"):
        if j.get(k):
            j[k.replace("_json", "")] = json.loads(j[k])
    return j


@app.get("/api/jobs", dependencies=auth)
async def jobs(limit: int = 50, offset: int = 0, status: str | None = None):
    return [_job_out(j) for j in repo().list_jobs(limit, offset, status)]


@app.get("/api/jobs/{job_id}", dependencies=auth)
async def job(job_id: str):
    j = repo().get_job(job_id)
    if not j:
        raise HTTPException(404, "Không tìm thấy job")
    out = _job_out(j)
    d = Path(j["artifacts_dir"])
    out["news"] = json.loads((d / "news.json").read_text(encoding="utf-8")) if (d / "news.json").exists() else []
    out["artifacts"] = sorted(p.name for p in d.iterdir() if p.is_file()) if d.exists() else []
    out["publish_logs"] = repo().publish_logs(job_id)
    out["events"] = repo().events(job_id)
    pp = d / "publish_preview.json"
    out["publish_preview"] = json.loads(pp.read_text(encoding="utf-8")) if pp.exists() else None
    return out


class JobEdit(BaseModel):
    video_title: str | None = None
    social_post_text: str | None = None


@app.put("/api/jobs/{job_id}", dependencies=auth)
async def edit_job(job_id: str, b: JobEdit):
    import unicodedata

    if not repo().get_job(job_id):
        raise HTTPException(404, "Không tìm thấy job")
    fields = {k: unicodedata.normalize("NFC", v) for k, v in b.model_dump().items() if v is not None}
    if "video_title" in fields and len(fields["video_title"]) > 80:
        raise HTTPException(400, "Tiêu đề tối đa 80 ký tự")
    if "social_post_text" in fields:
        t = fields["social_post_text"]
        miss = [x for x in (config.DISCLAIMER, config.AI_DECLARATION) if x not in t]
        if miss:
            raise HTTPException(400, "Bài đăng phải giữ câu miễn trừ và dòng khai báo AI (R-LEGAL-1/4)")
        bad = [p for p in config.BANNED_PHRASES if p in t.lower()]
        if bad:
            raise HTTPException(400, f"Bài đăng chứa cụm từ cấm: {', '.join(bad)}")
    repo().update_job(job_id, **fields)
    return {"ok": True}


class ApproveBody(BaseModel):
    platforms: list[str]
    privacy: dict[str, str] = {}
    dry_run: bool = False


@app.post("/api/jobs/{job_id}/approve", dependencies=auth)
async def approve(job_id: str, b: ApproveBody):
    j = repo().get_job(job_id)
    if not j or j["status"] != "WAITING_APPROVAL":
        raise HTTPException(400, "Job không ở trạng thái chờ duyệt")
    return {"results": await orch().publish(job_id, [p for p in b.platforms if p in PLATFORMS], b.privacy, b.dry_run)}


@app.post("/api/jobs/{job_id}/publish", dependencies=auth)
async def republish(job_id: str, b: ApproveBody):
    j = repo().get_job(job_id)
    if not j or not j["final_video_path"]:
        raise HTTPException(400, "Job chưa có video")
    return {"results": await orch().publish(job_id, [p for p in b.platforms if p in PLATFORMS], b.privacy, b.dry_run)}


class RetryBody(BaseModel):
    from_step: int | None = None


@app.post("/api/jobs/{job_id}/retry", dependencies=auth, status_code=202)
async def retry(job_id: str, b: RetryBody):
    return {"job_id": await orch().retry(job_id, b.from_step)}


@app.delete("/api/jobs/{job_id}", dependencies=auth)
async def delete_job(job_id: str):
    j = repo().get_job(job_id)
    if not j:
        raise HTTPException(404, "Không tìm thấy job")
    if j["status"] in ("RUNNING", "PUBLISHING"):
        raise HTTPException(409, "Job đang chạy")
    out_root = config.data_dir() / "outputs"
    d = Path(j["artifacts_dir"]).resolve()
    if d.is_relative_to(out_root.resolve()):
        shutil.rmtree(d, ignore_errors=True)
    repo().delete_job(job_id)
    return {"ok": True}


# ---------------- media (Range) ----------------
@app.get("/media/{job_id}/{filename}")
async def media(job_id: str, filename: str, request: Request, token: str | None = None):
    await require_token(request)
    j = repo().get_job(job_id)
    if not j:
        raise HTTPException(404, "Không tìm thấy job")
    p = safe_path(Path(j["artifacts_dir"]), filename)
    if not p.exists():
        raise HTTPException(404, "Không có file")
    return FileResponse(p)  # Starlette hỗ trợ HTTP Range


@app.get("/asset/{asset_id}")
async def asset_file(asset_id: int, request: Request):
    await require_token(request)
    a = repo().one("SELECT * FROM assets WHERE id=?", (asset_id,))
    if not a:
        raise HTTPException(404, "Không có tài nguyên")
    return FileResponse(safe_path(config.data_dir(), Path(a["path"]).resolve().relative_to(config.data_dir().resolve()).as_posix()))


# ---------------- assets ----------------
@app.post("/api/assets/upload", dependencies=auth)
async def upload(kind: str = Form(...), file: UploadFile = File(...), consent_subject_name: str | None = Form(None),
                 consent_relation: str | None = Form(None), consent_statement: str | None = Form(None)):
    if kind not in ("avatar", "logo", "bgm"):
        raise HTTPException(400, "kind phải là avatar | logo | bgm")
    if kind == "avatar" and not (consent_subject_name and consent_relation in ("SELF", "AUTHORIZED") and consent_statement):
        raise HTTPException(400, "Ảnh chân dung bắt buộc có xác nhận đồng ý (R-LEGAL-3)")
    data = await file.read()
    if len(data) > 30 * 1024 * 1024:
        raise HTTPException(400, "File quá lớn (>30 MB)")
    ext = Path(file.filename or "").suffix.lower() or (".mp3" if kind == "bgm" else ".png")
    allowed = {"avatar": {".png", ".jpg", ".jpeg", ".webp"}, "logo": {".png", ".jpg", ".jpeg", ".webp"}, "bgm": {".mp3", ".m4a", ".wav"}}
    if ext not in allowed[kind]:
        raise HTTPException(400, f"Định dạng không hỗ trợ: {ext}")
    sha = hashlib.sha256(data).hexdigest()
    dest = config.data_dir() / "user_assets" / f"{kind}_{sha[:12]}{ext}"
    dest.write_bytes(data)
    w = h = dur = None
    if kind in ("avatar", "logo"):
        from PIL import Image

        with Image.open(dest) as im:
            w, h = im.size
    else:
        from stockai.render import ffmpeg

        dur = await ffmpeg.probe_duration(dest)
    aid = repo().add_asset(kind, str(dest), sha, w, h, dur)
    warn = None
    if kind == "avatar":
        repo().add_consent(aid, consent_subject_name, consent_relation, consent_statement)
        if w and w < 720:
            warn = f"Ảnh chỉ rộng {w}px (< 720px), chất lượng có thể kém"
    return {"id": aid, "width": w, "height": h, "duration_s": dur, "warning": warn}


@app.get("/api/assets", dependencies=auth)
async def assets():
    out = {}
    for k in ("avatar", "logo", "bgm"):
        a = repo().active_asset(k)
        if a:
            a["consent"] = repo().consent_for(a["id"]) if k == "avatar" else None
        out[k] = a
    return out


@app.delete("/api/assets/{kind}", dependencies=auth)
async def deactivate_asset(kind: str):
    repo().x("UPDATE assets SET is_active=0 WHERE kind=?", (kind,))
    return {"ok": True}


class TTSBody(BaseModel):
    voice: str = "vi-VN-HoaiMyNeural"
    rate: str = "+5%"
    text: str | None = None


@app.post("/api/tts/preview", dependencies=auth)
async def tts_preview(b: TTSBody):
    from stockai.providers.tts.edge import EdgeTTSProvider
    from stockai.text.vi_normalize import normalize_for_tts

    text = normalize_for_tts(b.text or "Xin chào, đây là bản tin chứng khoán của StockAI Studio. VN-Index tăng 0,97% trong phiên hôm nay.")
    key = hashlib.sha1(f"{b.voice}|{b.rate}|{text}".encode()).hexdigest()[:16]
    d = config.data_dir() / "temp" / "tts_preview" / key
    if not (d / "voice.mp3").exists():
        d.mkdir(parents=True, exist_ok=True)
        await EdgeTTSProvider().synthesize(text, b.voice, b.rate, d)
    return {"url": f"/tts/{key}", "text": text}


@app.get("/tts/{key}")
async def tts_file(key: str, request: Request):
    await require_token(request)
    return FileResponse(safe_path(config.data_dir() / "temp" / "tts_preview", key, "voice.mp3"), media_type="audio/mpeg")


# ---------------- schedules ----------------
class ScheduleBody(BaseModel):
    name: str
    session_type: str = "PRE_MARKET"
    cron_hour: int
    cron_minute: int
    days_of_week: str = "mon-fri"
    target_platforms: list[str] = ["telegram"]
    require_approval: bool = True
    is_active: bool = True


@app.get("/api/schedules", dependencies=auth)
async def schedules():
    rows = repo().schedules()
    for s in rows:
        j = repo().get_job(s["last_job_id"]) if s["last_job_id"] else None
        s["last_status"] = j["status"] if j else None
        js = state["scheduler"].sched.get_job(f"schedule-{s['id']}") if state.get("scheduler") else None
        nrt = getattr(js, "next_run_time", None) if js else None
        s["next_run_at"] = nrt.isoformat() if nrt else None
    return rows


def _sched_args(b: ScheduleBody):
    if not (0 <= b.cron_hour <= 23 and 0 <= b.cron_minute <= 59):
        raise HTTPException(400, "Giờ/phút không hợp lệ")
    plats = [p for p in b.target_platforms if p in PLATFORMS] or ["telegram"]
    approval = 1 if (b.require_approval or "tiktok" in plats) else 0
    return (b.name, b.session_type, b.cron_hour, b.cron_minute, b.days_of_week, json.dumps(plats), approval, int(b.is_active))


@app.post("/api/schedules", dependencies=auth)
async def create_schedule(b: ScheduleBody):
    sid = repo().x("INSERT INTO schedules(name, session_type, cron_hour, cron_minute, days_of_week, target_platforms_json, "
                   "require_approval, is_active) VALUES (?,?,?,?,?,?,?,?)", _sched_args(b))
    state["scheduler"].sync()
    return {"id": sid}


@app.put("/api/schedules/{sid}", dependencies=auth)
async def update_schedule(sid: int, b: ScheduleBody):
    repo().x("UPDATE schedules SET name=?, session_type=?, cron_hour=?, cron_minute=?, days_of_week=?, target_platforms_json=?, "
             "require_approval=?, is_active=? WHERE id=?", (*_sched_args(b), sid))
    state["scheduler"].sync()
    return {"ok": True}


@app.delete("/api/schedules/{sid}", dependencies=auth)
async def delete_schedule(sid: int):
    repo().x("UPDATE content_jobs SET schedule_id=NULL WHERE schedule_id=?", (sid,))
    repo().x("DELETE FROM schedules WHERE id=?", (sid,))
    state["scheduler"].sync()
    return {"ok": True}


# ---------------- settings ----------------
@app.get("/api/settings", dependencies=auth)
async def get_settings():
    return repo().all_settings()


@app.put("/api/settings", dependencies=auth)
async def put_settings(body: dict):
    for k, v in body.items():
        if k not in config.DEFAULT_SETTINGS and k not in config.SECRET_KEYS:
            continue
        if k in config.SECRET_KEYS and (v is None or "••" in str(v)):
            continue  # giữ nguyên giá trị đang che
        if k in config.SECRET_KEYS and v == "":
            secrets.delete_secret(k)
            continue
        repo().set_setting(k, str(v))
    from stockai.render import ffmpeg

    ffmpeg.set_paths(repo().get_setting("ffmpeg_path"), repo().get_setting("ffprobe_path"))
    return repo().all_settings()


@app.get("/api/settings/production-check", dependencies=auth)
async def production_check():
    r = repo()
    missing = []
    if not (secrets.get_secret("ssi_consumer_id") and secrets.get_secret("ssi_consumer_secret")):
        missing.append("Nguồn dữ liệu hợp lệ: SSI FastConnect (quyết định D1)")
    if not (secrets.get_secret("gemini_api_key") or secrets.get_secret("openai_api_key")):
        missing.append("Khóa LLM (Gemini hoặc OpenAI-compatible)")
    a = r.active_asset("avatar")
    if not a or a["is_placeholder"]:
        missing.append("Ảnh chân dung thật + bản ghi đồng ý (R-LEGAL-3)")
    if not any(secrets.get_secret(k) for k in ("telegram_bot_token", "facebook_page_token", "youtube_oauth_token", "tiktok_access_token")):
        missing.append("Ít nhất một kênh đăng đã cấu hình")
    if not state.get("preflight", {}).get("ok"):
        missing.append("Preflight FFmpeg/font chưa đạt")
    return {"missing": missing, "ready": not missing}


@app.post("/api/settings/test/{service}", dependencies=auth)
async def test_service(service: str):
    r = repo()
    try:
        if service == "telegram":
            from stockai.providers.publish.telegram import TelegramPublisher
            ok, msg = await TelegramPublisher(r.get_setting("telegram_chat_id")).check_credentials()
        elif service == "facebook":
            from stockai.providers.publish.facebook import FacebookPublisher
            ok, msg = await FacebookPublisher(r.get_setting("facebook_page_id"), r.get_setting("facebook.graph_version")).check_credentials()
        elif service == "youtube":
            from stockai.providers.publish.youtube import YouTubePublisher
            ok, msg = await YouTubePublisher().check_credentials()
        elif service == "tiktok":
            from stockai.providers.publish.tiktok import TikTokPublisher
            ok, msg = await TikTokPublisher().check_credentials()
        elif service == "gemini":
            key = secrets.get_secret("gemini_api_key")
            if not key:
                return {"ok": False, "message": "Chưa có khóa"}
            from google import genai
            client = genai.Client(api_key=key)
            names = [m.name async for m in await client.aio.models.list()]
            want = r.get_setting("llm.model")
            ok = any(want in n for n in names)
            msg = f"Khóa hợp lệ · {len(names)} model · {'có' if ok else 'KHÔNG thấy'} {want}"
        elif service == "ssi":
            from stockai.providers.market.ssi_fc import SsiFastConnectProvider
            bars = await SsiFastConnectProvider().fetch_daily("VNINDEX", 25)
            ok, msg = True, f"Nhận {len(bars)} phiên, gần nhất {bars[-1].date}"
        elif service == "fal":
            ok = bool(secrets.get_secret("fal_key"))
            msg = "Đã có khóa fal (kiểm tra thật khi chạy job PRODUCTION)" if ok else "Chưa có khóa"
        elif service == "heygen":
            ok = bool(secrets.get_secret("heygen_api_key"))
            msg = "Đã có khóa (adapter v3 chưa kiểm chứng)" if ok else "Chưa có khóa"
        else:
            raise HTTPException(404, "Dịch vụ không hỗ trợ")
    except StockAIError as e:
        ok, msg = False, e.message
    except Exception as e:  # noqa: BLE001
        ok, msg = False, secrets.redact(f"{type(e).__name__}: {e}")[:300]
    return {"ok": ok, "message": msg}


# ---------------- bảo trì ----------------
def cleanup_outputs(days: int) -> dict:
    root = config.data_dir() / "outputs"
    cutoff = datetime.now() - timedelta(days=days)
    freed, removed = 0, 0
    for d in root.glob("*"):
        try:
            if datetime.strptime(d.name, "%Y-%m-%d") < cutoff:
                freed += sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
                shutil.rmtree(d)
                removed += 1
        except ValueError:
            continue
    shutil.rmtree(config.data_dir() / "temp", ignore_errors=True)
    (config.data_dir() / "temp").mkdir(exist_ok=True)
    return {"removed_days": removed, "freed_mb": round(freed / 1e6, 1)}


class CleanupBody(BaseModel):
    older_than_days: int = 30


@app.post("/api/maintenance/cleanup", dependencies=auth)
async def cleanup(b: CleanupBody):
    return cleanup_outputs(b.older_than_days)


@app.post("/api/maintenance/open-folder", dependencies=auth)
async def open_folder(body: dict | None = None):
    import os
    import subprocess
    import sys

    target = config.data_dir()
    if body and body.get("job_id"):
        j = repo().get_job(body["job_id"])
        if j:
            target = Path(j["artifacts_dir"])
    if sys.platform == "win32":
        os.startfile(target)  # noqa: S606
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(target)])
    return {"ok": True, "path": str(target)}


@app.get("/api/maintenance/diagnostics", dependencies=auth)
async def diagnostics():
    log = config.data_dir() / "logs" / "stockai.log"
    tail = log.read_text(encoding="utf-8", errors="replace")[-20000:] if log.exists() else ""
    return {"preflight": state.get("preflight"), "settings": repo().all_settings(), "log_tail": secrets.redact(tail),
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}


# ---------------- WebSocket ----------------
@app.websocket("/ws/events")
async def ws_events(ws: WebSocket, token: str | None = None):
    import secrets as pysecrets

    try:
        check_origin(ws.headers.get("origin"))
    except HTTPException:
        await ws.close(code=4403)
        return
    if not token or not pysecrets.compare_digest(token, APP_TOKEN):
        await ws.close(code=4401)
        return
    await ws.accept()
    q = bus.subscribe()
    try:
        while True:
            ev = await q.get()
            await ws.send_text(json.dumps(ev, ensure_ascii=False, default=str))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        bus.unsubscribe(q)
