"""Thành phần đồ họa bằng Pillow (Blueprint 9.7 Giai đoạn A + 9.6 tiền xử lý avatar)."""

import math
import unicodedata
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from stockai import config
from stockai.layout import LAYOUT as L
from stockai.models import NewsHighlight

BG = (11, 17, 32)
IMPACT_COLORS = {"TÍCH CỰC": (16, 185, 129), "TIÊU CỰC": (244, 63, 94), "TRUNG LẬP": (245, 158, 11)}
SESSION_LABEL = {"PRE_MARKET": "TRƯỚC PHIÊN", "POST_MARKET": "TỔNG KẾT PHIÊN", "ADHOC": "ĐIỂM TIN"}


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    path = {"bold": config.FONT_BOLD, "semibold": config.FONT_SEMIBOLD, "regular": config.FONT_REGULAR}[weight]
    return ImageFont.truetype(str(path), size)


def wrap(text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    lines, cur = [], ""
    for w in nfc(text).split():
        t = f"{cur} {w}".strip()
        if f.getlength(t) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def _logo(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 64) -> None:
    draw.rounded_rectangle([x, y, x + size, y + size], radius=14, fill=(16, 185, 129))
    for i, h in enumerate((0.35, 0.6, 0.85)):
        bx = x + 12 + i * 15
        draw.rectangle([bx, y + size - 10 - int((size - 20) * h), bx + 9, y + size - 10], fill=(4, 19, 13))


def make_base(out: Path, session_type: str, run_date: date, logo: Path | None = None) -> Path:
    img = Image.new("RGB", (L.W, L.H), BG)
    d = ImageDraw.Draw(img)
    hx, hy = L.header.x, L.header.y
    if logo and logo.exists():
        lg = Image.open(logo).convert("RGBA")
        lg.thumbnail((200, 72))
        img.paste(lg, (hx, hy + (L.header.h - lg.height) // 2), lg)
        tx = hx + lg.width + 16
    else:
        _logo(d, hx, hy + 18)
        tx = hx + 80
    d.text((tx, hy + 14), "BẢN TIN CHỨNG KHOÁN", font=font(38), fill=(249, 250, 251))
    d.text((tx, hy + 60), SESSION_LABEL[session_type], font=font(26, "semibold"), fill=(52, 211, 153))
    ds = run_date.strftime("%d/%m/%Y")
    f = font(30, "semibold")
    d.text((L.header.x2 - f.getlength(ds), hy + 34), ds, font=f, fill=(156, 163, 175))
    # đường phân cách phát sáng Z4
    glow = Image.new("RGBA", (L.W, 60), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rectangle([0, 26, L.W, 34], fill=(16, 185, 129, 200))
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    img.paste(glow, (0, L.divider.y - 28), glow)
    d.rectangle([0, L.divider.y, L.W, L.divider.y2 - 1], fill=(16, 185, 129))
    img.save(out)
    return out


def make_news_card(h: NewsHighlight, source: str, out: Path, idx: int, synthetic: bool) -> Path:
    W, H = L.broll.w, L.broll.h
    img = Image.new("RGB", (W, H))
    top, bot = (15, 23, 42), (17, 24, 39)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))
    col = IMPACT_COLORS[h.impact]
    d.rectangle([60, 110, 67, 560], fill=col)
    f_tag = font(26)
    tw = int(f_tag.getlength(h.impact)) + 36
    d.rounded_rectangle([96, 100, 96 + tw, 146], radius=23, fill=tuple(int(c * 0.25) for c in col))
    d.text((114, 106), h.impact, font=f_tag, fill=col)
    d.text((120 + tw, 108), f"TIN NÓNG #{idx + 1}", font=font(24, "semibold"), fill=(156, 163, 175))
    size = 64
    while size >= 44:
        fh = font(size)
        lines = wrap(h.headline, fh, 900)
        if len(lines) <= 3:
            break
        size -= 4
    lines = lines[:3]
    y = 180
    for ln in lines:
        d.text((96, y), ln, font=fh, fill=(249, 250, 251))
        y += int(size * 1.25)
    fb = font(32, "regular")
    brief_lines = wrap(h.brief, fb, 900)
    if len(brief_lines) > 2:
        brief_lines = brief_lines[:2]
        while fb.getlength(brief_lines[1] + "…") > 900 and " " in brief_lines[1]:
            brief_lines[1] = brief_lines[1].rsplit(" ", 1)[0]
        brief_lines[1] += "…"
    for ln in brief_lines:
        d.text((96, y + 20), ln, font=fb, fill=(203, 213, 225))
        y += 44
    d.text((96, 590), f"Nguồn: {source}", font=font(24, "semibold"), fill=(100, 116, 139))
    if synthetic:
        _watermark(img)
    img.save(out)
    return out


def _watermark(img: Image.Image) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(46)
    text = config.SYNTHETIC_WATERMARK
    w = f.getlength(text)
    d.text(((img.width - w) / 2, img.height / 2 - 30), text, font=f, fill=(245, 158, 11, 90))
    layer = layer.rotate(14, center=(img.width / 2, img.height / 2))
    img.paste(layer, (0, 0), layer)


def watermark_file(path: Path) -> None:
    img = Image.open(path).convert("RGB")
    _watermark(img)
    img.save(path)


def make_ticker_strip(text: str, out: Path) -> int:
    """Trả về S = độ rộng một đoạn; dải lặp ceil(1080/S)+1 lần."""
    f = font(34, "semibold")
    seg = nfc(text) + "  •  "
    S = math.ceil(f.getlength(seg))
    n = math.ceil(L.W / S) + 1
    img = Image.new("RGB", (S * n, L.ticker.h), (17, 24, 39))
    d = ImageDraw.Draw(img)
    for i in range(n):
        d.text((i * S, 10), seg, font=f, fill=(229, 231, 235))
    img.save(out)
    return S


def _badge(d: ImageDraw.ImageDraw, x: int, y: int, h: int, text: str, f: ImageFont.FreeTypeFont) -> None:
    tw = int(f.getlength(text))
    d.rounded_rectangle([x, y, x + tw + 90, y + h], radius=h // 2, fill=(15, 23, 42, 225))
    d.rounded_rectangle([x + 6, y + 6, x + 58, y + h - 6], radius=(h - 12) // 2, fill=(139, 92, 246, 255))
    d.text((x + 17, y + 7), "AI", font=f, fill=(255, 255, 255, 255))
    d.text((x + 70, y + 7), text, font=f, fill=(229, 231, 235, 255))


def make_ai_label(out: Path) -> Path:
    """Nhãn AI cố định suốt video (trong Z3) — ảnh trong suốt 1080×1920."""
    img = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 0))
    _badge(ImageDraw.Draw(img), L.ai_label.x, L.ai_label.y, L.ai_label.h, "Nội dung có sử dụng AI", font(24))
    img.save(out)
    return out


def make_ai_intro(out: Path) -> Path:
    img = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    b = L.ai_intro
    d.rounded_rectangle([b.x, b.y, b.x2, b.y2], radius=18, fill=(76, 29, 149, 235))
    f = font(34)
    t = "Video có sử dụng AI: MC ảo & giọng đọc tổng hợp"
    d.text((b.x + (b.w - f.getlength(t)) / 2, b.y + 22), t, font=f, fill=(255, 255, 255, 255))
    img.save(out)
    return out


def make_disclaimer(out: Path) -> Path:
    img = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    b = L.disclaimer
    d.rounded_rectangle([b.x, b.y, b.x2, b.y2], radius=14, fill=(0, 0, 0, 215))
    f = font(28, "semibold")
    d.text((b.x + (b.w - f.getlength(config.DISCLAIMER)) / 2, b.y + 17), config.DISCLAIMER, font=f, fill=(253, 230, 138, 255))
    img.save(out)
    return out


def make_safe_zone_overlay(out: Path) -> Path:
    img = Image.new("RGBA", (L.W, L.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for z in L.unsafe_zones:
        d.rectangle([z.x, z.y, z.x2 - 1, z.y2 - 1], fill=(244, 63, 94, 90))
    d.text((40, 1470), "Vùng bị UI nền tảng che", font=font(30), fill=(255, 255, 255, 230))
    img.save(out)
    return out


def make_placeholder_portrait(out: Path) -> Path:
    """Ảnh chân dung mẫu vẽ bằng Pillow (is_placeholder=1)."""
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), (30, 41, 59))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(30 - 19 * t), int(41 - 24 * t), int(59 - 27 * t)))
    for i in range(9):
        d.rectangle([60 + i * 115, 200 + (i % 3) * 40, 130 + i * 115, 760], fill=(15, 23, 42))
    d.ellipse([180, 900, 900, 1600], fill=(51, 65, 85))
    d.polygon([(470, 905), (540, 1060), (610, 905)], fill=(29, 78, 216))
    d.rectangle([495, 730, 585, 910], fill=(226, 180, 143))
    d.ellipse([385, 300, 695, 760], fill=(226, 180, 143))
    d.chord([370, 250, 710, 560], 180, 360, fill=(31, 41, 55))
    d.ellipse([470, 490, 500, 520], fill=(17, 24, 39))
    d.ellipse([580, 490, 610, 520], fill=(17, 24, 39))
    d.arc([490, 560, 590, 650], 20, 160, fill=(154, 52, 18), width=8)
    f = font(34, "semibold")
    t = "ẢNH MẪU — hãy tải ảnh chân dung của bạn"
    d.text(((W - f.getlength(t)) / 2, 1240), t, font=f, fill=(226, 232, 240))
    img.save(out)
    return out


def crop_portrait(src: Path, out: Path, warn=None) -> Path:
    """Crop về 1080×976: có OpenCV → căn mặt; không → crop giữa lệch lên trên."""
    img = Image.open(src).convert("RGB")
    if img.width < 720 and warn:
        warn(f"Ảnh chân dung chỉ rộng {img.width}px (< 720px) — chất lượng có thể kém")
    target = L.avatar.w / L.avatar.h
    cx, cy = img.width / 2, img.height * 0.38
    try:
        import cv2
        import numpy as np

        gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        faces = casc.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        if len(faces):
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            cx, cy = x + w / 2, y + h * 0.4
    except ImportError:
        pass
    if img.width / img.height > target:
        ch = img.height
        cw = ch * target
    else:
        cw = img.width
        ch = cw / target
    left = min(max(cx - cw / 2, 0), img.width - cw)
    top = min(max(cy - ch * 0.18, 0), img.height - ch)  # mắt ở ~18% chiều cao vùng
    img.crop((int(left), int(top), int(left + cw), int(top + ch))).resize((L.avatar.w, L.avatar.h), Image.LANCZOS).save(out)
    return out
