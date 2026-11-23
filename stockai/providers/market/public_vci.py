"""PublicVciProvider — endpoint công khai KHÔNG CHÍNH THỨC mà website Vietcap dùng. Chỉ DEMO cá nhân.

[KIỂM CHỨNG] URL và cấu trúc phản hồi theo tài liệu reverse-engineer (Phụ lục C); có thể đổi bất kỳ lúc nào.
Kết quả kiểm chứng ghi trong docs/DECISIONS.md.
"""

import time
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from stockai import config
from stockai.errors import TransientError
from stockai.models import OHLCVBar

URL = "https://trading.vietcap.com.vn/api/chart/OHLCChart/gap-chart"
VN = ZoneInfo(config.TZ)


def parse_response(data) -> list[OHLCVBar]:
    item = data[0] if isinstance(data, list) else data
    ts, o, h, lo, c, v = (item[k] for k in ("t", "o", "h", "l", "c", "v"))
    bars = []
    for i in range(len(ts)):
        d = datetime.fromtimestamp(int(ts[i]), tz=UTC).astimezone(VN).date()
        bars.append(OHLCVBar(date=d, open=float(o[i]), high=float(h[i]), low=float(lo[i]), close=float(c[i]),
                             volume=float(v[i])))
    bars.sort(key=lambda b: b.date)
    return bars


class PublicVciProvider:
    name = "Vietcap công khai (không chính thức)"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(1, max=4), retry=retry_if_exception_type(TransientError),
           reraise=True)
    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]:
        body = {"timeFrame": "ONE_DAY", "symbols": [symbol], "to": int(time.time()) + 86400, "countBack": sessions + 5}
        headers = {"User-Agent": config.USER_AGENT, "Content-Type": "application/json",
                   "Referer": "https://trading.vietcap.com.vn/", "Origin": "https://trading.vietcap.com.vn"}
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(URL, json=body, headers=headers)
        except httpx.TransportError as e:
            raise TransientError(f"Lỗi mạng: {e}") from e
        if r.status_code >= 500:
            raise TransientError(f"HTTP {r.status_code}")
        r.raise_for_status()
        bars = parse_response(r.json())
        if len(bars) < 21:
            raise ValueError(f"Chỉ nhận được {len(bars)} phiên")
        return bars[-sessions:]
