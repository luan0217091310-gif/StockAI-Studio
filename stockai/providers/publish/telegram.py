"""Telegram Bot API: sendVideo (≤50MB, caption ≤1024) + sendMessage bài đầy đủ (≤4096/tin, HTML)."""

import json
from pathlib import Path

import httpx

from stockai import secrets
from stockai.errors import ConfigError
from stockai.models import PublishOptions, PublishResult
from stockai.providers.publish.base import raise_for
from stockai.text import captions


class TelegramPublisher:
    platform = "telegram"

    def __init__(self, chat_id: str | None, token: str | None = None, hashtags: list[str] | None = None,
                 duration: float = 0, thumb: Path | None = None):
        self.token = token or secrets.get_secret("telegram_bot_token")
        self.chat_id, self.hashtags, self.duration, self.thumb = chat_id, hashtags or [], duration, thumb

    @property
    def api(self) -> str:
        return f"https://api.telegram.org/bot{self.token}"

    async def check_credentials(self) -> tuple[bool, str]:
        if not self.token:
            return False, "Chưa có Bot Token"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{self.api}/getMe")
        if r.status_code != 200:
            return False, f"Token không hợp lệ (HTTP {r.status_code})"
        bot = r.json()["result"]["username"]
        if not self.chat_id:
            return False, f"Bot @{bot} hợp lệ nhưng chưa có Chat ID"
        return True, f"Bot @{bot} hợp lệ, chat {self.chat_id}"

    async def publish(self, job_id: str, video: Path, title: str, text: str, opts: PublishOptions) -> PublishResult:
        if not self.token or not self.chat_id:
            raise ConfigError("Thiếu Telegram Bot Token hoặc Chat ID", hint="Cài đặt → Mạng xã hội → Telegram")
        if video.stat().st_size > 50 * 1024 * 1024:
            return PublishResult(platform="telegram", status="FAILED", error_message="Video > 50 MB")
        cap = captions.telegram_caption(title, text)
        async with httpx.AsyncClient(timeout=300) as c:
            files = {"video": (video.name, video.open("rb"), "video/mp4")}
            if self.thumb and self.thumb.exists():
                files["thumbnail"] = (self.thumb.name, self.thumb.open("rb"), "image/jpeg")
            r = await c.post(f"{self.api}/sendVideo", files=files,
                             data={"chat_id": self.chat_id, "caption": cap, "parse_mode": "HTML", "supports_streaming": "true",
                                   "width": "1080", "height": "1920", "duration": str(int(self.duration))})
            raise_for(r)
            msg = r.json()["result"]
            full = text + ("\n\n" + " ".join(self.hashtags) if self.hashtags else "")
            for part in captions.split_message(captions.html.escape(full)):
                r2 = await c.post(f"{self.api}/sendMessage", data={"chat_id": self.chat_id, "text": part, "parse_mode": "HTML"})
                raise_for(r2)
        return PublishResult(platform="telegram", status="SUCCESS", privacy_level="channel",
                             remote_post_id=str(msg["message_id"]), remote_post_url=None,
                             error_message=None) if msg else PublishResult(platform="telegram", status="FAILED",
                                                                           error_message=json.dumps(r.json())[:300])
