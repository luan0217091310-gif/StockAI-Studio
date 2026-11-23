import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

# Mọi test dùng thư mục dữ liệu tạm, không chạm dữ liệu thật
os.environ.setdefault("STOCKAI_DATA_DIR", tempfile.mkdtemp(prefix="stockai_test_"))

from stockai.analysis.indicators import build_snapshot  # noqa: E402
from stockai.models import NewsItem, ScriptContext  # noqa: E402
from stockai.providers.market.csv_import import CsvImportProvider  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
VN = ZoneInfo("Asia/Ho_Chi_Minh")


@pytest.fixture
def snapshot():
    import asyncio

    bars = asyncio.run(CsvImportProvider(FIX / "ohlcv_vnindex_60.csv").fetch_daily("VNINDEX", 60))
    return build_snapshot(bars, "fixture", "LIVE")


@pytest.fixture
def news():
    now = datetime(2026, 11, 23, 7, 0, tzinfo=VN)
    titles = [("Khối ngoại bán ròng gần 450 tỷ đồng trên HOSE, HPG bị bán mạnh", "CafeF"),
              ("NHNN giữ ổn định lãi suất điều hành", "VnEconomy"),
              ("Thanh khoản HOSE cải thiện, dòng tiền quay lại nhóm chứng khoán", "Vietstock"),
              ("Fed phát tín hiệu thận trọng", "VnEconomy")]
    return [NewsItem(id=i, title=t, source=s, url=f"https://x/{i}", published_at=now, summary="Tóm tắt tin.", content_hash=str(i))
            for i, (t, s) in enumerate(titles)]


@pytest.fixture
def ctx(snapshot, news):
    return ScriptContext(run_date=date(2026, 11, 23), session_type="PRE_MARKET", market=snapshot, news=news,
                         hook_style="con số nổi bật nhất")
