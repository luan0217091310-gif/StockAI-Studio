"""Bộ dựng caption theo từng nền tảng (Blueprint 9.8)."""

import html

from stockai import config

LIMITS = {"telegram_caption": 1024, "telegram_message": 4096, "facebook": 2200, "youtube_title": 100,
          "youtube_description": 5000, "tiktok": 2200}


def _tags(hashtags: list[str]) -> str:
    return " ".join(h if h.startswith("#") else f"#{h}" for h in hashtags)


def telegram_caption(title: str, post: str) -> str:
    bullets = [ln for ln in post.splitlines() if ln.strip().startswith(("•", "-", "▪"))][:3]
    body = "\n".join(html.escape(b) for b in bullets)
    cap = f"<b>{html.escape(title)}</b>\n{body}\nChi tiết ở tin nhắn bên dưới.\n{config.AI_DECLARATION}"
    return cap[: LIMITS["telegram_caption"]]


def split_message(text: str, limit: int = LIMITS["telegram_message"]) -> list[str]:
    out, cur = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            out.append(line[:limit])
            line = line[limit:]
        if len(cur) + len(line) > limit:
            out.append(cur)
            cur = ""
        cur += line
    if cur:
        out.append(cur)
    return out


def facebook_text(post: str, hashtags: list[str]) -> str:
    return f"{post}\n\n{_tags(hashtags)}"[: LIMITS["facebook"]]


def youtube_meta(title: str, post: str, hashtags: list[str]) -> dict:
    t = title.strip()
    suffix = " #Shorts"
    t = t[: LIMITS["youtube_title"] - len(suffix)] + suffix
    desc = f"{post}\n\n{_tags(hashtags)} #Shorts"[: LIMITS["youtube_description"]]
    return {"title": t, "description": desc, "tags": [h.lstrip("#") for h in hashtags]}


def tiktok_text(post: str, hashtags: list[str]) -> str:
    return f"{post}\n{_tags(hashtags)}"[: LIMITS["tiktok"]]


def build_all(title: str, post: str, hashtags: list[str]) -> dict:
    return {
        "telegram": {"caption": telegram_caption(title, post), "messages": split_message(html.escape(post))},
        "facebook": {"description": facebook_text(post, hashtags)},
        "youtube": youtube_meta(title, post, hashtags),
        "tiktok": {"title": tiktok_text(post, hashtags)},
    }
