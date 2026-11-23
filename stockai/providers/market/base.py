"""Chuỗi provider thị trường (Blueprint 9.2)."""

from collections.abc import Callable

from stockai.analysis.indicators import build_snapshot
from stockai.errors import ProviderError
from stockai.models import MarketSnapshot


async def fetch_snapshot(order: list[str], symbol: str, mode: str, offline: bool, repo=None,
                         emit: Callable[[str, str], None] | None = None) -> MarketSnapshot:
    from stockai.providers.market.cache import CacheProvider
    from stockai.providers.market.csv_import import CsvImportProvider
    from stockai.providers.market.public_vci import PublicVciProvider
    from stockai.providers.market.ssi_fc import SsiFastConnectProvider
    from stockai.providers.market.synthetic import SyntheticProvider

    say = emit or (lambda lvl, m: None)
    registry = {"ssi_fc": SsiFastConnectProvider, "public_vci": PublicVciProvider, "csv": CsvImportProvider,
                "cache": CacheProvider, "synthetic": SyntheticProvider}
    for name in order:
        if name == "synthetic" and mode != "DEMO":
            continue  # SyntheticProvider chỉ dùng ở DEMO
        if name == "public_vci" and mode != "DEMO":
            continue  # D7: tắt nguồn không chính thức ở PRODUCTION
        cls = registry.get(name)
        if not cls:
            continue
        if offline and name in ("ssi_fc", "public_vci"):
            say("DEBUG", f"{name}: bỏ qua (offline)")
            continue
        try:
            if name == "cache":
                snap = await CacheProvider(repo).snapshot(symbol)
                say("INFO", f"Dùng snapshot đã lưu ({snap.session_date})")
                return snap
            prov = cls()
            bars = await prov.fetch_daily(symbol, 60)
            quality = "SYNTHETIC" if name == "synthetic" else "LIVE"
            snap = build_snapshot(bars, prov.name, quality, symbol)
            say("INFO", f"Nguồn thị trường: {prov.name} ({len(bars)} phiên)")
            return snap
        except Exception as e:  # thử nguồn tiếp theo
            say("WARN", f"{name}: {type(e).__name__}: {str(e)[:160]}")
    raise ProviderError("Không lấy được dữ liệu thị trường từ nguồn nào", code="MARKET_UNAVAILABLE",
                        hint="Kiểm tra mạng, hoặc thả file CSV vào thư mục dữ liệu (market.csv)")
