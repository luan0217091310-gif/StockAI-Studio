"""Định dạng số kiểu Việt Nam: 1.285,40."""


def fmt(x: float, d: int = 2) -> str:
    s = f"{abs(x):,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return ("-" if x < 0 else "") + s


def fmt_signed(x: float, d: int = 2) -> str:
    return ("+" if x >= 0 else "-") + fmt(abs(x), d)
