"""CacheProvider — đọc market_snapshots gần nhất → data_quality = CACHED."""

import json

from stockai.analysis.indicators import build_snapshot
from stockai.models import MarketSnapshot, OHLCVBar


class CacheProvider:
    name = "Bộ nhớ đệm"

    def __init__(self, repo):
        self.repo = repo

    async def snapshot(self, symbol: str) -> MarketSnapshot:
        if self.repo is None:
            raise LookupError("Không có repo")
        row = self.repo.latest_snapshot(symbol)
        if not row:
            raise LookupError("Chưa có snapshot thật nào được lưu")
        bars = [OHLCVBar(**b) for b in json.loads(row["bars_json"])]
        snap = build_snapshot(bars, f"{row['source']} (đã lưu)", "CACHED", symbol)
        snap.foreign_net_bn_vnd = row["foreign_net_bn_vnd"]
        snap.value_bn_vnd = row["value_bn_vnd"]
        return snap

    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]:
        return (await self.snapshot(symbol)).bars[-sessions:]
