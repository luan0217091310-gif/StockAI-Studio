"""Chỉ báo kỹ thuật — hàm thuần (Blueprint 9.2)."""

import pandas as pd

from stockai.models import MarketSnapshot, OHLCVBar


def sma(close: pd.Series, n: int = 20) -> pd.Series:
    return close.rolling(n).mean()


def rsi_wilder(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rsi = 100 - 100 / (1 + gain / loss)
    return rsi.where(loss != 0, 100.0)


def support_resistance(low: pd.Series, high: pd.Series, n: int = 20) -> tuple[float, float]:
    return float(low.tail(n).min()), float(high.tail(n).max())


def build_snapshot(bars: list[OHLCVBar], source: str, quality: str, symbol: str = "VNINDEX") -> MarketSnapshot:
    if len(bars) < 21:
        raise ValueError("Cần tối thiểu 21 phiên để tính chỉ báo")
    df = pd.DataFrame([b.model_dump() for b in bars])
    close = df["close"]
    change = float(close.iloc[-1] - close.iloc[-2])
    sup, res = support_resistance(df["low"], df["high"])
    return MarketSnapshot(
        symbol=symbol, session_date=bars[-1].date, bars=bars, close=round(float(close.iloc[-1]), 2),
        change=round(change, 2), change_pct=round(change / float(close.iloc[-2]) * 100, 2),
        volume=float(df["volume"].iloc[-1]), sma20=round(float(sma(close).iloc[-1]), 2),
        rsi14=round(float(rsi_wilder(close).iloc[-1]), 2), support20=round(sup, 2), resistance20=round(res, 2),
        source=source, data_quality=quality,  # type: ignore[arg-type]
    )
