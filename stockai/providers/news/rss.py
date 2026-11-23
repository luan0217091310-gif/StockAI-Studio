"""Tin tức RSS (Blueprint 9.1). Chỉ lưu tiêu đề + tóm tắt + link; không tải toàn văn."""

import asyncio
import calendar
import logging
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser
import httpx
from bs4 import BeautifulSoup

from stockai import config
from stockai.analysis import ranking
from stockai.models import NewsItem

log = logging.getLogger("stockai.news")
VN = ZoneInfo(config.TZ)
FIXTURES = config.ROOT / "tests" / "fixtures"
_etags: dict[str, dict[str, str]] = {}


def clean_text(s: str, limit: int = 300) -> str:
    t = BeautifulSoup(s or "", "html.parser").get_text(" ", strip=True)
    t = unicodedata.normalize("NFC", " ".join(t.split()))
    if len(t) <= limit:
        return t
    cut = t[:limit]
    return cut[: cut.rfind(" ")] if " " in cut else cut


def parse_feed(content: bytes | str, source: str, warn=None) -> list[dict]:
    fp = feedparser.parse(content)
    out = []
    for e in fp.entries:
        title = unicodedata.normalize("NFC", (e.get("title") or "").strip())
        link = e.get("link") or ""
        pp = e.get("published_parsed") or e.get("updated_parsed")
        if not title or not link:
            continue
        if not pp:
            if warn:
                warn(f"Bỏ tin không đọc được ngày đăng: {title[:60]}")
            continue
        ts = datetime.fromtimestamp(calendar.timegm(pp), tz=UTC).astimezone(VN)
        out.append({"title": title, "source": source, "url": link, "published_at": ts,
                    "summary": clean_text(e.get("summary") or e.get("description") or "")})
    return out


async def _fetch(client: httpx.AsyncClient, source: str, url: str) -> bytes | None:
    headers = {"User-Agent": config.USER_AGENT}
    if url in _etags:
        headers.update(_etags[url])
    r = await client.get(url, headers=headers, timeout=10, follow_redirects=True)
    if r.status_code == 304:
        return None
    r.raise_for_status()
    cache = {}
    if r.headers.get("etag"):
        cache["If-None-Match"] = r.headers["etag"]
    if r.headers.get("last-modified"):
        cache["If-Modified-Since"] = r.headers["last-modified"]
    _etags[url] = cache
    return r.content


async def collect(now: datetime | None = None, offline: bool = False, sources: dict[str, str] | None = None,
                  emit=None) -> list[NewsItem]:
    now = now or datetime.now(VN)
    sources = sources or config.RSS_SOURCES
    warn = (lambda m: emit("WARN", m)) if emit else (lambda m: log.warning(m))
    raw: list[dict] = []
    if offline:
        for name in sources:
            f = FIXTURES / f"rss_{name.lower()}.xml"
            if f.exists():
                raw += parse_feed(_shift_fixture(f, now), name, warn)
    else:
        async with httpx.AsyncClient() as client:
            res = await asyncio.gather(*(_fetch(client, n, u) for n, u in sources.items()), return_exceptions=True)
        for (name, _), r in zip(sources.items(), res, strict=True):
            if isinstance(r, Exception):
                warn(f"Nguồn {name} lỗi: {type(r).__name__}: {r}"[:200])
                continue
            if r:
                items = parse_feed(r, name, warn)
                if emit:
                    emit("INFO", f"{name}: {len(items)} tin")
                raw += items
    ranked = ranking.rank(raw, now)
    return [NewsItem(id=i, title=x["title"], source=x["source"], url=x["url"], published_at=x["published_at"],
                     summary=x["summary"], content_hash=x["content_hash"], score=x["score"]) for i, x in enumerate(ranked)]


def _shift_fixture(path: Path, now: datetime) -> str:
    """Fixture dùng placeholder {H-n} → ngày giờ tương đối so với now (để test cửa sổ thời gian ổn định)."""
    import re
    from datetime import timedelta
    from email.utils import format_datetime

    txt = path.read_text(encoding="utf-8")

    def rep(m):
        d = now - timedelta(hours=int(m.group(1)))
        if m.group(2) == "2y":  # kiểu CafeF: năm 2 chữ số
            return d.strftime("%a, %d %b %y %H:%M:%S +0700")
        return format_datetime(d)

    return re.sub(r"\{H-(\d+)(?:\|(2y))?\}", rep, txt)
