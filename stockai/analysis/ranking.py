"""Chống trùng, lọc chủ đề, cửa sổ thời gian, xếp hạng tin — hàm thuần (Blueprint 9.1)."""

import hashlib
import re
import unicodedata
from datetime import datetime, timedelta

from stockai import config


def normalize_title(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def content_hash(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()


def jaccard(a: str, b: str) -> float:
    A, B = set(normalize_title(a).split()), set(normalize_title(b).split())
    if not A or not B:
        return 0.0
    return len(A & B) / len(A | B)


def news_window_start(now: datetime) -> datetime:
    """since = min(now − 48h, 00:00 ngày giao dịch liền trước), tối đa 96h."""
    prev = now.replace(hour=0, minute=0, second=0, microsecond=0)
    while True:
        prev -= timedelta(days=1)
        if prev.weekday() < 5:
            break
    since = min(now - timedelta(hours=48), prev)
    return max(since, now - timedelta(hours=96))


def keyword_weight(text: str, keywords: dict[str, float] | None = None) -> float:
    kw = keywords or config.TOPIC_KEYWORDS
    low = text.lower()
    return sum(w for k, w in kw.items() if k in low)


def is_on_topic(text: str) -> bool:
    return keyword_weight(text) > 0


def dedupe(items: list[dict]) -> list[dict]:
    """items: dict có title, published_at (datetime). Giữ tin sớm hơn, cộng 'sources'."""
    out: list[dict] = []
    seen: set[str] = set()
    for it in sorted(items, key=lambda x: x["published_at"]):
        h = content_hash(it["title"])
        it = {**it, "content_hash": h, "sources": it.get("sources", 1)}
        if h in seen:
            for o in out:
                if o["content_hash"] == h:
                    o["sources"] += 1
            continue
        dup = next((o for o in out if jaccard(o["title"], it["title"]) >= 0.6), None)
        if dup:
            dup["sources"] += 1
            continue
        seen.add(h)
        out.append(it)
    return out


def score_items(items: list[dict], now: datetime, window_hours: float = 96) -> list[dict]:
    if not items:
        return []
    weights = [keyword_weight(i["title"] + " " + i.get("summary", "")) for i in items]
    maxw = max(weights) or 1
    for it, w in zip(items, weights, strict=True):
        age_h = (now - it["published_at"]).total_seconds() / 3600
        recency = max(0.0, 1 - age_h / window_hours)
        it["score"] = round(0.5 * recency + 0.3 * w / maxw + 0.2 * min(it.get("sources", 1), 3) / 3, 4)
    return sorted(items, key=lambda x: x["score"], reverse=True)


def rank(items: list[dict], now: datetime, limit: int = 20) -> list[dict]:
    since = news_window_start(now)
    fresh = [i for i in items if since <= i["published_at"] <= now + timedelta(minutes=5)]
    topical = [i for i in fresh if is_on_topic(i["title"] + " " + i.get("summary", ""))]
    return score_items(dedupe(topical), now)[:limit]
