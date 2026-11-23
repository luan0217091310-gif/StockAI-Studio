"""DB (10 bảng, bí mật không vào SQLite) + API (401/403/409, path traversal)."""

import pytest
from fastapi.testclient import TestClient

from stockai import secrets
from stockai.db.repo import get_repo


def test_db_tables_and_seed():
    r = get_repo()
    t = set(r.tables())
    assert {"schema_version", "settings", "assets", "consents", "news_items", "market_snapshots", "schedules",
            "content_jobs", "job_events", "publish_logs"} <= t
    assert len(r.schedules()) >= 2
    assert r.get_setting("llm.model") == "gemini-3.8-flash"


def test_secret_not_in_sqlite(monkeypatch):
    store = {}
    monkeypatch.setattr(secrets, "set_secret", lambda k, v: store.__setitem__(k, v))
    monkeypatch.setattr(secrets, "get_secret", lambda k: store.get(k))
    r = get_repo()
    r.set_setting("gemini_api_key", "AIzaSyTEST1234567890")
    row = r.one("SELECT value, is_secret FROM settings WHERE key='gemini_api_key'")
    assert row["value"] is None and row["is_secret"] == 1
    assert r.all_settings()["gemini_api_key"] == "AIza••••••7890"


def test_redact():
    s = secrets.redact("url bot123456:ABC-def token AIzaXYZ Bearer abc access_token=zzz")
    assert "ABC-def" not in s and "AIzaXYZ" not in s and "abc" not in s.split("Bearer")[-1] and "zzz" not in s


def test_synthetic_snapshot_never_saved():
    assert get_repo().save_snapshot({"data_quality": "SYNTHETIC"}) is None


@pytest.fixture
def client():
    from stockai.server import api, security

    api.state["no_scheduler"] = True
    security.PORT["value"] = 8765
    with TestClient(api.app, base_url="http://127.0.0.1:8765") as c:
        yield c, security.APP_TOKEN


def test_api_requires_token(client):
    c, _ = client
    assert c.get("/api/status").status_code == 401
    assert c.get("/api/status", headers={"X-App-Token": "sai"}).status_code == 401


def test_api_rejects_foreign_origin(client):
    c, tok = client
    assert c.get("/api/status", headers={"X-App-Token": tok, "Origin": "https://evil.example"}).status_code == 403
    assert c.get("/api/status", headers={"X-App-Token": tok, "Origin": "http://127.0.0.1:8765"}).status_code == 200


def test_api_409_when_job_running(client, monkeypatch):
    c, tok = client
    from stockai.server import api

    monkeypatch.setattr(api.state["orch"], "is_busy", lambda: True)
    r = c.post("/api/pipeline/run", headers={"X-App-Token": tok}, json={})
    assert r.status_code == 409 and r.json()["error"]["code"] == "JOB_RUNNING"


def test_media_path_traversal(client):
    c, tok = client
    r = get_repo()
    r.create_job("job-trav", "2026-11-23", "ADHOC", "MANUAL", "DEMO", None, str(r.path.parent / "outputs" / "x"))
    assert c.get("/media/job-trav/..%2F..%2Fstock_ai.db", params={"token": tok}).status_code in (403, 404)
    assert c.get("/media/job-trav/x.mp4").status_code == 401


def test_avatar_upload_requires_consent(client):
    c, tok = client
    r = c.post("/api/assets/upload", headers={"X-App-Token": tok}, data={"kind": "avatar"},
               files={"file": ("a.png", b"\x89PNG", "image/png")})
    assert r.status_code == 400 and "R-LEGAL-3" in r.json()["error"]["message"]


def test_edit_post_must_keep_disclaimer(client):
    c, tok = client
    r = get_repo()
    r.create_job("job-edit", "2026-11-23", "ADHOC", "MANUAL", "DEMO", None, "x")
    resp = c.put("/api/jobs/job-edit", headers={"X-App-Token": tok}, json={"social_post_text": "Mua ngay!"})
    assert resp.status_code == 400


def test_schedule_crud(client):
    c, tok = client
    h = {"X-App-Token": tok}
    sid = c.post("/api/schedules", headers=h, json={"name": "T", "cron_hour": 9, "cron_minute": 5, "target_platforms": ["tiktok"],
                                                     "require_approval": False}).json()["id"]
    row = get_repo().get_schedule(sid)
    assert row["require_approval"] == 1  # TikTok luôn cần duyệt
    assert c.delete(f"/api/schedules/{sid}", headers=h).status_code == 200
