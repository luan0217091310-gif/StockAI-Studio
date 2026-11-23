"""DemoMotionProvider — ảnh thật + chuyển động "nhịp thở" nhẹ (không khớp môi). Sóng âm thêm ở bước dựng."""

from pathlib import Path

from stockai.models import AvatarResult, ProgressCb
from stockai.render import ffmpeg

UPSCALE = 2160  # Blueprint gợi ý ×4 (4320); dùng ×2 để nhanh hơn ~3 lần, vẫn mượt (ghi trong DECISIONS)


class DemoMotionProvider:
    name = "DemoMotion"
    has_lipsync = False

    def estimate_cost_usd(self, duration_s: float) -> float:
        return 0.0

    async def render(self, portrait: Path, audio: Path, size: tuple[int, int], out_dir: Path,
                     on_progress: ProgressCb) -> AvatarResult:
        w, h = size
        dur = await ffmpeg.probe_duration(audio)
        await on_progress(0.1, "DemoMotion: dựng chuyển động nhịp thở 6 giây")
        vf = (f"scale={UPSCALE}:-1,zoompan=z='1.03+0.03*sin(2*PI*on/180)':x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps=30,format=yuv420p")
        await ffmpeg.run(["-loop", "1", "-framerate", "30", "-i", portrait.name, "-t", f"{dur:.3f}", "-vf", vf,
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-r", "30", "avatar.mp4"],
                         cwd=out_dir, timeout=600)
        await on_progress(1.0, "DemoMotion xong")
        return AvatarResult(video_path=out_dir / "avatar.mp4", provider=self.name, has_lipsync=False, duration_s=dur)


async def normalize_video(src: Path, dst: Path, size: tuple[int, int], audio_duration: float) -> Path:
    """R-AV-2: 1080×976, 30fps, yuv420p, độ dài khớp audio ±0,1s (ngắn → tpad clone; dài → cắt)."""
    w, h = size
    vdur = await ffmpeg.probe_duration(src)
    pad = max(0.0, audio_duration - vdur)
    vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps=30,format=yuv420p"
    if pad > 0.05:
        vf += f",tpad=stop_mode=clone:stop_duration={pad:.3f}"
    await ffmpeg.run(["-i", src.name, "-t", f"{audio_duration:.3f}", "-an", "-vf", vf, "-c:v", "libx264", "-preset",
                      "veryfast", "-crf", "20", dst.name], cwd=dst.parent, timeout=600)
    return dst
