"""Facebook Reels Publishing API: start → upload rupload.facebook.com → finish (PUBLISHED). Giới hạn 30/24h.

[KIỂM CHỨNG] phiên bản Graph API (settings facebook.graph_version, mặc định v25.0).
"""

from pathlib import Path

import httpx

from stockai import secrets
from stockai.errors import ConfigError
from stockai.models import PublishOptions, PublishResult
from stockai.providers.publish.base import raise_for


class FacebookPublisher:
    platform = "facebook"

    def __init__(self, page_id: str | None, version: str = "v25.0", recent_count: int = 0):
        self.page_id, self.version, self.recent = page_id, version, recent_count
        self.token = secrets.get_secret("facebook_page_token")

    async def check_credentials(self) -> tuple[bool, str]:
        if not self.token or not self.page_id:
            return False, "Thiếu Page ID hoặc Page Token"
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"https://graph.facebook.com/{self.version}/{self.page_id}", params={"access_token": self.token, "fields": "name"})
        return (r.status_code == 200, r.json().get("name", r.text[:150]) if r.status_code == 200 else f"HTTP {r.status_code}")

    async def publish(self, job_id: str, video: Path, title: str, text: str, opts: PublishOptions) -> PublishResult:
        if not self.token or not self.page_id:
            raise ConfigError("Thiếu Facebook Page ID/Token")
        if self.recent >= 30:
            return PublishResult(platform="facebook", status="SKIPPED", error_message="Đã đạt 30 Reels/24h")
        base = f"https://graph.facebook.com/{self.version}/{self.page_id}/video_reels"
        async with httpx.AsyncClient(timeout=300) as c:
            r = await c.post(base, data={"upload_phase": "start", "access_token": self.token})
            raise_for(r)
            vid = r.json()["video_id"]
            data = video.read_bytes()
            r = await c.post(f"https://rupload.facebook.com/video-upload/{self.version}/{vid}", content=data,
                             headers={"Authorization": f"OAuth {self.token}", "offset": "0", "file_size": str(len(data))})
            raise_for(r)
            r = await c.post(base, data={"upload_phase": "finish", "video_id": vid, "video_state": "PUBLISHED",
                                         "description": text, "title": title, "access_token": self.token})
            raise_for(r)
        return PublishResult(platform="facebook", status="SUCCESS", privacy_level="published", remote_post_id=vid,
                             remote_post_url=f"https://www.facebook.com/reel/{vid}")
