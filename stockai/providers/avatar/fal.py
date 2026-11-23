"""FalAvatarProvider — talking-head khớp môi qua fal.ai queue (PRODUCTION, M7).

[KIỂM CHỨNG] tên model, tham số đầu vào (image_url, audio_url), giá trước khi bật.
Luồng: upload ảnh + audio lên storage của fal → submit queue → poll 5s (timeout 10 phút) → tải MP4 → chuẩn hóa.
"""

import asyncio
from pathlib import Path

import httpx

from stockai import secrets
from stockai.errors import ConfigError, ProviderError
from stockai.models import AvatarResult, ProgressCb
from stockai.providers.avatar.demo_motion import normalize_video
from stockai.render import ffmpeg

PRICE_PER_SECOND = {
    "fal-ai/kling-video/ai-avatar/v2/standard": 0.0562,
    "fal-ai/kling-video/ai-avatar/v2/pro": 0.115,
    "fal-ai/bytedance/omnihuman": 0.14,
}


class FalAvatarProvider:
    name = "fal.ai"
    has_lipsync = True

    def __init__(self, model: str):
        self.model = model
        self.key = secrets.get_secret("fal_key")

    def estimate_cost_usd(self, duration_s: float) -> float:
        return round(PRICE_PER_SECOND.get(self.model, 0.12) * duration_s, 2)

    async def render(self, portrait: Path, audio: Path, size: tuple[int, int], out_dir: Path,
                     on_progress: ProgressCb) -> AvatarResult:
        if not self.key:
            raise ConfigError("Chưa có fal.ai key", hint="Cài đặt → Avatar & Giọng → fal.ai")
        try:
            import fal_client
        except ImportError as e:
            raise ConfigError("Thiếu gói fal-client", hint="uv add fal-client") from e
        import os

        os.environ["FAL_KEY"] = self.key
        await on_progress(0.05, "Tải ảnh + audio lên fal storage")
        img_url = await asyncio.to_thread(fal_client.upload_file, str(portrait))
        aud_url = await asyncio.to_thread(fal_client.upload_file, str(audio))
        handle = await asyncio.to_thread(fal_client.submit, self.model, {"image_url": img_url, "audio_url": aud_url})
        for i in range(120):  # 10 phút
            st = await asyncio.to_thread(handle.status)
            await on_progress(min(0.9, 0.1 + i / 120), f"fal: {type(st).__name__}")
            if type(st).__name__ == "Completed":
                break
            await asyncio.sleep(5)
        else:
            raise ProviderError("fal.ai quá 10 phút", code="AVATAR_TIMEOUT")
        res = await asyncio.to_thread(handle.get)
        url = res["video"]["url"]
        raw = out_dir / "avatar_raw.mp4"
        async with httpx.AsyncClient(timeout=120) as c:
            raw.write_bytes((await c.get(url)).content)
        dur = await ffmpeg.probe_duration(audio)
        out = await normalize_video(raw, out_dir / "avatar.mp4", size, dur)
        return AvatarResult(video_path=out, provider=f"fal:{self.model}", has_lipsync=True, duration_s=dur,
                            cost_usd=self.estimate_cost_usd(dur))
