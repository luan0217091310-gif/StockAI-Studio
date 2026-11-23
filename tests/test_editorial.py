"""factcheck, hậu kiểm, template fallback, generate_checked (R-LEGAL-1, R-LEGAL-4)."""

import pytest

from stockai import config
from stockai.analysis import factcheck
from stockai.providers.llm.base import build_prompts, generate_checked
from stockai.providers.llm.template_fallback import TemplateFallbackProvider


@pytest.mark.parametrize("raw,val", [("1.285,40", 1285.4), ("1285,4", 1285.4), ("+0,97", 0.97), ("-12,35", -12.35), ("450", 450)])
def test_parse_formats(raw, val):
    assert factcheck.parse_vn_number(raw) == pytest.approx(val)


def test_extract_numbers_vn_formats():
    nums = [v for _, v in factcheck.extract_numbers("VN-Index 1.285,40 điểm (+0,97%), giảm -12,35 điểm, 450 tỷ")]
    assert 1285.4 in nums and 0.97 in [abs(x) for x in nums] and 450 in nums


def test_factcheck_accepts_real_numbers(ctx):
    m = ctx.market
    from stockai.text.format import fmt
    text = f"VN-Index đóng cửa {fmt(m.close)} điểm, {fmt(abs(m.change_pct))}%, SMA20 {fmt(m.sma20)}, RSI {fmt(m.rsi14, 1)}, khối ngoại bán 450 tỷ."
    assert factcheck.check_numbers(text, ctx) == []


def test_factcheck_catches_invented_number(ctx):
    errs = factcheck.check_numbers("VN-Index có thể lên 1.999,99 điểm", ctx)
    assert errs and "1.999,99" in errs[0]


def test_factcheck_ticker(ctx):
    assert factcheck.check_tickers("HPG giảm mạnh", ctx) == []
    assert factcheck.check_tickers("VNM tăng trần", ctx)


async def test_template_passes_postcheck(ctx):
    out = await TemplateFallbackProvider().generate(ctx)
    assert factcheck.postcheck(out, ctx) == []
    assert 160 <= len(out.video_script.split()) <= 220
    assert out.video_script.endswith(config.DISCLAIMER)
    assert config.AI_DECLARATION in out.social_post_text
    assert len(out.ticker_text) <= 120


async def test_template_all_hook_styles(ctx):
    for h in config.HOOK_STYLES:
        out = await TemplateFallbackProvider().generate(ctx.model_copy(update={"hook_style": h}))
        assert factcheck.postcheck(out, ctx) == [], h


async def test_postcheck_detects_banned_and_missing_disclaimer(ctx):
    out = await TemplateFallbackProvider().generate(ctx)
    bad = out.model_copy(update={"video_script": out.video_script.replace(config.DISCLAIMER, "Hãy mua ngay.")})
    errs = factcheck.postcheck(bad, ctx)
    assert any("miễn trừ" in e for e in errs) and any("mua ngay" in e for e in errs)


class FakeLLM:
    name, model = "fake", "fake-1"

    def __init__(self, out):
        self.out, self.calls = out, 0

    async def generate(self, ctx, feedback=None):
        self.calls += 1
        self.feedback = feedback
        return self.out


async def test_invented_numbers_blocked_then_fallback(ctx):
    good = await TemplateFallbackProvider().generate(ctx)
    lying = good.model_copy(update={"video_script": "Chỉ số sẽ lên 1.999,99 điểm. " + good.video_script})
    llm = FakeLLM(lying)
    out, meta = await generate_checked(llm, TemplateFallbackProvider(), ctx, lambda *a: None)
    assert llm.calls == 2 and "1.999,99" in llm.feedback      # gọi lại 1 lần với feedback
    assert meta["factcheck_passed"] == 0 and meta["llm_provider"] == "template_fallback"
    assert "1.999,99" not in out.video_script


async def test_valid_llm_accepted(ctx):
    good = await TemplateFallbackProvider().generate(ctx)
    out, meta = await generate_checked(FakeLLM(good), TemplateFallbackProvider(), ctx, lambda *a: None)
    assert meta["llm_provider"] == "fake" and meta["factcheck_passed"] == 1


def test_prompt_contains_rules(ctx):
    sys, user = build_prompts(ctx, "- lỗi A")
    assert "160–220 từ" in sys and config.DISCLAIMER in sys and "23/11/2026" in sys
    assert "lỗi A" in user and '"i": 0' in user
