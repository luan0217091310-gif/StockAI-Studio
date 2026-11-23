"""DryRunPublisher — ghi publish_preview.json, trạng thái DRY_RUN."""

import json
from pathlib import Path

from stockai.models import PublishOptions, PublishResult


class DryRunPublisher:
    def __init__(self, platform: str, payload: dict):
        self.platform, self.payload = platform, payload

    async def check_credentials(self) -> tuple[bool, str]:
        return True, "Dry-run không cần khóa"

    async def publish(self, job_id: str, video: Path, title: str, text: str, opts: PublishOptions) -> PublishResult:
        f = video.parent / "publish_preview.json"
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        data[self.platform] = {"platform": self.platform, "title": title, "privacy": opts.privacy, **self.payload}
        f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return PublishResult(platform=self.platform, status="DRY_RUN", privacy_level=opts.privacy)
