"""CsvImportProvider — người dùng thả file CSV date,open,high,low,close,volume."""

from pathlib import Path

import pandas as pd

from stockai import config
from stockai.models import OHLCVBar


class CsvImportProvider:
    name = "CSV người dùng"

    def __init__(self, path: Path | None = None):
        self.path = path or (config.data_dir() / "market.csv")

    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]:
        if not self.path.exists():
            raise FileNotFoundError(f"Không có file {self.path}")
        df = pd.read_csv(self.path)
        df.columns = [c.strip().lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df.sort_values("date").tail(sessions)
        return [OHLCVBar(**r) for r in df[["date", "open", "high", "low", "close", "volume"]].to_dict("records")]
