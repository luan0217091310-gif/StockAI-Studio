"""edge-tts provider (Blueprint 9.5). PHẢI truyền boundary="WordBoundary" (edge-tts >= 7)."""

import re
from pathlib import Path

from stockai.errors import ProviderError
from stockai.models import AudioResult, WordTiming
from stockai.render import ffmpeg
from stockai.render.subtitles import build_cues, distribute_sentence, to_ass, to_srt


def align_to_script(words: list[WordTiming], display_text: str) -> list[WordTiming]:
    """Giữ thời gian TTS nhưng hiển thị từ theo kịch bản gốc khi số từ khớp (để phụ đề có dấu câu/số đẹp)."""
    disp = display_text.split()
    if len(disp) == len(words):
        return [WordTiming(text=d, start_ms=w.start_ms, end_ms=w.end_ms) for d, w in zip(disp, words, strict=True)]
    return words


async def write_subs(words: list[WordTiming], out_dir: Path) -> tuple[Path, Path]:
    cues = build_cues(words)
    srt, ass = out_dir / "subs.srt", out_dir / "subs.ass"
    srt.write_text(to_srt(cues), encoding="utf-8")
    ass.write_text(to_ass(cues), encoding="utf-8-sig")
    return srt, ass


class EdgeTTSProvider:
    name = "edge-tts"

    async def synthesize(self, text: str, voice: str, rate: str, out_dir: Path, emit=None) -> AudioResult:
        import edge_tts

        import asyncio

        audio = out_dir / "voice.mp3"
        last: Exception | None = None
        for attempt in range(1, 6):  # dịch vụ đôi khi trả NoAudioReceived ngẫu nhiên → thử lại
            words: list[WordTiming] = []
            sentences: list[tuple[str, int, int]] = []
            try:
                comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
                with audio.open("wb") as f:
                    async for chunk in comm.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            s = chunk["offset"] // 10_000
                            words.append(WordTiming(text=chunk["text"], start_ms=s, end_ms=(chunk["offset"] + chunk["duration"]) // 10_000))
                        elif chunk["type"] == "SentenceBoundary":
                            s = chunk["offset"] // 10_000
                            sentences.append((chunk["text"], s, (chunk["offset"] + chunk["duration"]) // 10_000))
                last = None
                break
            except Exception as e:
                last = e
                if emit:
                    emit("WARN", f"edge-tts lần {attempt}: {type(e).__name__} — thử lại")
                await asyncio.sleep(1.5 * attempt)
        if last:
            raise ProviderError(f"edge-tts lỗi: {type(last).__name__}: {last}", code="TTS_FAILED",
                                hint="Cập nhật edge-tts (uv lock --upgrade-package edge-tts) hoặc chọn TTS khác trong Cài đặt") from last
        if not words and sentences:
            if emit:
                emit("WARN", "Không nhận được WordBoundary — chia thời gian câu theo số ký tự")
            for t, s, e in sentences:
                words += distribute_sentence(t, s, e)
        if not words:
            raise ProviderError("edge-tts không trả về mốc thời gian", code="TTS_NO_TIMING")
        duration = await ffmpeg.probe_duration(audio)
        srt, ass = await write_subs(words, out_dir)
        return AudioResult(audio_path=audio, srt_path=srt, ass_path=ass, duration_s=duration, words=words)


class OfflineTTSProvider:
    """Dùng khi --offline: audio im lặng + mốc thời gian ước lượng (không cần mạng). Ghi WARN."""

    name = "offline-estimate"

    async def synthesize(self, text: str, voice: str, rate: str, out_dir: Path, emit=None) -> AudioResult:
        pct = int(re.sub(r"[^\d-]", "", rate) or 0)
        k = 1 / (1 + pct / 100)
        words, t = [], 300.0
        for w in text.split():
            d = (170 + len(w) * 38) * k
            words.append(WordTiming(text=w, start_ms=int(t), end_ms=int(t + d)))
            t += d + ((380 if w[-1] in ".?!" else 180 if w[-1] in ",;:" else 40) * k)
        dur = (t + 600) / 1000
        audio = out_dir / "voice.mp3"
        await ffmpeg.run(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{dur:.2f}", "-c:a", "libmp3lame",
                          "-b:a", "64k", audio.name], cwd=out_dir)
        srt, ass = await write_subs(words, out_dir)
        return AudioResult(audio_path=audio, srt_path=srt, ass_path=ass, duration_s=round(dur, 2), words=words)
