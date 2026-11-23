"""Biểu đồ nến 1080×660 (Blueprint 9.3)."""

import matplotlib

matplotlib.use("Agg")

from pathlib import Path  # noqa: E402

import matplotlib.pyplot as plt  # noqa: E402
import mplfinance as mpf  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from stockai import config  # noqa: E402
from stockai.models import MarketSnapshot  # noqa: E402
from stockai.text.format import fmt, fmt_signed  # noqa: E402

BG, GRID, UP, DOWN, SMA, TXT = "#0F172A", "#1E293B", "#10B981", "#F43F5E", "#F59E0B", "#E5E7EB"
_registered = False


def register_fonts() -> str:
    global _registered
    if not _registered:
        for f in (config.FONT_REGULAR, config.FONT_SEMIBOLD, config.FONT_BOLD):
            if f.exists():
                font_manager.fontManager.addfont(str(f))
        _registered = True
    return "Be Vietnam Pro"


def render_chart(m: MarketSnapshot, out: Path) -> Path:
    family = register_fonts()
    plt.rcParams["font.family"] = family
    df = pd.DataFrame([b.model_dump() for b in m.bars])
    df.index = pd.DatetimeIndex(df.pop("date"))
    df.columns = ["Open", "High", "Low", "Close", "Volume"]
    mc = mpf.make_marketcolors(up=UP, down=DOWN, edge="inherit", wick="inherit", volume={"up": UP, "down": DOWN})
    style = mpf.make_mpf_style(marketcolors=mc, facecolor=BG, figcolor=BG, edgecolor=GRID, gridcolor=GRID, gridstyle="-",
                               rc={"font.family": family, "axes.labelcolor": TXT, "xtick.color": TXT, "ytick.color": TXT,
                                   "axes.edgecolor": GRID})
    hl = dict(hlines=[m.support20, m.resistance20], colors=[UP, DOWN], linestyle="--", linewidths=1.4)
    fig, axes = mpf.plot(df, type="candle", style=style, volume=True, mav=(20,), hlines=hl, returnfig=True,
                         figsize=(10.8, 6.6), panel_ratios=(4, 1), ylabel="", ylabel_lower="", xrotation=0,
                         datetime_format="%d/%m", tight_layout=False, update_width_config={"candle_linewidth": 1.0},
                         scale_padding={"left": 0.75, "right": 0.9, "top": 2.1, "bottom": 0.5})
    ax = axes[0]
    for line in ax.get_lines():
        if line.get_linestyle() == "-" and len(line.get_xdata()) == len(df):
            line.set_color(SMA)
            line.set_linewidth(2.2)
    xmax = len(df) - 0.5
    for v, col, lb in ((m.support20, UP, "Hỗ trợ"), (m.resistance20, DOWN, "Kháng cự")):
        ax.text(xmax, v, f" {lb} {fmt(v)}", color=col, fontsize=11, va="bottom", ha="right", fontweight="bold")
    color = UP if m.change >= 0 else DOWN
    # Nhãn AI chiếm y 16–60px của khung B-roll → tiêu đề bắt đầu từ ~y 72px
    fig.text(0.035, 0.84, f"VN-INDEX | {fmt(m.close)} ({fmt_signed(m.change)} | {fmt_signed(m.change_pct)}%)",
             color=color, fontsize=21, fontweight="bold", ha="left")
    fig.text(0.035, 0.795, f"Phiên {m.session_date.strftime('%d/%m/%Y')} · Nguồn: {m.source} · SMA20 {fmt(m.sma20)} (vàng) · RSI14 {fmt(m.rsi14)}",
             color=TXT, fontsize=11.5, ha="left")
    for a in axes:
        a.tick_params(labelsize=10)
    if m.data_quality == "SYNTHETIC":
        fig.text(0.5, 0.47, config.SYNTHETIC_WATERMARK, color="#F59E0B", alpha=0.32, fontsize=30, fontweight="bold",
                 ha="center", va="center", rotation=18)
    fig.savefig(out, dpi=100, facecolor=BG)
    plt.close(fig)
    return out
