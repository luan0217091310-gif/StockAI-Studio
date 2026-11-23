"""ElevenLabsProvider (tùy chọn, M7). [KIỂM CHỨNG] model hỗ trợ tiếng Việt, endpoint with-timestamps."""

import base64
from pathlib import Path

import httpx

from stockai import secrets
from stockai.errors import ConfigError
from stockai.models import AudioResult, WordTiming
from stockai.providers.tts.edge import write_subs
from stockai.render import ffmpeg


def chars_to_words(chars: list[str], starts: list[float], ends: list[float]) -> list[WordTiming]:
    words, cur, s, prev_end = [], "", None, 0.0
    for ch, a, b in zip(chars, starts, ends, strict=True):
        if ch.isspace():
            if cur:
                words.append(WordTiming(text=cur, start_ms=int(s * 1000), end_ms=int(prev_end * 1000)))
            cur, s = "", None
            continue
        if s is None:
            s = a
        cur += ch
        prev_end = b
    if cur:
        words.append(WordTiming(text=cur, start_ms=int(s * 1000), end_ms=int(prev_end * 1000)))
    return words


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self, voice_id: str, model: str = "eleven_multilingual_v2"):
        self.key = secrets.get_secret("elevenlabs_api_key")
        if not self.key:
            raise ConfigError("Chưa có ElevenLabs API key")
        self.voice_id, self.model = voice_id, model

    async def synthesize(self, text: str, voice: str, rate: str, out_dir: Path, emit=None) -> AudioResult:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/with-timestamps",
                             headers={"xi-api-key": self.key}, json={"text": text, "model_id": self.model})
            r.raise_for_status()
            data = r.json()
        audio = out_dir / "voice.mp3"
        audio.write_bytes(base64.b64decode(data["audio_base64"]))
        al = data["alignment"]
        words = chars_to_words(al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])
        srt, ass = await write_subs(words, out_dir)
        return AudioResult(audio_path=audio, srt_path=srt, ass_path=ass, duration_s=await ffmpeg.probe_duration(audio), words=words)
