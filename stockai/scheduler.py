"""Lập lịch APScheduler 3.11 (Blueprint 9.9): đồng bộ CRUD, chạy bù, thử lại, bỏ qua."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from stockai import config
from stockai.pipeline.events import bus

log = logging.getLogger("stockai.scheduler")
VN = ZoneInfo(config.TZ)
TRANSIENT = {"TRANSIENT", "MARKET_UNAVAILABLE", "TTS_FAILED"}


def dow(days: str) -> str:
    return "mon-sun" if days in ("all", "mon-sun") else days


class Scheduler:
    def __init__(self, orch):
        self.orch = orch
        self.repo = orch.repo
        self.sched = AsyncIOScheduler(timezone=config.TZ)

    def start(self) -> None:
        self.sched.start()
        self.sync()
        asyncio.get_event_loop().create_task(self.catchup())

    def shutdown(self) -> None:
        if self.sched.running:
            self.sched.shutdown(wait=False)

    def sync(self) -> None:
        """Đồng bộ toàn bộ lịch DB → APScheduler (gọi sau mọi CRUD)."""
        wanted = set()
        for s in self.repo.schedules():
            jid = f"schedule-{s['id']}"
            if not s["is_active"]:
                continue
            wanted.add(jid)
            self.sched.add_job(self.fire, CronTrigger(day_of_week=dow(s["days_of_week"]), hour=s["cron_hour"],
                                                      minute=s["cron_minute"], timezone=config.TZ),
                               id=jid, args=[s["id"], "SCHEDULE"], replace_existing=True, misfire_grace_time=1800,
                               coalesce=True, max_instances=1)
        for j in self.sched.get_jobs():
            if j.id.startswith("schedule-") and j.id not in wanted:
                j.remove()
        nxt = self.next_run()
        bus.publish({"type": "schedule", "next_run_at": nxt.isoformat() if nxt else None})

    def next_run(self) -> datetime | None:
        times = [t for j in self.sched.get_jobs() if j.id.startswith("schedule-") and (t := getattr(j, "next_run_time", None))]
        return min(times) if times else None

    async def fire(self, schedule_id: int, trigger: str = "SCHEDULE", attempt: int = 1) -> str | None:
        s = self.repo.get_schedule(schedule_id)
        if not s:
            return None
        if self.orch.is_busy():
            log.warning("Lịch %s: đang có job chạy → thử lại sau 5 phút", schedule_id)
            self._retry_later(schedule_id, trigger, attempt)
            return None
        plats = json.loads(s["target_platforms_json"])
        job_id = await self.orch.start(session_type=s["session_type"], trigger=trigger, schedule_id=schedule_id,
                                       platforms=plats, require_approval=bool(s["require_approval"]) or "tiktok" in plats)
        self.repo.x("UPDATE schedules SET last_run_at=datetime('now','localtime'), last_job_id=? WHERE id=?", (job_id, schedule_id))
        await self.orch.wait()
        job = self.repo.get_job(job_id)
        if job["status"] == "FAILED" and (job["error_code"] in TRANSIENT) and attempt < 3:
            self.orch.emit(job_id, None, "WARN", f"Lỗi tạm thời → thử lại lần {attempt + 1}/3 sau 5 phút")
            self._retry_later(schedule_id, "RETRY", attempt + 1)
        return job_id

    def _retry_later(self, schedule_id: int, trigger: str, attempt: int) -> None:
        if attempt > 3:
            return
        self.sched.add_job(self.fire, "date", run_date=datetime.now(VN) + timedelta(minutes=5),
                           args=[schedule_id, trigger, attempt], id=f"retry-{schedule_id}-{attempt}", replace_existing=True)

    async def catchup(self) -> list[int]:
        """Lúc khởi động: lịch hôm nay bị lỡ trong vòng catchup_minutes và chưa có job → chạy bù.

        Mọi lịch bị lỡ đều được chạy bù, lần lượt theo giờ (mỗi lúc một job), thay vì chỉ lịch đầu tiên."""
        now = datetime.now(VN)
        window = int(self.repo.get_setting("schedule.catchup_minutes", "120"))
        fired = []
        for s in self.repo.schedules():
            if not s["is_active"]:
                continue
            if dow(s["days_of_week"]) == "mon-fri" and now.weekday() > 4:
                continue
            at = now.replace(hour=s["cron_hour"], minute=s["cron_minute"], second=0, microsecond=0)
            if at > now:
                continue
            exists = self.repo.one("SELECT id FROM content_jobs WHERE schedule_id=? AND run_date=? LIMIT 1",
                                   (s["id"], now.strftime("%Y-%m-%d")))
            if exists:
                continue
            late = (now - at).total_seconds() / 60
            if late <= window:
                log.info("Chạy bù lịch %s (lỡ %.0f phút)", s["name"], late)
                fired.append(s["id"])
            else:
                bus.publish({"type": "log", "job_id": None, "step": None, "level": "WARN",
                             "message": f"Đã lỡ lịch “{s['name']}” lúc {at:%H:%M} (quá {window} phút)"})
        if fired:
            self._catchup_task = asyncio.get_running_loop().create_task(self._run_sequential(fired))
        return fired

    async def _run_sequential(self, schedule_ids: list[int]) -> None:
        for sid in schedule_ids:  # fire() chờ job xong mới trả về → không chạy chồng
            try:
                await self.fire(sid, "CATCHUP")
            except Exception:  # noqa: BLE001
                log.exception("Chạy bù lịch %s lỗi", sid)


def prevent_sleep(on: bool) -> None:
    """Chặn máy ngủ khi pipeline chạy (Windows SetThreadExecutionState)."""
    import sys

    if sys.platform == "win32":
        import ctypes

        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))
