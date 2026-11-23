"""Word timings → cues → SRT + ASS (Blueprint 9.5, 10.4). Hàm thuần."""

from functools import lru_cache

from PIL import ImageFont

from stockai import config
from stockai.layout import LAYOUT
from stockai.models import WordTiming

MIN_CUE_MS, MAX_CUE_MS, GAP_MS = 800, 3500, 150


@lru_cache(maxsize=1)
def _font():
    return ImageFont.truetype(str(config.FONT_BOLD), LAYOUT.subtitle_font_size)


def text_width(s: str) -> float:
    return _font().getlength(s)


def build_cues(words: list[WordTiming], max_px: int = LAYOUT.subtitle_max_line_px) -> list[dict]:
    cues: list[dict] = []
    lines: list[str] = [""]
    start = end = None

    def flush():
        nonlocal lines, start
        if start is not None and any(lines):
            cues.append({"start": start, "end": end, "lines": [ln for ln in lines if ln]})
        lines, start = [""], None

    for w in words:
        cand = (lines[-1] + " " + w.text).strip()
        if start is not None and text_width(cand) > max_px:
            if len(lines) < 2 and (w.end_ms - start) <= MAX_CUE_MS:
                lines.append(w.text)
            else:
                flush()
                lines = [w.text]
        else:
            lines[-1] = cand
        if start is None:
            start = w.start_ms
        end = w.end_ms
        dur = end - start
        if dur >= MAX_CUE_MS or (w.text[-1:] in ".?!;:" and dur >= MIN_CUE_MS) or (w.text[-1:] == "," and len(lines) == 2 and dur >= MIN_CUE_MS):
            flush()
    flush()
    for a, b in zip(cues, cues[1:], strict=False):
        if b["start"] - a["end"] < GAP_MS:
            a["end"] = b["start"]
    for c in cues:  # độ dài tối thiểu
        if c["end"] - c["start"] < MIN_CUE_MS:
            c["end"] = c["start"] + MIN_CUE_MS
    for a, b in zip(cues, cues[1:], strict=False):  # không chồng lấn
        if a["end"] > b["start"]:
            a["end"] = b["start"]
    return cues


def _srt_ts(ms: int) -> str:
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _ass_ts(ms: int) -> str:
    cs = round(ms / 10)
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def to_srt(cues: list[dict]) -> str:
    return "\n".join(f"{i}\n{_srt_ts(c['start'])} --> {_srt_ts(c['end'])}\n" + "\n".join(c["lines"]) + "\n"
                     for i, c in enumerate(cues, 1))


ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Be Vietnam Pro,60,&H0015CCFA,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,2,140,140,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def to_ass(cues: list[dict]) -> str:
    ev = [f"Dialogue: 0,{_ass_ts(c['start'])},{_ass_ts(c['end'])},Main,,0,0,0,,{'\\N'.join(c['lines'])}" for c in cues]
    return ASS_HEADER + "\n".join(ev) + "\n"


def distribute_sentence(text: str, start_ms: int, end_ms: int) -> list[WordTiming]:
    """Khi chỉ có SentenceBoundary: chia thời gian câu cho từng từ theo tỉ lệ số ký tự."""
    words = text.split()
    total = sum(len(w) for w in words) or 1
    out, t = [], start_ms
    for w in words:
        d = (end_ms - start_ms) * len(w) / total
        out.append(WordTiming(text=w, start_ms=int(t), end_ms=int(t + d)))
        t += d
    return out
