"""Cấu hình, đường dẫn, hằng số."""

import os
from pathlib import Path

from platformdirs import user_data_dir

APP_NAME = "StockAI Studio"
APP_AUTHOR = "StockAI"
TZ = "Asia/Ho_Chi_Minh"
USER_AGENT = "StockAI-Studio/3.0"

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "assets" / "fonts"
UI_DIR = ROOT / "ui"
FONT_REGULAR = FONTS_DIR / "BeVietnamPro-Regular.ttf"
FONT_SEMIBOLD = FONTS_DIR / "BeVietnamPro-SemiBold.ttf"
FONT_BOLD = FONTS_DIR / "BeVietnamPro-Bold.ttf"

DISCLAIMER = "Nội dung chỉ mang tính tham khảo, không phải khuyến nghị đầu tư."
AI_DECLARATION = "Video có sử dụng AI (MC ảo, giọng đọc tổng hợp)."
AI_METADATA = "AI-generated content: StockAI Studio; synthetic presenter & voice"
SYNTHETIC_WATERMARK = "DỮ LIỆU MINH HỌA – KHÔNG PHẢI SỐ LIỆU THẬT"

BANNED_PHRASES = ["chắc chắn", "mua ngay", "bắt đáy ngay", "x2 tài khoản", "cơ hội cuối cùng"]

TOPIC_KEYWORDS: dict[str, float] = {
    "vn-index": 3.0, "vnindex": 3.0, "cổ phiếu": 2.0, "chứng khoán": 2.0, "hose": 2.0, "hnx": 2.0,
    "upcom": 1.5, "khối ngoại": 3.0, "thanh khoản": 2.5, "lãi suất": 2.0, "tỷ giá": 1.5,
    "nhnn": 1.5, "fed": 1.5, "trái phiếu": 1.0, "vn30": 2.0, "niêm yết": 1.0,
}

RSS_SOURCES = {
    "CafeF": "https://cafef.vn/thi-truong-chung-khoan.rss",
    "Vietstock": "https://vietstock.vn/830/chung-khoan/co-phieu.rss",
    "VnEconomy": "https://vneconomy.vn/chung-khoan.rss",
}

HOOK_STYLES = ["câu hỏi gợi tò mò", "con số nổi bật nhất", "so sánh với phiên trước",
               "tin nóng nhất", "cảnh báo nhẹ nhàng"]

DEFAULT_SETTINGS: dict[str, str] = {
    "mode": "DEMO",
    "market.symbol": "VNINDEX",
    "market.providers_order": "public_vci,cache,synthetic",
    "llm.provider": "gemini",
    "llm.model": "gemini-3.8-flash",
    "llm.fallback_model": "gemini-3.5-flash-lite",
    "llm.openai_base_url": "",
    "llm.openai_model": "",
    "tts.provider": "edge",
    "tts.voice": "vi-VN-HoaiMyNeural",
    "tts.rate": "+5%",
    "tts.number_mode": "engine",
    "avatar.provider": "demo",
    "avatar.fal_model": "fal-ai/kling-video/ai-avatar/v2/standard",
    "avatar.max_cost_usd": "5",
    "publish.default_privacy": "private",
    "audio.bgm_db": "-22",
    "render.debug_safe_zone": "false",
    "retention.days": "30",
    "schedule.catchup_minutes": "120",
    "telegram_chat_id": "",
    "facebook_page_id": "",
    "facebook.graph_version": "v25.0",
    "youtube.category_id": "25",
    "ffmpeg_path": "",
    "ffprobe_path": "",
}

SECRET_KEYS = ["gemini_api_key", "openai_api_key", "fal_key", "heygen_api_key", "elevenlabs_api_key",
               "ssi_consumer_id", "ssi_consumer_secret", "telegram_bot_token", "facebook_page_token",
               "youtube_oauth_token", "tiktok_access_token"]


def data_dir() -> Path:
    p = Path(os.environ.get("STOCKAI_DATA_DIR") or user_data_dir(APP_NAME, APP_AUTHOR))
    for sub in ("user_assets", "outputs", "temp", "logs"):
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def setup_logging(level: str | None = None) -> None:
    """Log xoay vòng 5 file × 5 MB trong logs/, che bí mật (R-SEC-5)."""
    import logging
    from logging.handlers import RotatingFileHandler

    from stockai.secrets import redact

    class Redact(logging.Filter):
        def filter(self, record):
            record.msg = redact(str(record.msg))
            return True

    root = logging.getLogger("stockai")
    if root.handlers:
        return
    h = RotatingFileHandler(data_dir() / "logs" / "stockai.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    h.addFilter(Redact())
    root.addHandler(h)
    root.setLevel(level or os.environ.get("LOG_LEVEL", "INFO"))
    root.propagate = False


def is_offline() -> bool:
    return os.environ.get("STOCKAI_OFFLINE", "") in ("1", "true", "yes")
