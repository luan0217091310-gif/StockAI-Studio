"""Kiểm tra số liệu trong kịch bản bằng code (Blueprint 9.4 — hậu kiểm)."""

import re

from stockai import config
from stockai.models import ScriptContext, ScriptOutput

NUM_RE = re.compile(r"(?<![\w])[+-]?\d{1,3}(?:\.\d{3})+(?:,\d+)?|(?<![\w.,])[+-]?\d+(?:,\d+)?")
TICKER_RE = re.compile(r"\b[A-Z]{3}\b")
TICKER_WHITELIST = {"SMA", "RSI", "HNX", "VND", "USD", "ETF", "GDP", "CPI", "FED", "NHNN"}
SMALL_NUMBERS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 14, 20, 60}


def parse_vn_number(s: str) -> float:
    s = s.strip()
    return float(s.replace(".", "").replace(",", "."))


def extract_numbers(text: str) -> list[tuple[str, float]]:
    out = []
    for m in NUM_RE.finditer(text):
        raw = m.group(0)
        try:
            out.append((raw, parse_vn_number(raw)))
        except ValueError:
            continue
    return out


def allowed_numbers(ctx: ScriptContext) -> list[float]:
    m = ctx.market
    vals: list[float] = [m.close, m.change, m.change_pct, m.sma20, m.rsi14, m.support20, m.resistance20]
    for v in (m.volume, m.value_bn_vnd, m.foreign_net_bn_vnd):
        if v is not None:
            vals += [v, v / 1e6, v / 1e3]
    for d in (m.session_date, ctx.run_date):
        vals += [d.day, d.month, d.year]
    vals += list(SMALL_NUMBERS)
    for n in ctx.news:
        vals += [x for _, x in extract_numbers(n.title + " " + n.summary)]
    return vals


def _ok(v: float, allowed: list[float]) -> bool:
    v = abs(v)
    for a in allowed:
        a = abs(a)
        if abs(a - v) <= 0.01 or (a and abs(a - v) / a <= 0.005):
            return True
        for d in (0, 1):
            if abs(round(a, d) - v) <= 0.01:
                return True
    return False


def check_numbers(text: str, ctx: ScriptContext) -> list[str]:
    allowed = allowed_numbers(ctx)
    return [f"Số không có trong dữ liệu đầu vào: {raw}" for raw, v in extract_numbers(text) if not _ok(v, allowed)]


def check_tickers(text: str, ctx: ScriptContext) -> list[str]:
    corpus = " ".join(n.title + " " + n.summary for n in ctx.news).upper() + " VNINDEX VN-INDEX"
    return [f"Mã không có trong dữ liệu đầu vào: {t}" for t in sorted(set(TICKER_RE.findall(text)))
            if t not in TICKER_WHITELIST and t not in corpus]


def factcheck(out: ScriptOutput, ctx: ScriptContext) -> list[str]:
    text = "\n".join([out.video_script, out.social_post_text, out.ticker_text])
    return check_numbers(text, ctx) + check_tickers(text, ctx)


def word_count(s: str) -> int:
    return len(s.split())


def postcheck(out: ScriptOutput, ctx: ScriptContext) -> list[str]:
    """Hậu kiểm bắt buộc 2–5 (R-LEGAL-1, R-LEGAL-4)."""
    errs: list[str] = []
    wc = word_count(out.video_script)
    if not 160 <= wc <= 220:
        errs.append(f"video_script có {wc} từ (yêu cầu 160–220)")
    for h in out.selected_news:
        if word_count(h.headline) > 12:
            errs.append(f"headline quá 12 từ: {h.headline}")
        if not 0 <= h.source_index < len(ctx.news):
            errs.append(f"source_index không hợp lệ: {h.source_index}")
    if not out.video_script.strip().endswith(config.DISCLAIMER):
        errs.append("Câu cuối video_script phải là câu miễn trừ trách nhiệm")
    if config.DISCLAIMER not in out.social_post_text:
        errs.append("social_post_text thiếu câu miễn trừ trách nhiệm")
    if config.AI_DECLARATION not in out.social_post_text:
        errs.append("social_post_text thiếu dòng khai báo AI")
    low = (out.video_script + " " + out.social_post_text + " " + out.video_title).lower()
    errs += [f"Chứa cụm từ cấm: '{b}'" for b in config.BANNED_PHRASES if b in low]
    for field, val in (("value_bn_vnd", ctx.market.value_bn_vnd), ("foreign_net_bn_vnd", ctx.market.foreign_net_bn_vnd)):
        if val is None and field == "foreign_net_bn_vnd" and re.search(r"khối ngoại (mua|bán) ròng \d", low):
            errs.append("Nhắc số liệu khối ngoại khi dữ liệu không có")
    return errs + factcheck(out, ctx)
