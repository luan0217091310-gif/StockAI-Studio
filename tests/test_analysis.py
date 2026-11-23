"""indicators, ranking, chống trùng, cửa sổ thời gian, RSS fixture."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from stockai.analysis import indicators, ranking
from stockai.providers.news import rss
from tests.conftest import FIX, VN


def test_sma_hand_computed():
    s = pd.Series([float(i) for i in range(1, 25)])
    assert indicators.sma(s, 20).iloc[-1] == pytest.approx(sum(range(5, 25)) / 20)
    assert pd.isna(indicators.sma(s, 20).iloc[18])


def test_rsi_wilder_hand_computed():
    # delta 1,1,-1,1 ; alpha=1/14, adjust=False → RSI ≈ 93,367 (tính tay)
    r = indicators.rsi_wilder(pd.Series([1.0, 2, 3, 2, 3]))
    assert r.iloc[-1] == pytest.approx(93.367, abs=1e-3)


def test_rsi_all_gains_is_100():
    assert indicators.rsi_wilder(pd.Series([1.0, 2, 3, 4, 5])).iloc[-1] == 100


def test_support_resistance_and_snapshot(snapshot):
    df = pd.DataFrame([b.model_dump() for b in snapshot.bars])
    assert snapshot.support20 == pytest.approx(df["low"].tail(20).min(), abs=0.01)
    assert snapshot.resistance20 == pytest.approx(df["high"].tail(20).max(), abs=0.01)
    assert snapshot.change == pytest.approx(df["close"].iloc[-1] - df["close"].iloc[-2], abs=0.01)
    assert len(snapshot.bars) == 60


def test_window_monday_morning_starts_friday():
    mon = datetime(2026, 11, 23, 7, 30, tzinfo=VN)  # thứ Hai
    since = ranking.news_window_start(mon)
    assert since == datetime(2026, 11, 20, 0, 0, tzinfo=VN)  # 00:00 thứ Sáu


def test_window_midweek_is_48h():
    wed = datetime(2026, 11, 25, 15, 30, tzinfo=VN)
    assert ranking.news_window_start(wed) == wed - timedelta(hours=48)


def test_window_capped_96h():
    tue = datetime(2026, 11, 24, 23, 0, tzinfo=VN)
    assert tue - ranking.news_window_start(tue) <= timedelta(hours=96)


def test_dedupe_exact_and_jaccard():
    now = datetime(2026, 11, 23, 8, tzinfo=VN)
    items = [{"title": "Khối ngoại bán ròng phiên thứ ba liên tiếp trên HOSE", "published_at": now - timedelta(hours=3)},
             {"title": "Khối ngoại bán ròng phiên thứ ba liên tiếp trên HOSE!", "published_at": now - timedelta(hours=1)},
             {"title": "Khối ngoại bán ròng phiên thứ 3 liên tiếp trên sàn HOSE", "published_at": now - timedelta(hours=2)},
             {"title": "Fed giữ lãi suất", "published_at": now}]
    out = ranking.dedupe(items)
    assert len(out) == 2
    first = next(o for o in out if "Khối ngoại" in o["title"])
    assert first["sources"] == 3 and first["published_at"] == now - timedelta(hours=3)  # giữ tin sớm hơn


def test_topic_filter():
    assert ranking.is_on_topic("VN-Index tăng điểm")
    assert not ranking.is_on_topic("Giá vàng miếng lập đỉnh mới")


def test_rank_scores_sorted_and_limited():
    now = datetime(2026, 11, 23, 8, tzinfo=VN)
    items = [{"title": f"Cổ phiếu ngân hàng số {i} khối ngoại", "summary": "", "published_at": now - timedelta(hours=i)} for i in range(30)]
    out = ranking.rank(items, now)
    assert len(out) <= 20
    assert [o["score"] for o in out] == sorted([o["score"] for o in out], reverse=True)


def test_parse_two_digit_year_cafef():
    xml = "<rss><channel><item><title>VN-Index tăng</title><link>https://a</link><pubDate>Sun, 22 Nov 26 20:09:00 +0700</pubDate></item></channel></rss>"
    items = rss.parse_feed(xml, "CafeF")
    assert items[0]["published_at"].year == 2026 and items[0]["published_at"].hour == 20


def test_parse_drops_missing_date():
    warns = []
    xml = "<rss><channel><item><title>Cổ phiếu</title><link>https://a</link></item></channel></rss>"
    assert rss.parse_feed(xml, "X", warns.append) == [] and warns


def test_clean_text_strips_html_and_limits():
    s = rss.clean_text("<p>Xin <b>chào</b></p> " + "từ " * 200)
    assert "<" not in s and len(s) <= 300 and not s.endswith(" ")


async def test_collect_offline_fixture():
    now = datetime(2026, 11, 23, 8, tzinfo=VN)
    items = await rss.collect(now=now, offline=True)
    titles = [i.title for i in items]
    assert not any("vàng" in t for t in titles)            # lọc chủ đề
    assert not any("quá cũ" in t for t in titles)          # cửa sổ thời gian
    assert not any("không có ngày" in t for t in titles)   # bỏ tin không có ngày
    assert sum("Khối ngoại bán ròng" in t for t in titles) == 1  # chống trùng
    assert (FIX / "rss_cafef.xml").exists()
