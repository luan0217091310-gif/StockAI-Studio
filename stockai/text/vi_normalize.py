"""Chuẩn hóa văn bản trước khi đọc TTS (Blueprint 9.5)."""

import re
import unicodedata

_EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF️]")
_DIGITS = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _int_words(n: int) -> str:
    if n < 10:
        return _DIGITS[n]
    if n < 100:
        t, u = divmod(n, 10)
        head = "mười" if t == 1 else _DIGITS[t] + " mươi"
        if u == 0:
            return head
        tail = {1: "mốt" if t > 1 else "một", 5: "lăm", 4: "tư" if t > 1 else "bốn"}.get(u, _DIGITS[u])
        return f"{head} {tail}"
    if n < 1000:
        h, r = divmod(n, 100)
        s = f"{_DIGITS[h]} trăm"
        if r == 0:
            return s
        return f"{s} lẻ {_DIGITS[r]}" if r < 10 else f"{s} {_int_words(r)}"
    for unit, name in ((10**9, "tỷ"), (10**6, "triệu"), (1000, "nghìn")):
        if n >= unit:
            q, r = divmod(n, unit)
            s = f"{_int_words(q)} {name}"
            if r == 0:
                return s
            return f"{s} {'không trăm ' if r < 100 else ''}{_int_words(r)}".replace("không trăm lẻ", "không trăm lẻ")
    return str(n)


def number_to_words(raw: str) -> str:
    raw = raw.replace(".", "")
    if "," in raw:
        i, f = raw.split(",", 1)
        return f"{_int_words(int(i or 0))} phẩy {' '.join(_DIGITS[int(c)] for c in f)}" if len(f) > 2 else \
            f"{_int_words(int(i or 0))} phẩy {_int_words(int(f))}"
    return _int_words(int(raw))


def normalize_for_tts(text: str, number_mode: str = "engine") -> str:
    s = nfc(text)
    s = re.sub(r"\+\s?(\d[\d.,]*)\s*điểm", r"tăng \1 điểm", s)
    s = re.sub(r"(?<![\w])-\s?(\d[\d.,]*)\s*điểm", r"giảm \1 điểm", s)
    s = re.sub(r"(\d)\s*%", r"\1 phần trăm", s)
    s = s.replace("%", " phần trăm")
    s = re.sub(r"VN-?INDEX|VN-?Index|VNINDEX", "VN-Index", s, flags=re.IGNORECASE)
    s = s.replace("|", ".")
    s = _EMOJI.sub("", s)
    s = re.sub(r"[*#_~]", "", s)
    if number_mode == "words":
        s = re.sub(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", lambda m: number_to_words(m.group(0)), s)
    return re.sub(r"\s+", " ", s).strip()
