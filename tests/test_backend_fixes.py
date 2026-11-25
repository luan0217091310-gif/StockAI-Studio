"""Hồi quy cho các lỗi backend phát hiện khi rà soát (26/11/2026)."""

import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from stockai.db.repo import get_repo


@pytest.fixture
def client():
    from stockai.server import api, security

    api.state["no_scheduler"] = True
    security.PORT["value"] = 8765
    with TestClient(api.app, base_url="http://127.0.0.1:8765") as c:
        yield c, security.APP_TOKEN


def test_edit_missing_job_is_404(client):
    c, tok = client
    r = c.put("/api/jobs/khong-ton-tai", headers={"X-App-Token": tok}, json={"video_title": "x"})
    assert r.status_code == 404


def test_approve_while_publishing_is_409(client):
    """Bấm Duyệt & Đăng 2 lần liên tiếp không được đăng song song (R-RUN-4, R-PUB-2)."""
    c, tok = client
    from stockai.server import api

    r = get_repo()
    r.create_job("job-busy", "2026-11-23", "ADHOC", "MANUAL", "DEMO", None, "x")
    r.update_job("job-busy", status="WAITING_APPROVAL")
    orch = api.state["orch"]
    asyncio.run(orch.publish_lock.acquire())  # giả lập một lượt đăng đang chạy (không tranh chấp → không gắn event loop)
    try:
        resp = c.post("/api/jobs/job-busy/approve", headers={"X-App-Token": tok}, json={"platforms": ["telegram"]})
        assert resp.status_code == 409 and resp.json()["error"]["code"] == "JOB_RUNNING"
    finally:
        orch.publish_lock.release()


def test_publish_rejected_while_other_job_runs():
    from stockai.errors import StockAIError
    from stockai.pipeline.orchestrator import Orchestrator

    o = Orchestrator()
    o.current_job = "job-khac"

    async def run():
        await o.lock.acquire()
        try:
            with pytest.raises(StockAIError) as e:
                await o.publish("job-x", ["telegram"], {})
            assert e.value.code == "JOB_RUNNING"
        finally:
            o.lock.release()

    asyncio.run(run())


def test_tiktok_privacy_not_shared_state():
    """Mức riêng tư TikTok truyền theo từng lần đăng, không lưu vào thuộc tính dùng chung của Orchestrator."""
    from stockai.pipeline.orchestrator import Orchestrator

    o = Orchestrator()
    job = {"duration_s": 60, "thumbnail_path": None}
    p1 = o.publisher("tiktok", [], job, privacy="PUBLIC_TO_EVERYONE")
    p2 = o.publisher("tiktok", [], job)
    assert p1.privacy == "PUBLIC_TO_EVERYONE" and p2.privacy == "SELF_ONLY"
    assert not hasattr(o, "_tiktok_privacy")


def test_catchup_runs_every_missed_schedule(monkeypatch):
    """Lỡ 2 lịch trong cửa sổ chạy bù → chạy bù cả hai (lần lượt), không chỉ lịch đầu tiên."""
    from stockai.pipeline.orchestrator import Orchestrator
    from stockai.scheduler import VN, Scheduler

    now = datetime.now(VN)
    a, b = now - timedelta(minutes=20), now - timedelta(minutes=10)
    if a.date() != now.date():
        pytest.skip("Gần nửa đêm — lịch giả lập sẽ rơi sang hôm trước")
    r = get_repo()
    ids = [r.x("INSERT INTO schedules(name, session_type, cron_hour, cron_minute, days_of_week) VALUES (?,?,?,?,?)",
               (f"bù {t:%H:%M}", "PRE_MARKET", t.hour, t.minute, "mon-sun")) for t in (a, b)]
    fired: list[int] = []

    async def fake_fire(self, sid, trigger="SCHEDULE", attempt=1):
        fired.append(sid)

    monkeypatch.setattr(Scheduler, "fire", fake_fire)

    async def run():
        s = Scheduler(Orchestrator(r))
        planned = await s.catchup()
        await asyncio.sleep(0.05)
        return planned

    try:
        planned = asyncio.run(run())
        assert set(ids) <= set(planned) and set(ids) <= set(fired)
    finally:
        for sid in ids:
            r.x("DELETE FROM schedules WHERE id=?", (sid,))


def test_status_includes_sparkline(client, tmp_path):
    import json

    c, tok = client
    r = get_repo()
    (tmp_path / "market.json").write_text(json.dumps({"close": 1700.5, "change": 1, "change_pct": .1, "session_date": "2026-11-25",
                                                      "data_quality": "LIVE", "bars": [{"close": 1600 + i} for i in range(60)]}),
                                          encoding="utf-8")
    r.create_job("job-spark", "2099-01-01", "ADHOC", "MANUAL", "DEMO", None, str(tmp_path))
    r.update_job("job-spark", data_quality="LIVE")
    r.x("UPDATE content_jobs SET created_at='2999-01-01 00:00:00' WHERE id='job-spark'")
    m = c.get("/api/status", headers={"X-App-Token": tok}).json()["market"]
    assert "bars" not in m and m["spark"] == [1600 + i for i in range(30, 60)]
    r.delete_job("job-spark")
