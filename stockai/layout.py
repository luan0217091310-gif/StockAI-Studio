"""TỌA ĐỘ KHUNG HÌNH 9:16 — nguồn sự thật duy nhất (Blueprint Mục 10)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x: int
    y: int
    w: int
    h: int

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    def intersects(self, o: "Box") -> bool:
        return self.x < o.x2 and o.x < self.x2 and self.y < o.y2 and o.y < self.y2


@dataclass(frozen=True)
class Layout:
    W: int = 1080
    H: int = 1920
    FPS: int = 30
    z0_top: Box = Box(0, 0, 1080, 120)
    header: Box = Box(60, 120, 960, 100)
    ticker: Box = Box(0, 220, 1080, 60)
    ticker_speed: int = 140
    broll: Box = Box(0, 280, 1080, 660)
    ai_label: Box = Box(76, 296, 440, 44)
    ai_intro: Box = Box(76, 360, 928, 92)
    divider: Box = Box(0, 940, 1080, 4)
    avatar: Box = Box(0, 944, 1080, 976)
    subtitles: Box = Box(140, 1240, 800, 160)
    subtitle_font_size: int = 60
    subtitle_max_line_px: int = 800
    subtitle_margin_v: int = 520  # đáy chữ tại y = 1920 - 520 = 1400
    wave: Box = Box(120, 1410, 840, 60)
    disclaimer: Box = Box(60, 860, 900, 70)
    # Vùng bị UI nền tảng che (Mục 10.3)
    unsafe_bottom: Box = Box(0, 1440, 1080, 480)
    unsafe_right: Box = Box(960, 840, 120, 600)
    unsafe_top: Box = Box(0, 0, 1080, 120)

    @property
    def unsafe_zones(self) -> list[Box]:
        return [self.unsafe_bottom, self.unsafe_right, self.unsafe_top]

    @property
    def important_zones(self) -> dict[str, Box]:
        return {"subtitles": self.subtitles, "ai_label": self.ai_label, "ticker": self.ticker,
                "disclaimer": self.disclaimer, "header": self.header}


LAYOUT = Layout()
