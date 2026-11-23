"""PIPELINE ORCHESTRATOR — 5 bước, lock, cancel, resume, manifest (Blueprint 4.2, 9)."""

import asyncio
import hashlib
import json
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from stockai import config, secrets
from stockai.db.repo import Repo, get_repo
from stockai.errors import ConfigError, StockAIError
from stockai.layout import LAYOUT
from stockai.models import MarketSnapshot, NewsItem, PublishOptions, ScriptContext, ScriptOutput, WordTiming
from stockai.pipeline.events import bus
from stockai.render import ffmpeg

log = logging.getLogger("stockai.pipeline")
VN = ZoneInfo(config.TZ)
STEP_RANGE = {1: (0, 20), 2: (20, 35), 3: (35, 70), 4: (70, 95), 5: (95, 100)}
STEP_NAMES = {1: "Thu thập", 2: "AI biên tập", 3: "Giọng & Avatar", 4: "Dựng video", 5: "Xuất bản"}
PLATFORMS = ["telegram", "facebook", "youtube", "tiktok"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class Orchestrator:
    def __init__(self, repo: Repo | None = None):
        self.repo = repo or get_repo()
        self.lock = asyncio.Lock()
        self.task: asyncio.Task | None = None
        self.current_job: str | None = None
        self.echo = None  # callback in ra console (CLI)

    # ---------------- tiện ích sự kiện ----------------
    def emit(self, job_id: str, step: int | None, level: str, message: str, data: dict | None = None) -> None:
        self.repo.add_event(job_id, step, level, message, data)
        bus.publish({"type": "log", "job_id": job_id, "step": step, "level": level, "message": message})
        if self.echo:
            self.echo(level, message)
        log.log(logging.WARNING if level in ("WARN", "ERROR") else logging.INFO, "[%s] %s", job_id[:8], secrets.redact(message))

    async def progress(self, job_id: str, step: int, frac: float) -> None:
        a, b = STEP_RANGE[step]
        pct = int(a + (b - a) * max(0.0, min(1.0, frac)))
        self.repo.update_job(job_id, progress_pct=pct, current_step=step)
        bus.publish({"type": "progress", "job_id": job_id, "step": step, "progress": pct})
        await asyncio.sleep(0)

    def set_status(self, job_id: str, status: str, **kw) -> None:
        self.repo.update_job(job_id, status=status, **kw)
        bus.publish({"type": "job_status", "job_id": job_id, "status": status})

    # ---------------- manifest ----------------
    def manifest(self, job_dir: Path) -> dict:
        f = job_dir / "manifest.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"steps_done": [], "artifacts": {}}

    def save_manifest(self, job_dir: Path, step: int, files: list[str]) -> None:
        m = self.manifest(job_dir)
        if step not in m["steps_done"]:
            m["steps_done"].append(step)
        for name in files:
            p = job_dir / name
            if p.exists():
                m["artifacts"][name] = {"sha256": sha256_file(p), "size": p.stat().st_size, "step": step}
        (job_dir / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")

    def step_done(self, job_dir: Path, step: int) -> bool:
        m = self.manifest(job_dir)
        if step not in m["steps_done"]:
            return False
        return all((job_dir / n).exists() and sha256_file(job_dir / n) == a["sha256"]
                   for n, a in m["artifacts"].items() if a["step"] == step)

    # ---------------- API công khai ----------------
    def is_busy(self) -> bool:
        return self.lock.locked() or self.repo.active_job() is not None

    async def start(self, *, session_type: str = "ADHOC", trigger: str = "MANUAL", schedule_id: int | None = None,
                    mode: str | None = None, platforms: list[str] | None = None, dry_run: bool = False,
                    skip_publish: bool = False, offline: bool | None = None, stop_after: int | None = None,
                    require_approval: bool = True) -> str:
        if self.is_busy():
            raise StockAIError("Đang có job chạy", code="JOB_RUNNING")
        mode = mode or self.repo.get_setting("mode", "DEMO")
        now = datetime.now(VN)
        job_id = str(uuid.uuid4())
        job_dir = config.data_dir() / "outputs" / now.strftime("%Y-%m-%d") / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        self.repo.create_job(job_id, now.strftime("%Y-%m-%d"), session_type, trigger, mode, schedule_id, str(job_dir))
        opts = dict(platforms=platforms or ["telegram"], dry_run=dry_run, skip_publish=skip_publish,
                    offline=config.is_offline() if offline is None else offline, stop_after=stop_after,
                    require_approval=require_approval)
        (job_dir / "run_options.json").write_text(json.dumps(opts), encoding="utf-8")
        self.task = asyncio.create_task(self._run(job_id, job_dir, opts))
        return job_id

    async def retry(self, job_id: str, from_step: int | None = None) -> str:
        job = self.repo.get_job(job_id)
        if not job:
            raise StockAIError("Không tìm thấy job", code="NOT_FOUND")
        if self.is_busy():
            raise StockAIError("Đang có job chạy", code="JOB_RUNNING")
        job_dir = Path(job["artifacts_dir"])
        opts = json.loads((job_dir / "run_options.json").read_text(encoding="utf-8"))
        if from_step:
            m = self.manifest(job_dir)
            m["steps_done"] = [s for s in m["steps_done"] if s < from_step]
            (job_dir / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
        self.repo.update_job(job_id, trigger="RETRY", error_code=None, error_message=None)
        self.task = asyncio.create_task(self._run(job_id, job_dir, opts))
        return job_id

    async def cancel(self) -> bool:
        if self.task and not self.task.done():
            self.task.cancel()
            ffmpeg.kill_all()
            return True
        return False

    async def wait(self) -> None:
        if self.task:
            try:
                await self.task
            except asyncio.CancelledError:
                pass

    # ---------------- chạy ----------------
    async def _run(self, job_id: str, job_dir: Path, opts: dict) -> None:
        from stockai.scheduler import prevent_sleep

        async with self.lock:
            self.current_job = job_id
            prevent_sleep(True)
            job = self.repo.get_job(job_id)
            self.set_status(job_id, "RUNNING", started_at=datetime.now(VN).isoformat(timespec="seconds"))
            self.emit(job_id, 0, "INFO", f"Bắt đầu job {job_id[:8]} · {job['session_type']} · chế độ {job['mode']} · "
                                         f"{'offline' if opts['offline'] else 'online'} · kích hoạt {job['trigger']}")
            try:
                for step, fn in ((1, self.step_collect), (2, self.step_edit), (3, self.step_voice), (4, self.step_render)):
                    if opts.get("stop_after") and step > opts["stop_after"]:
                        self.set_status(job_id, "COMPLETED", completed_at=datetime.now(VN).isoformat(timespec="seconds"))
                        self.emit(job_id, step, "SUCCESS", f"Dừng sau bước {opts['stop_after']} theo yêu cầu")
                        return
                    if self.step_done(job_dir, step):
                        self.emit(job_id, step, "INFO", f"B{step} {STEP_NAMES[step]}: đã có artifact hợp lệ → bỏ qua")
                        continue
                    self.repo.update_job(job_id, current_step=step)
                    result = await fn(job_id, job_dir, opts)
                    if result == "SKIPPED":
                        return
                await self.step_publish(job_id, job_dir, opts)
            except asyncio.CancelledError:
                self.set_status(job_id, "CANCELLED", error_code="CANCELLED", error_message="Người dùng đã hủy")
                self.emit(job_id, None, "WARN", "Job đã bị hủy")
            except StockAIError as e:
                self.set_status(job_id, "FAILED", error_code=e.code, error_message=e.message)
                self.emit(job_id, None, "ERROR", f"{e.code}: {e.message}" + (f" — Gợi ý: {e.hint}" if e.hint else ""))
            except Exception as e:  # noqa: BLE001
                log.exception("job lỗi")
                self.set_status(job_id, "FAILED", error_code="UNEXPECTED", error_message=f"{type(e).__name__}: {e}"[:500])
                self.emit(job_id, None, "ERROR", f"Lỗi không mong đợi: {type(e).__name__}: {e}"[:400])
            finally:
                self.current_job = None
                prevent_sleep(False)
                shutil.rmtree(config.data_dir() / "temp" / job_id, ignore_errors=True)

    # ---------------- B1 ----------------
    async def step_collect(self, job_id: str, job_dir: Path, opts: dict):
        from stockai.providers.market.base import fetch_snapshot
        from stockai.providers.news import rss
        from stockai.render.chart import render_chart

        job = self.repo.get_job(job_id)
        say = lambda lvl, m: self.emit(job_id, 1, lvl, m)  # noqa: E731
        await self.progress(job_id, 1, 0.05)
        say("INFO", "B1 · Thu thập tin RSS (CafeF, Vietstock, VnEconomy)")
        news = await asyncio.wait_for(rss.collect(offline=opts["offline"], emit=say), 30)
        if len(news) < 3:
            raise StockAIError(f"Chỉ có {len(news)} tin phù hợp (cần ≥ 3)", code="NEWS_INSUFFICIENT")
        ids = [self.repo.upsert_news({**n.model_dump(), "published_at": n.published_at.isoformat()}) for n in news]
        say("SUCCESS", f"Giữ {len(news)} tin sau lọc chủ đề + chống trùng + xếp hạng. Top: {news[0].title[:80]}")
        await self.progress(job_id, 1, 0.4)
        order = [s.strip() for s in self.repo.get_setting("market.providers_order", "public_vci,cache,synthetic").split(",")]
        if job["mode"] == "PRODUCTION" and "ssi_fc" not in order:
            order = ["ssi_fc", "csv", "cache"]
        snap = await asyncio.wait_for(fetch_snapshot(order, self.repo.get_setting("market.symbol", "VNINDEX"), job["mode"],
                                                     opts["offline"], self.repo, say), 30)
        snap_id = self.repo.save_snapshot(snap.model_dump(mode="json"))
        if snap.data_quality == "SYNTHETIC":
            say("WARN", "Đang dùng DỮ LIỆU MINH HỌA → watermark trên biểu đồ/video, chặn đăng (R-DATA-2, R-PUB-1)")
        today = datetime.now(VN).date()
        if job["session_type"] == "POST_MARKET" and snap.data_quality == "LIVE" and snap.session_date != today:
            self.set_status(job_id, "SKIPPED", error_message="Hôm nay không có phiên giao dịch")
            say("WARN", "Hôm nay không có phiên giao dịch → SKIPPED")
            return "SKIPPED"
        say("SUCCESS", f"VN-Index {snap.close} ({snap.change_pct:+}%) phiên {snap.session_date:%d/%m/%Y} · SMA20 {snap.sma20} · "
                       f"RSI14 {snap.rsi14} · HT {snap.support20} · KC {snap.resistance20} · nguồn {snap.source} [{snap.data_quality}]")
        await self.progress(job_id, 1, 0.7)
        await asyncio.to_thread(render_chart, snap, job_dir / "chart.png")
        (job_dir / "market.json").write_text(snap.model_dump_json(indent=1), encoding="utf-8")
        (job_dir / "news.json").write_text(json.dumps([n.model_dump(mode="json") for n in news], ensure_ascii=False, indent=1), encoding="utf-8")
        self.repo.update_job(job_id, data_quality=snap.data_quality, market_snapshot_id=snap_id, news_ids_json=json.dumps(ids))
        self.save_manifest(job_dir, 1, ["chart.png", "market.json", "news.json"])
        say("SUCCESS", "Đã vẽ chart.png 1080×660")
        await self.progress(job_id, 1, 1)

    def load_ctx(self, job_id: str, job_dir: Path) -> ScriptContext:
        from stockai.providers.llm.base import hook_style_for

        job = self.repo.get_job(job_id)
        snap = MarketSnapshot.model_validate_json((job_dir / "market.json").read_text(encoding="utf-8"))
        news = [NewsItem(**n) for n in json.loads((job_dir / "news.json").read_text(encoding="utf-8"))]
        rd = datetime.strptime(job["run_date"], "%Y-%m-%d").date()
        return ScriptContext(run_date=rd, session_type=job["session_type"], market=snap, news=news, hook_style=hook_style_for(rd))

    # ---------------- B2 ----------------
    async def step_edit(self, job_id: str, job_dir: Path, opts: dict):
        from stockai.providers.llm.base import generate_checked
        from stockai.providers.llm.template_fallback import TemplateFallbackProvider

        say = lambda lvl, m: self.emit(job_id, 2, lvl, m)  # noqa: E731
        ctx = self.load_ctx(job_id, job_dir)
        say("INFO", f"B2 · AI biên tập · hook hôm nay: “{ctx.hook_style}”")
        await self.progress(job_id, 2, 0.1)
        primary = None
        if not opts["offline"]:
            prov = self.repo.get_setting("llm.provider", "gemini")
            try:
                if prov == "openai_compat":
                    from stockai.providers.llm.openai_compat import OpenAICompatProvider
                    primary = OpenAICompatProvider(self.repo.get_setting("llm.openai_base_url", ""),
                                                   self.repo.get_setting("llm.openai_model", ""), secrets.get_secret("openai_api_key"))
                else:
                    from stockai.providers.llm.gemini import GeminiProvider
                    primary = GeminiProvider(secrets.get_secret("gemini_api_key"), self.repo.get_setting("llm.model", "gemini-3.8-flash"),
                                             self.repo.get_setting("llm.fallback_model"))
            except ConfigError as e:
                say("WARN", f"{e.message} → dùng TemplateFallbackProvider")
        else:
            say("INFO", "Offline → TemplateFallbackProvider (đường chạy chuẩn)")
        out, meta = await asyncio.wait_for(generate_checked(primary, TemplateFallbackProvider(), ctx, say), 180)
        (job_dir / "script.json").write_text(out.model_dump_json(indent=1), encoding="utf-8")
        self.repo.update_job(job_id, script_json=out.model_dump_json(), video_title=out.video_title,
                             social_post_text=out.social_post_text, **meta)
        say("SUCCESS", f"Kịch bản: {len(out.video_script.split())} từ · {len(out.selected_news)} tin · 2 kịch bản · "
                       f"factcheck {'ĐẠT' if meta['factcheck_passed'] else 'LLM không đạt (đã fallback)'} · provider {meta['llm_provider']}")
        self.save_manifest(job_dir, 2, ["script.json"])
        await self.progress(job_id, 2, 1)

    # ---------------- B3 ----------------
    async def step_voice(self, job_id: str, job_dir: Path, opts: dict):
        from stockai.providers.tts.edge import EdgeTTSProvider, OfflineTTSProvider
        from stockai.text.vi_normalize import normalize_for_tts

        say = lambda lvl, m: self.emit(job_id, 3, lvl, m)  # noqa: E731
        job = self.repo.get_job(job_id)
        script = ScriptOutput.model_validate_json((job_dir / "script.json").read_text(encoding="utf-8"))
        text = normalize_for_tts(script.video_script, self.repo.get_setting("tts.number_mode", "engine"))
        voice = self.repo.get_setting("tts.voice", "vi-VN-HoaiMyNeural")
        rate = self.repo.get_setting("tts.rate", "+5%")
        say("INFO", f"B3 · TTS {voice} rate {rate} · văn bản đã chuẩn hóa ({len(text.split())} từ)")
        await self.progress(job_id, 3, 0.05)
        tts = OfflineTTSProvider() if opts["offline"] else EdgeTTSProvider()
        if opts["offline"]:
            say("WARN", "Offline: audio im lặng + mốc thời gian ước lượng (bật mạng để có giọng edge-tts thật)")
        try:
            audio = await asyncio.wait_for(tts.synthesize(text, voice, rate, job_dir, emit=say), 90)
        except StockAIError as e:
            say("WARN", f"{e.message} → dùng mốc thời gian ước lượng, audio im lặng")
            audio = await OfflineTTSProvider().synthesize(text, voice, rate, job_dir)
        if not 45 <= audio.duration_s <= 95:
            pct = int(rate.replace("%", "") or 0)
            new = max(-10, min(20, pct + (10 if audio.duration_s > 95 else -10)))
            say("WARN", f"Audio {audio.duration_s:.1f}s ngoài 45–95s → đọc lại với rate {new:+d}%")
            audio = await tts.synthesize(text, voice, f"{new:+d}%", job_dir, emit=say)
        (job_dir / "words.json").write_text(json.dumps([w.model_dump() for w in audio.words], ensure_ascii=False), encoding="utf-8")
        say("SUCCESS", f"voice.mp3 {audio.duration_s:.1f}s · {len(audio.words)} từ có mốc thời gian · subs.srt + subs.ass")
        await self.progress(job_id, 3, 0.35)
        # ---- avatar ----
        portrait, asset = self.portrait(say)
        prov_name = self.repo.get_setting("avatar.provider", "demo")
        provider = self.avatar_provider(prov_name, job["mode"], asset, audio.duration_s, say)
        from stockai.render.cards import crop_portrait

        crop_portrait(portrait, job_dir / "portrait_1080x976.png", warn=lambda m: say("WARN", m))

        async def on_prog(f, msg):
            await self.progress(job_id, 3, 0.35 + 0.65 * f)

        say("INFO", f"Avatar: {provider.name} (khớp môi: {'có' if provider.has_lipsync else 'không'})")
        res = await asyncio.wait_for(provider.render(job_dir / "portrait_1080x976.png", audio.audio_path,
                                                     (LAYOUT.avatar.w, LAYOUT.avatar.h), job_dir, on_prog), 900)
        self.repo.update_job(job_id, avatar_provider=res.provider, avatar_has_lipsync=int(res.has_lipsync),
                             est_cost_usd=res.cost_usd, duration_s=audio.duration_s)
        self.save_manifest(job_dir, 3, ["voice.mp3", "subs.srt", "subs.ass", "words.json", "avatar.mp4"])
        say("SUCCESS", f"avatar.mp4 1080×976 · 30fps · {res.duration_s:.1f}s · chi phí ${res.cost_usd:.2f}")
        await self.progress(job_id, 3, 1)

    def portrait(self, say) -> tuple[Path, dict | None]:
        from stockai.render.cards import make_placeholder_portrait

        asset = self.repo.active_asset("avatar")
        if asset and Path(asset["path"]).exists():
            if not asset["is_placeholder"] and not self.repo.consent_for(asset["id"]):
                raise ConfigError("Ảnh chân dung chưa có bản ghi đồng ý (R-LEGAL-3)", code="CONSENT_MISSING",
                                  hint="Tab Nhân vật & giọng → tải lại ảnh và tick ô đồng ý")
            say("INFO", "Dùng ảnh chân dung " + ("mẫu" if asset["is_placeholder"] else "người dùng (đã có bản ghi đồng ý)"))
            return Path(asset["path"]), asset
        p = config.data_dir() / "user_assets" / "placeholder_portrait.png"
        make_placeholder_portrait(p)
        aid = self.repo.add_asset("avatar", str(p), sha256_file(p), 1080, 1350, is_placeholder=1)
        say("INFO", "Chưa có ảnh chân dung → tạo ảnh mẫu (is_placeholder=1)")
        return p, self.repo.one("SELECT * FROM assets WHERE id=?", (aid,))

    def avatar_provider(self, name: str, mode: str, asset: dict | None, duration: float, say):
        from stockai.providers.avatar.demo_motion import DemoMotionProvider

        if name == "demo" or mode == "DEMO":
            if name != "demo":
                say("WARN", f"Chế độ DEMO → không gọi provider trả phí '{name}', dùng DemoMotion")
            return DemoMotionProvider()
        if asset and asset["is_placeholder"]:
            raise ConfigError("Không gửi ảnh mẫu cho provider trả phí", hint="Tải ảnh chân dung thật + đồng ý")
        if name in ("fal", "hybrid"):
            from stockai.providers.avatar.fal import FalAvatarProvider
            p = FalAvatarProvider(self.repo.get_setting("avatar.fal_model"))
        elif name == "heygen":
            from stockai.providers.avatar.heygen import HeyGenProvider
            p = HeyGenProvider()
        else:
            return DemoMotionProvider()
        cost = p.estimate_cost_usd(15 if name == "hybrid" else duration)
        cap = float(self.repo.get_setting("avatar.max_cost_usd", "5"))
        if cost > cap:  # R-AV-1
            raise ConfigError(f"Chi phí ước tính ${cost:.2f} vượt giới hạn ${cap:.2f}", code="COST_LIMIT",
                              hint="Tăng avatar.max_cost_usd hoặc dùng Hybrid/DemoMotion")
        return p

    # ---------------- B4 ----------------
    async def step_render(self, job_id: str, job_dir: Path, opts: dict):
        from stockai.render.composer import compose

        say = lambda lvl, m: self.emit(job_id, 4, lvl, m)  # noqa: E731
        job = self.repo.get_job(job_id)
        script = ScriptOutput.model_validate_json((job_dir / "script.json").read_text(encoding="utf-8"))
        news = json.loads((job_dir / "news.json").read_text(encoding="utf-8"))
        dur = await ffmpeg.probe_duration(job_dir / "voice.mp3")
        say("INFO", f"B4 · Dựng video 9:16 · {dur:.1f}s")

        async def prog(f, msg):
            say("INFO", msg)
            await self.progress(job_id, 4, f)

        bgm = self.repo.active_asset("bgm")
        logo = self.repo.active_asset("logo")
        res = await compose(job_dir, script, [n["source"] for n in news], job["session_type"],
                            datetime.strptime(job["run_date"], "%Y-%m-%d").date(), dur, job["data_quality"] == "SYNTHETIC",
                            prog, bgm=Path(bgm["path"]) if bgm else None, logo=Path(logo["path"]) if logo else None,
                            bgm_db=float(self.repo.get_setting("audio.bgm_db", "-22")),
                            # safe_zone_check.png rẻ (1 frame) nên luôn xuất để người dùng tự kiểm tra bố cục
                            debug_safe_zone=True)
        self.repo.update_job(job_id, final_video_path=str(res.final_video_path), thumbnail_path=str(res.thumbnail_path),
                             duration_s=res.duration_s, ai_label_applied=1)
        self.save_manifest(job_dir, 4, ["final.mp4", "thumbnail.jpg"])
        say("SUCCESS", f"final.mp4 đạt kiểm tra ffprobe: 1080×1920 · 30fps · có audio · {res.duration_s:.1f}s · "
                       f"{res.size_bytes / 1e6:.1f} MB · metadata AI · ai_label_applied=1")
        await self.progress(job_id, 4, 1)

    # ---------------- B5 ----------------
    async def step_publish(self, job_id: str, job_dir: Path, opts: dict):
        say = lambda lvl, m: self.emit(job_id, 5, lvl, m)  # noqa: E731
        self.repo.update_job(job_id, current_step=5)
        if opts.get("skip_publish"):
            self.set_status(job_id, "COMPLETED", completed_at=datetime.now(VN).isoformat(timespec="seconds"))
            say("INFO", "B5 · Bỏ qua xuất bản (--no-publish)")
            await self.progress(job_id, 5, 1)
            return
        if opts.get("require_approval", True):
            self.set_status(job_id, "WAITING_APPROVAL")
            say("WARN", "B5 · Chờ duyệt: mở Kho nội dung để xem video, sửa caption và bấm Duyệt & Đăng")
            await self.progress(job_id, 5, 0.3)
            await self.notify_draft(job_id, say)
            return
        plats = [p for p in opts["platforms"] if p != "tiktok"]  # TikTok luôn cần duyệt
        await self.publish(job_id, plats, {}, dry_run=opts.get("dry_run", False))

    async def notify_draft(self, job_id: str, say) -> None:
        """CÓ THỂ gửi bản nháp vào Telegram chat riêng của chủ kênh (nếu đã cấu hình)."""
        return None

    async def publish(self, job_id: str, platforms: list[str], privacy: dict[str, str], dry_run: bool = False) -> list[dict]:
        from stockai.providers.publish.dry_run import DryRunPublisher
        from stockai.text import captions

        job = self.repo.get_job(job_id)
        say = lambda lvl, m: self.emit(job_id, 5, lvl, m)  # noqa: E731
        video = Path(job["final_video_path"])
        script = ScriptOutput.model_validate_json(job["script_json"])
        title, text = job["video_title"] or script.video_title, job["social_post_text"] or script.social_post_text
        self.set_status(job_id, "PUBLISHING")
        blocked = job["data_quality"] == "SYNTHETIC" or not job["ai_label_applied"]  # R-PUB-1
        if blocked:
            say("WARN", "R-PUB-1: dữ liệu minh họa hoặc thiếu nhãn AI → chỉ dry-run")
        results = []
        caps = captions.build_all(title, text, script.hashtags)
        for p in platforms:
            if self.repo.has_success(job_id, p):  # R-PUB-2
                say("INFO", f"{p}: đã đăng thành công trước đó → bỏ qua")
                continue
            raw_priv = privacy.get(p, self.repo.get_setting("publish.default_privacy", "private"))
            # Ánh xạ mức riêng của nền tảng (SELF_ONLY, channel, published…) về tập chuẩn của PublishOptions (Mục 8)
            std = {"SELF_ONLY": "private", "MUTUAL_FOLLOW_FRIENDS": "unlisted", "PUBLIC_TO_EVERYONE": "public",
                   "channel": "public", "published": "public"}.get(raw_priv, raw_priv)
            opts = PublishOptions(privacy=std if std in ("public", "unlisted", "private", "draft") else "private",
                                  dry_run=dry_run or blocked)
            if p == "tiktok":
                self._tiktok_privacy = raw_priv
            try:
                if opts.dry_run or job["mode"] == "DEMO" and p != "telegram":
                    pub = DryRunPublisher(p, {**caps[p], "platform_privacy": raw_priv,
                                              "flags": {"is_aigc": True} if p == "tiktok" else
                                              {"containsSyntheticMedia": True} if p == "youtube" else {}})
                    res, attempt = await pub.publish(job_id, video, title, text, opts), 1
                else:
                    pub = self.publisher(p, script.hashtags, job)
                    from stockai.providers.publish.base import with_retry
                    res, attempt = await asyncio.wait_for(with_retry(lambda pub=pub, opts=opts: pub.publish(job_id, video, title, text, opts)), 300)
            except StockAIError as e:
                from stockai.models import PublishResult
                res, attempt = PublishResult(platform=p, status="FAILED", error_message=f"{e.message} {e.hint or ''}"), 1
            except Exception as e:  # noqa: BLE001
                from stockai.models import PublishResult
                res, attempt = PublishResult(platform=p, status="FAILED", error_message=f"{type(e).__name__}: {e}"[:300]), 1
            self.repo.add_publish_log(job_id, p, res.status, privacy_level=res.privacy_level, attempt=attempt,
                                      remote_post_id=res.remote_post_id, remote_post_url=res.remote_post_url,
                                      error_message=res.error_message, response_payload=res.model_dump_json())
            say("SUCCESS" if res.status in ("SUCCESS", "DRY_RUN") else "ERROR",
                f"{p}: {res.status}" + (f" · {res.remote_post_url}" if res.remote_post_url else "") + (f" · {res.error_message}" if res.error_message else ""))
            results.append(res.model_dump())
        self.set_status(job_id, "COMPLETED", completed_at=datetime.now(VN).isoformat(timespec="seconds"))
        await self.progress(job_id, 5, 1)
        return results

    def publisher(self, p: str, hashtags: list[str], job: dict):
        if p == "telegram":
            from stockai.providers.publish.telegram import TelegramPublisher
            return TelegramPublisher(self.repo.get_setting("telegram_chat_id"), hashtags=hashtags, duration=job["duration_s"] or 0,
                                     thumb=Path(job["thumbnail_path"]) if job["thumbnail_path"] else None)
        if p == "facebook":
            from stockai.providers.publish.facebook import FacebookPublisher
            return FacebookPublisher(self.repo.get_setting("facebook_page_id"), self.repo.get_setting("facebook.graph_version", "v25.0"),
                                     self.repo.count_recent_success("facebook"))
        if p == "youtube":
            from stockai.providers.publish.youtube import YouTubePublisher
            return YouTubePublisher(hashtags, self.repo.get_setting("youtube.category_id", "25"))
        if p == "tiktok":
            from stockai.providers.publish.tiktok import TikTokPublisher
            return TikTokPublisher(privacy_level=getattr(self, "_tiktok_privacy", "SELF_ONLY"))
        raise ConfigError(f"Nền tảng không hỗ trợ: {p}")


_orch: Orchestrator | None = None


def get_orchestrator() -> Orchestrator:
    global _orch
    if _orch is None:
        _orch = Orchestrator()
    return _orch


_ = WordTiming
