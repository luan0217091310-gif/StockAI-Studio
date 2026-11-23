"""Dựng video 2 giai đoạn (Blueprint 9.7). cwd = thư mục job, đường dẫn tương đối."""

import shutil
from collections.abc import Awaitable, Callable
from datetime import date
from pathlib import Path

from stockai import config
from stockai.errors import ValidationError
from stockai.layout import LAYOUT as L
from stockai.models import RenderResult, ScriptOutput
from stockai.render import cards, ffmpeg

XF = 0.4
SEG_TARGET = 7.0

Progress = Callable[[float, str], Awaitable[None]]


def broll_sequence(n_cards: int, duration: float) -> tuple[list[str], float]:
    """chart → card1..n → chart …, mỗi đoạn 6–8 giây, tổng (sau xfade) = duration."""
    cycle = ["chart.png"] + [f"news_card_{i + 1}.png" for i in range(n_cards)]
    n = max(2, round((duration - XF) / (SEG_TARGET - XF)))
    seq = [cycle[i % len(cycle)] for i in range(n - 1)] + ["chart.png"]
    seg = (duration + XF * (len(seq) - 1)) / len(seq)
    return seq, seg


async def build_broll(job_dir: Path, seq: list[str], seg: float) -> Path:
    args: list[str] = []
    for f in seq:
        args += ["-loop", "1", "-framerate", "30", "-t", f"{seg:.3f}", "-i", f]
    frames = int(seg * 30)
    parts = []
    for i, f in enumerate(seq):
        if f == "chart.png":  # zoom nhẹ 1.00 → 1.04
            parts.append(f"[{i}:v]scale=2160:-1,zoompan=z='1+0.04*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                         f":d=1:s=1080x660:fps=30,format=yuv420p,settb=AVTB[s{i}]")
        else:
            parts.append(f"[{i}:v]scale=1080:660,fps=30,format=yuv420p,settb=AVTB[s{i}]")
    last = "s0"
    for i in range(1, len(seq)):
        off = i * (seg - XF)
        parts.append(f"[{last}][s{i}]xfade=transition=fade:duration={XF}:offset={off:.3f}[x{i}]")
        last = f"x{i}"
    (job_dir / "broll_graph.txt").write_text(";\n".join(parts), encoding="utf-8")
    await ffmpeg.run(args + ["-/filter_complex", "broll_graph.txt", "-map", f"[{last}]", "-r", "30", "-c:v", "libx264",
                             "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "broll.mp4"], cwd=job_dir, timeout=600)
    return job_dir / "broll.mp4"


def final_graph(S: int, D: float, has_bgm: bool, bgm_db: float) -> str:
    g = [
        "[0:v][1:v]overlay=0:%d[v1]" % L.broll.y,
        "[v1][8:v]overlay=0:0[v1b]",
        "[v1b][2:v]overlay=0:%d[v2]" % L.avatar.y,
        f"[v2][3:v]overlay=x='-mod(t*{L.ticker_speed},{S})':y={L.ticker.y}[v3]",
        "[4:a]asplit=2[a_voice][a_wave]",
        f"[a_wave]showwaves=s={L.wave.w}x{L.wave.h}:mode=cline:colors=0x10B981:rate=30,format=rgba,colorchannelmixer=aa=0.8[wave]",
        f"[v3][wave]overlay={L.wave.x}:{L.wave.y}[v4]",
        "[v4]ass=subs.ass:fontsdir=fonts[v5]",
        "[v5][7:v]overlay=0:0:enable='lt(t,3)'[v6]",
        f"[v6][6:v]overlay=0:0:enable='gte(t,{max(0.0, D - 4):.3f})'[vout]",
    ]
    if has_bgm:
        g += [f"[5:a]volume={bgm_db}dB[a_bgm]",
              "[a_voice][a_bgm]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-14:TP=-1.5:LRA=11[aout]"]
    else:
        g += ["[a_voice]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"]
    return ";\n".join(g)


async def compose(job_dir: Path, script: ScriptOutput, news_sources: list[str], session_type: str, run_date: date,
                  duration: float, synthetic: bool, progress: Progress, bgm: Path | None = None, logo: Path | None = None,
                  bgm_db: float = -22, debug_safe_zone: bool = False) -> RenderResult:
    D = duration
    # ---------- Giai đoạn A ----------
    await progress(0.05, "Giai đoạn A: base.png, thẻ tin, ticker, nhãn AI, miễn trừ")
    cards.make_base(job_dir / "base.png", session_type, run_date, logo)
    for i, h in enumerate(script.selected_news):
        src = news_sources[h.source_index] if h.source_index < len(news_sources) else ""
        cards.make_news_card(h, src, job_dir / f"news_card_{i + 1}.png", i, synthetic)
    S = cards.make_ticker_strip(script.ticker_text, job_dir / "ticker_strip.png")
    cards.make_ai_label(job_dir / "ai_label.png")
    cards.make_ai_intro(job_dir / "ai_intro.png")
    cards.make_disclaimer(job_dir / "disclaimer.png")
    fonts = job_dir / "fonts"
    fonts.mkdir(exist_ok=True)
    for f in config.FONTS_DIR.glob("*.ttf"):
        shutil.copy2(f, fonts / f.name)
    seq, seg = broll_sequence(len(script.selected_news), D)
    await progress(0.2, f"B-roll: {len(seq)} đoạn × {seg:.1f}s, xfade {XF}s")
    await build_broll(job_dir, seq, seg)
    # ---------- Giai đoạn B ----------
    await progress(0.55, "Giai đoạn B: ghép cuối (filter_complex từ file)")
    has_bgm = bool(bgm and bgm.exists())
    if has_bgm:
        shutil.copy2(bgm, job_dir / "bgm.mp3")
    inputs = ["-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", "base.png",
              "-i", "broll.mp4", "-i", "avatar.mp4",
              "-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", "ticker_strip.png",
              "-i", "voice.mp3"]
    inputs += (["-stream_loop", "-1", "-i", "bgm.mp3"] if has_bgm else ["-f", "lavfi", "-t", "1", "-i", "anullsrc"])
    for f in ("disclaimer.png", "ai_intro.png", "ai_label.png"):
        inputs += ["-loop", "1", "-framerate", "30", "-t", f"{D:.3f}", "-i", f]
    (job_dir / "final_graph.txt").write_text(final_graph(S, D, has_bgm, bgm_db), encoding="utf-8")
    title = script.video_title.replace('"', "'")
    await ffmpeg.run(inputs + ["-/filter_complex", "final_graph.txt", "-map", "[vout]", "-map", "[aout]", "-t", f"{D:.3f}",
                               "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-maxrate", "3500k",
                               "-bufsize", "7000k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                               "-movflags", "+faststart", "-metadata", f"title={title}",
                               "-metadata", f"comment={config.AI_METADATA}", "final.mp4"], cwd=job_dir, timeout=600)
    await progress(0.9, "Kiểm tra ffprobe + tạo thumbnail")
    res = await verify(job_dir / "final.mp4", D)
    await ffmpeg.run(["-ss", "1", "-i", "final.mp4", "-frames:v", "1", "-q:v", "3", "thumbnail.jpg"], cwd=job_dir)
    if debug_safe_zone:
        await safe_zone_check(job_dir)
    return RenderResult(final_video_path=job_dir / "final.mp4", thumbnail_path=job_dir / "thumbnail.jpg", **res)


async def verify(path: Path, D: float) -> dict:
    info = await ffmpeg.probe(path)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    size = path.stat().st_size
    errs = []
    if not v or (v["width"], v["height"]) != (1080, 1920):
        errs.append(f"kích thước sai: {v and (v['width'], v['height'])}")
    if v:
        num, den = (int(x) for x in v["r_frame_rate"].split("/"))
        if abs(num / den - 30) > 0.01:
            errs.append(f"fps sai: {v['r_frame_rate']}")
    if not a:
        errs.append("không có luồng audio")
    if abs(dur - D) > 0.5:
        errs.append(f"độ dài {dur:.2f}s lệch so với {D:.2f}s")
    if size >= 48 * 1024 * 1024:
        errs.append(f"dung lượng {size / 1e6:.1f} MB ≥ 48 MB")
    if errs:
        raise ValidationError("Video không đạt kiểm tra: " + "; ".join(errs), code="RENDER_INVALID")
    return {"duration_s": round(dur, 2), "width": 1080, "height": 1920, "size_bytes": size}


async def safe_zone_check(job_dir: Path) -> Path:
    cards.make_safe_zone_overlay(job_dir / "safe_zone.png")
    await ffmpeg.run(["-ss", "5", "-i", "final.mp4", "-i", "safe_zone.png", "-filter_complex", "[0:v][1:v]overlay=0:0",
                      "-frames:v", "1", "safe_zone_check.png"], cwd=job_dir)
    return job_dir / "safe_zone_check.png"
