"""HybridAvatarProvider — khớp môi đoạn đầu + đoạn cuối (provider trả phí), đoạn giữa DemoMotion (miễn phí).

Tiết kiệm ~80% chi phí: chỉ ~15 giây được gửi cho provider khớp môi.
Luồng: cắt voice.mp3 → head/mid/tail → render từng đoạn trong thư mục con → nối (concat filter) → avatar.mp4.
"""

import shutil
from pathlib import Path

from stockai.models import AvatarResult, ProgressCb
from stockai.providers.avatar.demo_motion import DemoMotionProvider, normalize_video
from stockai.render import ffmpeg

HEAD_S, TAIL_S = 7.0, 8.0


def split_plan(duration: float, head: float = HEAD_S, tail: float = TAIL_S) -> list[tuple[str, float, float]]:
    """Trả [(tên, bắt đầu, độ dài)]. Audio ngắn (< head+tail+3s) → khớp môi toàn bộ."""
    if duration < head + tail + 3:
        return [("full", 0.0, duration)]
    return [("head", 0.0, head), ("mid", head, duration - head - tail), ("tail", duration - tail, tail)]


class HybridAvatarProvider:
    name = "Hybrid"
    has_lipsync = True

    def __init__(self, lipsync, filler=None):
        self.lipsync, self.filler = lipsync, filler or DemoMotionProvider()
        self.name = f"Hybrid({getattr(lipsync, 'name', 'lipsync')})"

    def estimate_cost_usd(self, duration_s: float) -> float:
        lip = sum(d for n, _, d in split_plan(duration_s) if n != "mid")
        return self.lipsync.estimate_cost_usd(lip)

    async def render(self, portrait: Path, audio: Path, size: tuple[int, int], out_dir: Path,
                     on_progress: ProgressCb) -> AvatarResult:
        dur = await ffmpeg.probe_duration(audio)
        plan = split_plan(dur)
        parts: list[str] = []
        cost = 0.0
        for i, (seg, start, length) in enumerate(plan):
            sub = out_dir / f"hyb_{seg}"
            sub.mkdir(exist_ok=True)
            shutil.copy(portrait, sub / portrait.name)
            await ffmpeg.run(["-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", f"../{audio.name}",
                              "-c:a", "libmp3lame", "-q:a", "2", "seg.mp3"], cwd=sub, timeout=120)
            prov = self.filler if seg == "mid" else self.lipsync

            async def prog(f, msg, i=i, seg=seg):
                await on_progress((i + f) / (len(plan) + 1), f"Hybrid {seg}: {msg}")

            res = await prov.render(sub / portrait.name, sub / "seg.mp3", size, sub, prog)
            cost += res.cost_usd
            # chuẩn hóa từng đoạn về đúng 1080×976/30fps/độ dài đoạn audio
            norm = sub / "norm.mp4"
            await normalize_video(res.video_path, norm, size, await ffmpeg.probe_duration(sub / "seg.mp3"))
            parts.append(f"hyb_{seg}/norm.mp4")
        await on_progress(len(plan) / (len(plan) + 1), "Hybrid: nối các đoạn")
        n = len(parts)
        (out_dir / "hybrid_concat.txt").write_text(
            "".join(f"[{k}:v]" for k in range(n)) + f"concat=n={n}:v=1:a=0,format=yuv420p[v]", encoding="utf-8")
        args = [a for p in parts for a in ("-i", p)]
        await ffmpeg.run(args + ["-/filter_complex", "hybrid_concat.txt", "-map", "[v]", "-r", "30", "-c:v", "libx264",
                                 "-preset", "veryfast", "-crf", "20", "-t", f"{dur:.3f}", "avatar.mp4"],
                         cwd=out_dir, timeout=600)
        await on_progress(1.0, "Hybrid xong")
        return AvatarResult(video_path=out_dir / "avatar.mp4", provider=self.name, has_lipsync=True,
                            duration_s=dur, cost_usd=round(cost, 2))
