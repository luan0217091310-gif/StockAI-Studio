"""Prompt + dựng ngữ cảnh + chạy LLM có hậu kiểm & fallback (Blueprint 9.4)."""

import json
from collections.abc import Callable
from datetime import date

from stockai import config
from stockai.analysis.factcheck import postcheck
from stockai.models import ScriptContext, ScriptOutput

SESSION_LABEL = {"PRE_MARKET": "trước phiên", "POST_MARKET": "tổng kết phiên", "ADHOC": "điểm tin"}

SYSTEM_PROMPT = """Bạn là biên tập viên bản tin chứng khoán Việt Nam. Viết bản tin {session_label} ngày {dd_mm_yyyy}
DỰA DUY NHẤT trên DỮ LIỆU THỊ TRƯỜNG và danh sách TIN bên dưới.

QUY TẮC BẮT BUỘC
1. Chỉ dùng con số, mã cổ phiếu, sự kiện có trong dữ liệu. Trường nào null thì không nhắc tới.
2. Không khuyến nghị mua/bán/nắm giữ bất kỳ mã nào. Không cam kết lợi nhuận. Không dùng các cụm
   "chắc chắn", "mua ngay", "bắt đáy ngay", "x2 tài khoản", "cơ hội cuối cùng".
3. Đưa đúng 2 kịch bản: "CƠ SỞ" và "THẬN TRỌNG", dựa trên hỗ trợ, kháng cự, RSI, SMA20 và dòng tiền (nếu có).
4. selected_news: chọn 3–4 tin tác động lớn nhất; source_index phải đúng chỉ số trong danh sách TIN.
5. video_script: 160–220 từ, văn nói của MC tài chính, câu ngắn, dễ nghe. Mở đầu bằng một câu hook
   theo phong cách: {hook_style}. Viết số theo kiểu Việt Nam (1.285,4 điểm; 0,97%).
   Không markdown, không emoji, không ký hiệu đặc biệt.
   Câu cuối PHẢI là: "Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư."
6. social_post_text: gạch đầu dòng, emoji vừa phải, nêu 2 kịch bản, ghi tên nguồn tin,
   kết thúc bằng câu miễn trừ trách nhiệm và dòng "Video có sử dụng AI (MC ảo, giọng đọc tổng hợp)."
7. ticker_text: tối đa 120 ký tự, dạng "VN-INDEX 1.285,4 (+0,97%) | ...".
8. Trả về đúng JSON theo schema."""

USER_PROMPT = """DỮ LIỆU THỊ TRƯỜNG:
{market_json}

TIN (đã đánh số):
{news_json}"""


def hook_style_for(d: date) -> str:
    return config.HOOK_STYLES[d.toordinal() % len(config.HOOK_STYLES)]


def market_json(ctx: ScriptContext) -> str:
    m = ctx.market
    data = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in m.model_dump(exclude={"bars"}).items()}
    data["session_date"] = m.session_date.strftime("%d/%m/%Y")
    if m.data_quality == "CACHED":
        data["ghi_chu"] = f"Số liệu phiên ngày {m.session_date.strftime('%d/%m')} (R-DATA-3: phải nói rõ)"
    return json.dumps(data, ensure_ascii=False)


def news_json(ctx: ScriptContext) -> str:
    return json.dumps([{"i": i, "title": n.title, "summary": n.summary, "source": n.source}
                       for i, n in enumerate(ctx.news)], ensure_ascii=False)


def build_prompts(ctx: ScriptContext, feedback: str | None = None) -> tuple[str, str]:
    sys = SYSTEM_PROMPT.format(session_label=SESSION_LABEL[ctx.session_type], dd_mm_yyyy=ctx.run_date.strftime("%d/%m/%Y"),
                               hook_style=ctx.hook_style)
    user = USER_PROMPT.format(market_json=market_json(ctx), news_json=news_json(ctx))
    if feedback:
        user += f"\n\nBẢN TRƯỚC BỊ LỖI, HÃY SỬA:\n{feedback}"
    return sys, user


async def generate_checked(primary, fallback, ctx: ScriptContext, emit: Callable[[str, str], None]) -> tuple[ScriptOutput, dict]:
    """Gọi LLM → hậu kiểm → gọi lại 1 lần với feedback → vẫn lỗi thì TemplateFallback."""
    meta = {"llm_provider": fallback.name, "llm_model": "-", "factcheck_passed": 1}
    if primary is not None:
        feedback = None
        for attempt in (1, 2):
            try:
                out = await primary.generate(ctx, feedback)
            except Exception as e:
                emit("WARN", f"{primary.name}: {type(e).__name__}: {str(e)[:200]}")
                break
            errs = postcheck(out, ctx)
            if not errs:
                emit("SUCCESS", f"{primary.name} ({getattr(primary, 'model', '')}) tạo kịch bản hợp lệ, qua factcheck (lần {attempt})")
                return out, {"llm_provider": primary.name, "llm_model": getattr(primary, "model", ""), "factcheck_passed": 1}
            emit("WARN", f"Hậu kiểm lần {attempt} lỗi: " + "; ".join(errs[:5]))
            feedback = "\n".join(f"- {e}" for e in errs)
        meta["factcheck_passed"] = 0
        emit("WARN", "LLM không đạt hậu kiểm → dùng TemplateFallbackProvider")
    out = await fallback.generate(ctx)
    errs = postcheck(out, ctx)
    if errs:
        raise ValueError("TemplateFallback không qua hậu kiểm: " + "; ".join(errs))
    return out, meta
