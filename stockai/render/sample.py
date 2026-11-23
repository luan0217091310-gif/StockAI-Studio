"""render-sample: video 8 giây, offline, để kiểm tra filtergraph trên máy (Blueprint 14 — Integration)."""

import tempfile
from datetime import date
from pathlib import Path

from stockai import config
from stockai.analysis.indicators import build_snapshot
from stockai.layout import LAYOUT
from stockai.models import NewsHighlight, Scenario, ScriptOutput, WordTiming
from stockai.providers.avatar.demo_motion import DemoMotionProvider
from stockai.providers.market.synthetic import SyntheticProvider
from stockai.providers.tts.edge import write_subs
from stockai.render import cards, ffmpeg
from stockai.render.chart import render_chart
from stockai.render.composer import compose


async def render_sample(d: date, out_dir: Path | None = None, seconds: float = 8.0) -> Path:
    job = out_dir or Path(tempfile.mkdtemp(prefix="stockai_sample_", dir=config.data_dir() / "temp"))
    job.mkdir(parents=True, exist_ok=True)
    snap = build_snapshot(await SyntheticProvider(d).fetch_daily("VNINDEX", 60), "Dữ liệu minh họa", "SYNTHETIC")
    render_chart(snap, job / "chart.png")
    text = "Xin chào quý vị, đây là bản tin mẫu tám giây để kiểm tra bộ dựng video của StockAI Studio."
    words, t = [], 200
    for w in text.split():
        words.append(WordTiming(text=w, start_ms=t, end_ms=t + 380))
        t += 420
    await write_subs(words, job)
    await ffmpeg.run(["-f", "lavfi", "-i", f"sine=frequency=220:duration={seconds}", "-af", "volume=0.05", "-c:a", "libmp3lame",
                      "voice.mp3"], cwd=job)
    cards.make_placeholder_portrait(job / "portrait.png")
    cards.crop_portrait(job / "portrait.png", job / "portrait_1080x976.png")

    async def noop(*_):
        return None

    await DemoMotionProvider().render(job / "portrait_1080x976.png", job / "voice.mp3", (LAYOUT.avatar.w, LAYOUT.avatar.h), job, noop)
    script = ScriptOutput(
        video_title="Bản tin mẫu 8 giây", market_sentiment="NEUTRAL",
        selected_news=[NewsHighlight(headline=f"Tin mẫu số {i + 1} kiểm tra thẻ tin", impact=imp, brief="Mô tả ngắn của tin mẫu.",
                                     source_index=0) for i, imp in enumerate(["TÍCH CỰC", "TIÊU CỰC", "TRUNG LẬP"])],
        scenarios=[Scenario(name="CƠ SỞ", description="-"), Scenario(name="THẬN TRỌNG", description="-")],
        social_post_text=f"{config.DISCLAIMER}\n{config.AI_DECLARATION}", video_script=text,
        ticker_text="VN-INDEX 1.285,40 (+0,97%) | Bản tin mẫu StockAI Studio")
    await compose(job, script, ["Mẫu"], "ADHOC", d, await ffmpeg.probe_duration(job / "voice.mp3"), True, noop, debug_safe_zone=True)
    return job / "final.mp4"
