"""YouTube Shorts: OAuth installed-app (loopback), token trong keyring, videos.insert resumable.

status.containsSyntheticMedia = true, selfDeclaredMadeForKids = false, mặc định private.
Cần gói tùy chọn: google-api-python-client, google-auth-oauthlib (uv add ...). [KIỂM CHỨNG] quota.
"""

import asyncio
import json
from pathlib import Path

from stockai import config, secrets
from stockai.errors import ConfigError
from stockai.models import PublishOptions, PublishResult
from stockai.text import captions

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _creds():
    try:
        from google.oauth2.credentials import Credentials
    except ImportError as e:
        raise ConfigError("Thiếu google-auth", hint="uv add google-api-python-client google-auth-oauthlib") from e
    raw = secrets.get_secret("youtube_oauth_token")
    if not raw:
        raise ConfigError("Chưa đăng nhập YouTube", code="YOUTUBE_LOGIN_REQUIRED", hint="Chạy: uv run stockai youtube-login client_secret.json")
    return Credentials.from_authorized_user_info(json.loads(raw), SCOPES)


def login(client_secret_file: str) -> str:
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    creds = flow.run_local_server(port=0)
    secrets.set_secret("youtube_oauth_token", creds.to_json())
    return "Đã lưu token YouTube vào keyring"


class YouTubePublisher:
    platform = "youtube"

    def __init__(self, hashtags: list[str] | None = None, category_id: str = "25"):
        self.hashtags, self.category_id = hashtags or [], category_id

    async def check_credentials(self) -> tuple[bool, str]:
        try:
            c = _creds()
        except ConfigError as e:
            return False, e.message
        if c.expired and not c.refresh_token:
            return False, "Cần đăng nhập lại (token hết hạn — app OAuth ở trạng thái Testing hết hạn sau ~7 ngày)"
        return True, "Đã có token YouTube"

    async def publish(self, job_id: str, video: Path, title: str, text: str, opts: PublishOptions) -> PublishResult:
        meta = captions.youtube_meta(title, text, self.hashtags)

        def _upload():
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload

            yt = build("youtube", "v3", credentials=_creds())
            body = {"snippet": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"],
                                "categoryId": self.category_id, "defaultLanguage": "vi"},
                    "status": {"privacyStatus": opts.privacy if opts.privacy in ("public", "unlisted", "private") else "private",
                               "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
            req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(video), resumable=True))
            resp = None
            while resp is None:
                _, resp = req.next_chunk()
            return resp

        resp = await asyncio.to_thread(_upload)
        vid = resp["id"]
        return PublishResult(platform="youtube", status="SUCCESS", privacy_level=opts.privacy, remote_post_id=vid,
                             remote_post_url=f"https://youtube.com/shorts/{vid}")


_ = config
