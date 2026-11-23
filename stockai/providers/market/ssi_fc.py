"""SsiFastConnectProvider — API chính thức FastConnect Data của SSI (PRODUCTION).

[KIỂM CHỨNG] URL, tham số, đơn vị phải đối chiếu https://guide.ssi.com.vn/ssi-products/fastconnect-data
trước khi bật. Cần consumer_id/consumer_secret (lưu keyring). Quyết định D1 (Mục 17) chưa chốt.
"""

from datetime import date, datetime, timedelta

import httpx

from stockai import secrets
from stockai.errors import ConfigError
from stockai.models import OHLCVBar

BASE = "https://fc-data.ssi.com.vn/api/v2/Market"


class SsiFastConnectProvider:
    name = "SSI FastConnect Data"

    async def _token(self, c: httpx.AsyncClient) -> str:
        cid, sec = secrets.get_secret("ssi_consumer_id"), secrets.get_secret("ssi_consumer_secret")
        if not cid or not sec:
            raise ConfigError("Chưa cấu hình SSI consumer ID/secret", hint="Cài đặt → Dữ liệu → SSI FastConnect")
        r = await c.post(f"{BASE}/AccessToken", json={"consumerID": cid, "consumerSecret": sec})
        r.raise_for_status()
        return r.json()["data"]["accessToken"]

    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]:
        async with httpx.AsyncClient(timeout=15) as c:
            tok = await self._token(c)
            to = date.today()
            frm = to - timedelta(days=int(sessions * 1.6) + 10)
            r = await c.get(f"{BASE}/DailyIndex", headers={"Authorization": f"Bearer {tok}"},
                            params={"indexId": symbol, "fromDate": frm.strftime("%d/%m/%Y"), "toDate": to.strftime("%d/%m/%Y"),
                                    "pageIndex": 1, "pageSize": 1000})
            r.raise_for_status()
            rows = r.json().get("data") or []
        bars = []
        for x in rows:
            d = datetime.strptime(x["TradingDate"], "%d/%m/%Y").date()
            close = float(x["IndexValue"])
            bars.append(OHLCVBar(date=d, open=float(x.get("Open") or close), high=float(x.get("High") or close),
                                 low=float(x.get("Low") or close), close=close, volume=float(x.get("TotalVol") or 0)))
        bars.sort(key=lambda b: b.date)
        return bars[-sessions:]
