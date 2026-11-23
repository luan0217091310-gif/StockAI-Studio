"""TikTok Content Posting API — mặc định gửi NHÁP vào hộp thư (inbox upload), is_aigc = true.

App chưa audit: chỉ đăng riêng tư. Luôn cần người dùng duyệt (R-PUB, 9.8).
[KIỂM CHỨNG] endpoint creator_info / inbox video init theo developers.tiktok.com.
"""

from pathlib import Path

import httpx

from stockai import secrets
from stockai.errors import ConfigError
from stockai.models import PublishOptions, PublishResult
from stockai.providers.publish.base import raise_for

API = "https://open.tiktokapis.com/v2"


class TikTokPublisher:
    platform = "tiktok"

    def __init__(self, direct_post: bool = False, privacy_level: str = "SELF_ONLY"):
        self.token = secrets.get_secret("tiktok_access_token")
        self.direct, self.privacy = direct_post, privacy_level

    def _h(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json; charset=UTF-8"}

    async def creator_info(self) -> dict:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(f"{API}/post/publish/creator_info/query/", headers=self._h())
            raise_for(r)
            return r.json()["data"]

    async def check_credentials(self) -> tuple[bool, str]:
        if not self.token:
            return False, "Chưa có access token"
        try:
            info = await self.creator_info()
            return True, f"@{info.get('creator_username')} · quyền riêng tư cho phép: {info.get('privacy_level_options')}"
        except Exception as e:
            return False, str(e)[:200]

    async def publish(self, job_id: str, video: Path, title: str, text: str, opts: PublishOptions) -> PublishResult:
        if not self.token:
            raise ConfigError("Chưa có TikTok access token")
        size = video.stat().st_size
        source = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": size, "total_chunk_count": 1}
        async with httpx.AsyncClient(timeout=300) as c:
            if self.direct:
                info = await self.creator_info()
                priv = self.privacy if self.privacy in info.get("privacy_level_options", []) else "SELF_ONLY"
                body = {"post_info": {"title": text[:2200], "privacy_level": priv, "is_aigc": True}, "source_info": source}
                r = await c.post(f"{API}/post/publish/video/init/", headers=self._h(), json=body)
            else:
                r = await c.post(f"{API}/post/publish/inbox/video/init/", headers=self._h(), json={"source_info": source})
                priv = "DRAFT_INBOX"
            raise_for(r)
            data = r.json()["data"]
            up = await c.put(data["upload_url"], content=video.read_bytes(),
                             headers={"Content-Type": "video/mp4", "Content-Range": f"bytes 0-{size - 1}/{size}"})
            raise_for(up)
        return PublishResult(platform="tiktok", status="SUCCESS", privacy_level=priv, remote_post_id=data.get("publish_id"))
