"""Hợp đồng dữ liệu & giao diện provider (Blueprint Mục 8). Giữ nguyên tên trường."""

from collections.abc import Awaitable, Callable
from datetime import date, datetime
from pathlib import Path
from typing import Literal, Protocol

from pydantic import BaseModel, Field, field_validator

DataQuality = Literal["LIVE", "CACHED", "SYNTHETIC"]
SessionType = Literal["PRE_MARKET", "POST_MARKET", "ADHOC"]


class OHLCVBar(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


class MarketSnapshot(BaseModel):
    symbol: str = "VNINDEX"
    session_date: date
    bars: list[OHLCVBar]
    close: float
    change: float
    change_pct: float
    volume: float | None = None
    value_bn_vnd: float | None = None
    foreign_net_bn_vnd: float | None = None
    sma20: float
    rsi14: float
    support20: float
    resistance20: float
    source: str
    data_quality: DataQuality


class NewsItem(BaseModel):
    id: int | None = None
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str = Field(default="", max_length=300)
    content_hash: str
    score: float = 0.0


class ScriptContext(BaseModel):
    run_date: date
    session_type: SessionType
    market: MarketSnapshot
    news: list[NewsItem]
    hook_style: str


class NewsHighlight(BaseModel):
    headline: str = Field(max_length=90)
    impact: Literal["TÍCH CỰC", "TIÊU CỰC", "TRUNG LẬP"]
    brief: str
    source_index: int

    @field_validator("headline")
    @classmethod
    def _max_12_words(cls, v: str) -> str:
        if len(v.split()) > 12:
            raise ValueError("headline tối đa 12 từ")
        return v


class Scenario(BaseModel):
    name: Literal["CƠ SỞ", "THẬN TRỌNG"]
    description: str


class ScriptOutput(BaseModel):
    video_title: str = Field(max_length=80)
    market_sentiment: Literal["BULLISH", "NEUTRAL", "BEARISH"]
    selected_news: list[NewsHighlight] = Field(min_length=3, max_length=4)
    scenarios: list[Scenario] = Field(min_length=2, max_length=2)
    social_post_text: str
    video_script: str
    ticker_text: str = Field(max_length=140)
    hashtags: list[str] = Field(default_factory=list, max_length=8)


class WordTiming(BaseModel):
    text: str
    start_ms: int
    end_ms: int


class AudioResult(BaseModel):
    audio_path: Path
    srt_path: Path
    ass_path: Path
    duration_s: float
    words: list[WordTiming]


class AvatarResult(BaseModel):
    video_path: Path
    provider: str
    has_lipsync: bool
    duration_s: float
    cost_usd: float = 0.0


class RenderResult(BaseModel):
    final_video_path: Path
    thumbnail_path: Path
    duration_s: float
    width: int
    height: int
    size_bytes: int


class PublishOptions(BaseModel):
    privacy: Literal["public", "unlisted", "private", "draft"] = "private"
    dry_run: bool = False


class PublishResult(BaseModel):
    platform: str
    status: Literal["SUCCESS", "FAILED", "DRY_RUN", "SKIPPED"]
    privacy_level: str | None = None
    remote_post_id: str | None = None
    remote_post_url: str | None = None
    error_message: str | None = None


ProgressCb = Callable[[float, str], Awaitable[None]]


class MarketDataProvider(Protocol):
    name: str

    async def fetch_daily(self, symbol: str, sessions: int = 60) -> list[OHLCVBar]: ...


class LLMProvider(Protocol):
    name: str

    async def generate(self, ctx: ScriptContext, feedback: str | None = None) -> ScriptOutput: ...


class TTSProvider(Protocol):
    name: str

    async def synthesize(self, text: str, voice: str, rate: str, out_dir: Path) -> AudioResult: ...


class AvatarProvider(Protocol):
    name: str
    has_lipsync: bool

    def estimate_cost_usd(self, duration_s: float) -> float: ...

    async def render(self, portrait: Path, audio: Path, size: tuple[int, int],
                     out_dir: Path, on_progress: ProgressCb) -> AvatarResult: ...


class Publisher(Protocol):
    platform: str

    async def check_credentials(self) -> tuple[bool, str]: ...

    async def publish(self, job_id: str, video: Path, title: str, text: str,
                      opts: PublishOptions) -> PublishResult: ...
