"""SyntheticProvider — random walk có seed cố định. CHỈ DEMO; luôn gắn nhãn SYNTHETIC."""

import random
from datetime import date, timedelta

from stockai.models import OHLCVBar


def trading_days(n: int, end: date) -> list[date]:
    d, out = end, []
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= timedelta(days=1)
    return out[::-1]


class SyntheticProvider:
    name = "Dữ liệu minh họa (Synthetic)"

    def __init__(self, end: date | None = None, seed: int = 20261123):
        self.end = end or date.today()
        self.seed = seed

    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]:
        rnd = random.Random(self.seed)
        c = 1650 + rnd.random() * 50
        bars = []
        for d in trading_days(sessions, self.end):
            o = c * (1 + (rnd.random() - 0.5) * 0.006)
            c = o * (1 + (rnd.random() - 0.48) * 0.018)
            h = max(o, c) * (1 + rnd.random() * 0.006)
            lo = min(o, c) * (1 - rnd.random() * 0.006)
            bars.append(OHLCVBar(date=d, open=round(o, 2), high=round(h, 2), low=round(lo, 2), close=round(c, 2),
                                 volume=round(550e6 + rnd.random() * 450e6)))
        return bars
