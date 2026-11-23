"""TemplateFallbackProvider — kịch bản tiếng Việt từ mẫu, luôn qua hậu kiểm. Đường chạy chuẩn khi --offline."""

from stockai import config
from stockai.models import NewsHighlight, Scenario, ScriptContext, ScriptOutput
from stockai.text.format import fmt, fmt_signed

LABEL = {"PRE_MARKET": "trước phiên", "POST_MARKET": "tổng kết phiên", "ADHOC": "điểm tin"}
LABEL_UP = {"PRE_MARKET": "TRƯỚC PHIÊN", "POST_MARKET": "TỔNG KẾT PHIÊN", "ADHOC": "ĐIỂM TIN"}


def _headline(title: str) -> str:
    words = title.split()
    h = " ".join(words[:12])
    while len(h) > 90:
        words = words[:-1]
        h = " ".join(words[:12])
    return h


def _sentence(s: str) -> str:
    s = s.strip().rstrip(".…")
    return s + "."


class TemplateFallbackProvider:
    name = "template_fallback"
    model = "-"

    async def generate(self, ctx: ScriptContext, feedback: str | None = None) -> ScriptOutput:
        m, d = ctx.market, ctx.run_date
        up = m.change >= 0
        dir_ = "tăng" if up else "giảm"
        sd = m.session_date.strftime("%d/%m")
        news = ctx.news[:3]
        hooks = {
            "câu hỏi gợi tò mò": f"Sau phiên {dir_} {fmt(abs(m.change))} điểm, VN-Index sẽ đi tiếp theo hướng nào?",
            "con số nổi bật nhất": f"{fmt(m.close)} điểm, đó là mức đóng cửa mới nhất của VN-Index.",
            "so sánh với phiên trước": f"So với phiên trước, VN-Index đã {dir_} {fmt(abs(m.change_pct))}%.",
            "tin nóng nhất": f"Tin đáng chú ý nhất lúc này: {_sentence(news[0].title)}" if news else "Thị trường có nhiều thông tin đáng chú ý.",
            "cảnh báo nhẹ nhàng": "Thị trường đang ở vùng nhạy cảm, hãy cùng điểm lại các tín hiệu cần lưu ý.",
        }
        templates = [
            "Xin chào quý vị, đây là bản tin chứng khoán {label} ngày {dmy}.",
            "Chào mừng quý vị đến với bản tin chứng khoán {label} ngày {dmy}.",
            "Kính chào quý vị, cùng điểm lại thị trường trong bản tin {label} ngày {dmy}.",
        ]
        greet = templates[d.toordinal() % len(templates)].format(label=LABEL[ctx.session_type], dmy=d.strftime("%d/%m/%Y"))
        rsi_state = "quá mua" if m.rsi14 > 70 else "quá bán" if m.rsi14 < 30 else "trung tính"
        cached = f" Lưu ý, đây là số liệu phiên ngày {sd}." if m.data_quality == "CACHED" else ""
        parts = [
            hooks.get(ctx.hook_style, hooks["con số nổi bật nhất"]), greet,
            f"Kết thúc phiên ngày {sd}, VN-Index đóng cửa tại {fmt(m.close)} điểm, {dir_} {fmt(abs(m.change))} điểm, tương ứng {fmt(abs(m.change_pct))}%.{cached}",
            f"Về kỹ thuật, chỉ số đang nằm {'trên' if m.close >= m.sma20 else 'dưới'} đường trung bình 20 phiên ở mức {fmt(m.sma20)} điểm.",
            f"Chỉ báo RSI 14 phiên ở mức {fmt(m.rsi14)}, cho thấy trạng thái {rsi_state}.",
            f"Vùng hỗ trợ gần nhất quanh {fmt(m.support20)} điểm, còn kháng cự nằm quanh {fmt(m.resistance20)} điểm.",
            "Tiếp theo là các tin đáng chú ý.",
        ]
        ordinals = ["Thứ nhất", "Thứ hai", "Thứ ba"]
        for i, n in enumerate(news):
            parts.append(f"{ordinals[i]}, theo {n.source}, {_sentence(n.title[0].lower() + n.title[1:])}")
        scen_base = f"Kịch bản cơ sở, chỉ số có thể dao động trong vùng từ {fmt(m.support20)} đến {fmt(m.resistance20)} điểm khi thị trường chờ thêm thông tin mới."
        scen_safe = f"Kịch bản thận trọng, nếu đánh mất vùng hỗ trợ {fmt(m.support20)} điểm, áp lực điều chỉnh có thể gia tăng, vì vậy việc quản trị rủi ro là rất quan trọng."
        closing = ["Cảm ơn quý vị đã theo dõi, hẹn gặp lại trong bản tin tiếp theo.", config.DISCLAIMER]
        fillers = [_sentence(n.summary) for n in news if n.summary] + [
            "Diễn biến dòng tiền trong những phiên tới sẽ là yếu tố quan trọng cần theo dõi.",
            "Quý vị nên theo dõi thêm thông tin từ các nguồn chính thức trước khi ra quyết định.",
            "Biến động ngắn hạn có thể còn lớn, vì vậy cần giữ sự bình tĩnh và kỷ luật.",
        ]

        def assemble(extra: list[str]) -> str:
            return " ".join(parts + extra + [scen_base, scen_safe] + closing)

        extra: list[str] = []
        text = assemble(extra)
        for f in fillers:
            if len(text.split()) >= 170:
                break
            if len(assemble(extra + [f]).split()) > 215:
                continue
            extra.append(f)
            text = assemble(extra)
        # cắt nếu quá dài (tin quá dài)
        while len(text.split()) > 220 and len(parts) > 7:
            parts.pop()
            text = assemble(extra)

        sentiment = "BULLISH" if m.change_pct > 0.3 else "BEARISH" if m.change_pct < -0.3 else "NEUTRAL"
        ticker = f"VN-INDEX {fmt(m.close)} ({fmt_signed(m.change_pct)}%) | SMA20 {fmt(m.sma20)} | RSI14 {fmt(m.rsi14)}"[:120]
        scenarios = [
            Scenario(name="CƠ SỞ", description=f"Dao động trong vùng {fmt(m.support20)} – {fmt(m.resistance20)} điểm, thị trường chờ thêm thông tin mới."),
            Scenario(name="THẬN TRỌNG", description=f"Nếu đánh mất hỗ trợ {fmt(m.support20)} điểm, áp lực điều chỉnh có thể gia tăng."),
        ]
        sources = ", ".join(dict.fromkeys(n.source for n in news))
        post = "\n".join([
            f"📊 BẢN TIN CHỨNG KHOÁN {LABEL_UP[ctx.session_type]} {d.strftime('%d/%m/%Y')}", "",
            f"• VN-Index: {fmt(m.close)} điểm ({fmt_signed(m.change)} | {fmt_signed(m.change_pct)}%) — phiên {sd}",
            f"• SMA20: {fmt(m.sma20)} · RSI14: {fmt(m.rsi14)}",
            f"• Hỗ trợ {fmt(m.support20)} · Kháng cự {fmt(m.resistance20)}", "",
            "📰 Tin đáng chú ý:", *[f"• {n.title} ({n.source})" for n in news], "",
            f"🔹 Kịch bản cơ sở: {scenarios[0].description}",
            f"🔸 Kịch bản thận trọng: {scenarios[1].description}", "",
            f"Nguồn tin: {sources}." if sources else "", config.DISCLAIMER, config.AI_DECLARATION,
        ])
        title = f"Bản tin {LABEL[ctx.session_type]} {d.strftime('%d/%m')}: VN-Index {dir_} {fmt(abs(m.change_pct))}%"[:80]
        return ScriptOutput(
            video_title=title, market_sentiment=sentiment,
            selected_news=[NewsHighlight(headline=_headline(n.title), impact="TRUNG LẬP", brief=n.summary or n.title,
                                         source_index=i) for i, n in enumerate(news)],
            scenarios=scenarios, social_post_text=post, video_script=text, ticker_text=ticker,
            hashtags=["#chungkhoan", "#VNIndex", "#bantinchungkhoan", "#taichinh"],
        )
