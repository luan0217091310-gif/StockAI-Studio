"""HeyGenProvider — Photo Avatar qua HeyGen API (PRODUCTION, M7).

[KIỂM CHỨNG] HeyGen API v3 `POST /v3/videos`, cách gửi audio có sẵn, trường trạng thái. Chưa kiểm chứng
do chưa có khóa. Giữ adapter tối thiểu; bật sau khi đối chiếu https://developers.heygen.com/photo-avatar.md
"""

from pathlib import Path

from stockai import secrets
from stockai.errors import ConfigError
from stockai.models import AvatarResult, ProgressCb


class HeyGenProvider:
    name = "HeyGen"
    has_lipsync = True
    PRICE_PER_SECOND = 0.10

    def estimate_cost_usd(self, duration_s: float) -> float:
        return round(self.PRICE_PER_SECOND * duration_s, 2)

    async def render(self, portrait: Path, audio: Path, size: tuple[int, int], out_dir: Path,
                     on_progress: ProgressCb) -> AvatarResult:
        if not secrets.get_secret("heygen_api_key"):
            raise ConfigError("Chưa có HeyGen API key")
        raise ConfigError("HeyGen adapter chưa kiểm chứng endpoint v3", code="NOT_VERIFIED",
                          hint="Xem docs/DECISIONS.md — cần đối chiếu tài liệu HeyGen trước khi bật (M7)")
