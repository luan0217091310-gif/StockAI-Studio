"""vi_normalize, phụ đề, captions, layout safe-zone."""

from stockai.layout import LAYOUT
from stockai.models import WordTiming
from stockai.render import subtitles
from stockai.text import captions
from stockai.text.vi_normalize import normalize_for_tts, number_to_words


def test_vi_normalize_rules():
    s = normalize_for_tts("VN-INDEX +12,35 điểm (0,97%) | 📈 *mạnh* #tag")
    assert "tăng 12,35 điểm" in s and "0,97 phần trăm" in s and "VN-Index" in s
    assert "|" not in s and "📈" not in s and "*" not in s and "#" not in s
    assert "giảm 5,2 điểm" in normalize_for_tts("-5,2 điểm")


def test_number_words():
    assert number_to_words("1.285") == "một nghìn hai trăm tám mươi lăm"
    assert number_to_words("21") == "hai mươi mốt"
    assert number_to_words("0,97") == "không phẩy chín mươi bảy"


def _words(n=120):
    ws, t = [], 0
    for i in range(n):
        w = ("chứng khoán," if i % 9 == 8 else "thị trường.") if i % 13 == 12 else "VN-Index"
        ws.append(WordTiming(text=w, start_ms=t, end_ms=t + 300))
        t += 330
    return ws


def test_cues_two_lines_width_no_overlap():
    cues = subtitles.build_cues(_words())
    assert cues
    for c in cues:
        assert 1 <= len(c["lines"]) <= 2
        assert all(subtitles.text_width(ln) <= LAYOUT.subtitle_max_line_px for ln in c["lines"])
        assert c["end"] > c["start"]
    for a, b in zip(cues, cues[1:], strict=False):
        assert a["end"] <= b["start"]


def test_srt_ass_format():
    cues = subtitles.build_cues(_words(20))
    srt, ass = subtitles.to_srt(cues), subtitles.to_ass(cues)
    assert srt.startswith("1\n00:00:00,000 --> ")
    assert "Style: Main,Be Vietnam Pro,60,&H0015CCFA" in ass and "Dialogue: 0,0:00:00.00" in ass
    assert "MarginV" in ass and ",140,140,520,1" in ass


def test_distribute_sentence():
    ws = subtitles.distribute_sentence("một hai ba", 0, 900)
    assert len(ws) == 3 and ws[-1].end_ms <= 900


def test_captions_limits():
    post = "\n".join(["• dòng " + "x" * 300] * 30) + "\nNội dung chỉ mang tính tham khảo."
    c = captions.build_all("Tiêu đề " * 20, post, ["#a", "b"])
    assert len(c["telegram"]["caption"]) <= 1024
    assert all(len(m) <= 4096 for m in c["telegram"]["messages"])
    assert len(c["youtube"]["title"]) <= 100 and c["youtube"]["title"].endswith("#Shorts")
    assert len(c["tiktok"]["title"]) <= 2200 and len(c["facebook"]["description"]) <= 2200


def test_layout_inside_frame_and_safe():
    L = LAYOUT
    for name in ("header", "ticker", "broll", "ai_label", "divider", "avatar", "subtitles", "wave", "disclaimer"):
        b = getattr(L, name)
        assert 0 <= b.x and b.x2 <= L.W and 0 <= b.y and b.y2 <= L.H, name
    for name, box in L.important_zones.items():
        for z in L.unsafe_zones:
            assert not box.intersects(z), f"{name} giao với vùng bị che {z}"
    assert L.H - L.subtitle_margin_v == L.subtitles.y2  # đáy phụ đề y=1400
    assert L.broll.y2 == L.divider.y and L.divider.y2 == L.avatar.y and L.avatar.y2 == L.H
