"""Hàm CRUD trên SQLite. Một kết nối dùng chung, bảo vệ bằng lock."""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from stockai import config, secrets
from stockai.db.migrate import connect, migrate

_lock = threading.RLock()


class Repo:
    def __init__(self, db_path: Path | None = None):
        self.path = db_path or (config.data_dir() / "stock_ai.db")
        self.conn = connect(self.path)
        migrate(self.conn)
        self._seed()

    # ---------- tiện ích ----------
    def q(self, sql: str, args: tuple = ()) -> list[dict]:
        with _lock:
            return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def one(self, sql: str, args: tuple = ()) -> dict | None:
        r = self.q(sql, args)
        return r[0] if r else None

    def x(self, sql: str, args: tuple = ()) -> int:
        with _lock:
            cur = self.conn.execute(sql, args)
            return cur.lastrowid

    def tables(self) -> list[str]:
        return [r["name"] for r in self.q("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]

    def _seed(self) -> None:
        for k, v in config.DEFAULT_SETTINGS.items():
            self.x("INSERT OR IGNORE INTO settings(key, value, is_secret) VALUES (?,?,0)", (k, v))
        if not self.q("SELECT id FROM schedules LIMIT 1"):
            self.x("INSERT INTO schedules(name, session_type, cron_hour, cron_minute) VALUES (?,?,?,?)",
                   ("Bản tin trước phiên", "PRE_MARKET", 7, 30))
            self.x("INSERT INTO schedules(name, session_type, cron_hour, cron_minute) VALUES (?,?,?,?)",
                   ("Tổng kết sau phiên", "POST_MARKET", 15, 30))

    # ---------- settings ----------
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        r = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r and r["value"] is not None else default

    def set_setting(self, key: str, value: str) -> None:
        if key in config.SECRET_KEYS:
            secrets.set_secret(key, value)
            self.x("INSERT INTO settings(key,value,is_secret,updated_at) VALUES (?,NULL,1,datetime('now')) "
                   "ON CONFLICT(key) DO UPDATE SET value=NULL, is_secret=1, updated_at=datetime('now')", (key,))
        else:
            self.x("INSERT INTO settings(key,value,is_secret,updated_at) VALUES (?,?,0,datetime('now')) "
                   "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=datetime('now')", (key, value))

    def all_settings(self) -> dict[str, Any]:
        out: dict[str, Any] = {r["key"]: r["value"] for r in self.q("SELECT key, value FROM settings WHERE is_secret=0")}
        for k in config.SECRET_KEYS:
            out[k] = secrets.mask(secrets.get_secret(k))
        return out

    # ---------- jobs ----------
    def create_job(self, job_id: str, run_date: str, session_type: str, trigger: str, mode: str,
                   schedule_id: int | None, artifacts_dir: str) -> None:
        self.x("INSERT INTO content_jobs(id, run_date, session_type, trigger, schedule_id, mode, status, artifacts_dir) "
               "VALUES (?,?,?,?,?,?, 'PENDING', ?)", (job_id, run_date, session_type, trigger, schedule_id, mode, artifacts_dir))

    def update_job(self, job_id: str, **fields: Any) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k}=?" for k in fields)
        self.x(f"UPDATE content_jobs SET {cols} WHERE id=?", (*fields.values(), job_id))

    def get_job(self, job_id: str) -> dict | None:
        return self.one("SELECT * FROM content_jobs WHERE id=?", (job_id,))

    def list_jobs(self, limit: int = 50, offset: int = 0, status: str | None = None) -> list[dict]:
        if status:
            return self.q("SELECT * FROM content_jobs WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                          (status, limit, offset))
        return self.q("SELECT * FROM content_jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))

    def active_job(self) -> dict | None:
        return self.one("SELECT * FROM content_jobs WHERE status IN ('RUNNING','PUBLISHING') LIMIT 1")

    def mark_interrupted(self) -> int:
        """R-RUN-4: job RUNNING từ lần trước → FAILED/INTERRUPTED."""
        with _lock:
            cur = self.conn.execute(
                "UPDATE content_jobs SET status='FAILED', error_code='INTERRUPTED', "
                "error_message='Ứng dụng bị đóng khi job đang chạy.' WHERE status IN ('RUNNING','PUBLISHING')")
            return cur.rowcount

    def add_event(self, job_id: str, step: int | None, level: str, message: str, data: dict | None = None) -> None:
        self.x("INSERT INTO job_events(job_id, step, level, message, data_json) VALUES (?,?,?,?,?)",
               (job_id, step, level, secrets.redact(message), json.dumps(data, ensure_ascii=False) if data else None))

    def events(self, job_id: str) -> list[dict]:
        return self.q("SELECT * FROM job_events WHERE job_id=? ORDER BY id", (job_id,))

    def delete_job(self, job_id: str) -> None:
        self.x("DELETE FROM publish_logs WHERE job_id=?", (job_id,))
        self.x("DELETE FROM content_jobs WHERE id=?", (job_id,))

    # ---------- news ----------
    def upsert_news(self, item: dict) -> int:
        r = self.one("SELECT id FROM news_items WHERE url=? OR content_hash=?", (item["url"], item["content_hash"]))
        if r:
            return r["id"]
        return self.x("INSERT INTO news_items(title, source, url, content_hash, summary, published_at) VALUES (?,?,?,?,?,?)",
                      (item["title"], item["source"], item["url"], item["content_hash"], item["summary"], item["published_at"]))

    # ---------- market ----------
    def save_snapshot(self, snap: dict, top_movers: list | None = None) -> int | None:
        if snap["data_quality"] == "SYNTHETIC":
            return None  # không bao giờ lưu dữ liệu minh họa
        self.x("""INSERT INTO market_snapshots(symbol, session_date, close, change, change_pct, volume,
                value_bn_vnd, foreign_net_bn_vnd, sma20, rsi14, support20, resistance20, bars_json, top_movers_json, source)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(symbol, session_date, source) DO UPDATE SET close=excluded.close, change=excluded.change,
                change_pct=excluded.change_pct, volume=excluded.volume, sma20=excluded.sma20, rsi14=excluded.rsi14,
                support20=excluded.support20, resistance20=excluded.resistance20, bars_json=excluded.bars_json,
                created_at=datetime('now')""",
               (snap["symbol"], str(snap["session_date"]), snap["close"], snap["change"], snap["change_pct"], snap.get("volume"),
                snap.get("value_bn_vnd"), snap.get("foreign_net_bn_vnd"), snap["sma20"], snap["rsi14"], snap["support20"],
                snap["resistance20"], json.dumps(snap["bars"], default=str), json.dumps(top_movers) if top_movers else None,
                snap["source"]))
        r = self.one("SELECT id FROM market_snapshots WHERE symbol=? AND session_date=? AND source=?",
                     (snap["symbol"], str(snap["session_date"]), snap["source"]))
        return r["id"] if r else None

    def latest_snapshot(self, symbol: str) -> dict | None:
        return self.one("SELECT * FROM market_snapshots WHERE symbol=? ORDER BY session_date DESC, id DESC LIMIT 1", (symbol,))

    # ---------- schedules ----------
    def schedules(self) -> list[dict]:
        rows = self.q("SELECT * FROM schedules ORDER BY cron_hour, cron_minute")
        for r in rows:
            r["target_platforms"] = json.loads(r["target_platforms_json"])
        return rows

    def get_schedule(self, sid: int) -> dict | None:
        return self.one("SELECT * FROM schedules WHERE id=?", (sid,))

    # ---------- assets ----------
    def add_asset(self, kind: str, path: str, sha256: str, width: int | None = None, height: int | None = None,
                  duration_s: float | None = None, is_placeholder: int = 0) -> int:
        self.x("UPDATE assets SET is_active=0 WHERE kind=?", (kind,))
        return self.x("INSERT INTO assets(kind, path, sha256, width, height, duration_s, is_placeholder) VALUES (?,?,?,?,?,?,?)",
                      (kind, path, sha256, width, height, duration_s, is_placeholder))

    def active_asset(self, kind: str) -> dict | None:
        return self.one("SELECT * FROM assets WHERE kind=? AND is_active=1 ORDER BY id DESC LIMIT 1", (kind,))

    def add_consent(self, asset_id: int, subject_name: str, relation: str, statement: str) -> int:
        return self.x("INSERT INTO consents(asset_id, subject_name, relation, statement) VALUES (?,?,?,?)",
                      (asset_id, subject_name, relation, statement))

    def consent_for(self, asset_id: int) -> dict | None:
        return self.one("SELECT * FROM consents WHERE asset_id=? ORDER BY id DESC LIMIT 1", (asset_id,))

    # ---------- publish ----------
    def add_publish_log(self, job_id: str, platform: str, status: str, **kw: Any) -> None:
        payload = kw.get("response_payload")
        self.x("""INSERT INTO publish_logs(job_id, platform, status, privacy_level, attempt, remote_post_id, remote_post_url,
                error_message, response_payload) VALUES (?,?,?,?,?,?,?,?,?)""",
               (job_id, platform, status, kw.get("privacy_level"), kw.get("attempt", 1), kw.get("remote_post_id"),
                kw.get("remote_post_url"), kw.get("error_message"), secrets.redact(payload) if payload else None))

    def has_success(self, job_id: str, platform: str) -> bool:
        return bool(self.one("SELECT id FROM publish_logs WHERE job_id=? AND platform=? AND status='SUCCESS'", (job_id, platform)))

    def publish_logs(self, job_id: str) -> list[dict]:
        return self.q("SELECT * FROM publish_logs WHERE job_id=? ORDER BY id", (job_id,))

    def count_recent_success(self, platform: str, hours: int = 24) -> int:
        r = self.one("SELECT COUNT(*) AS n FROM publish_logs WHERE platform=? AND status='SUCCESS' "
                     "AND created_at >= datetime('now', ?)", (platform, f"-{hours} hours"))
        return r["n"] if r else 0


_repo: Repo | None = None


def get_repo() -> Repo:
    global _repo
    if _repo is None:
        _repo = Repo()
    return _repo


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _unused(_: sqlite3.Connection) -> None:  # giữ import cho type checker
    pass
