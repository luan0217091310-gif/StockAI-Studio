"""StockAI Studio — Blueprint v3.0."""

import sys as _sys
import types as _types

__version__ = "3.0.0"

# Một số máy Windows bật Application Control chặn DLL chưa ký `_multiprocessing.pyd` của bản Python do uv tải về.
# APScheduler chỉ import ProcessPoolExecutor (không dùng tới) → thay bằng module rỗng để import không vỡ.
# StockAI không dùng multiprocessing ở bất kỳ đâu. Xem docs/DECISIONS.md.
try:
    import _multiprocessing  # noqa: F401
except ImportError:
    _mp = _types.ModuleType("_multiprocessing")

    def _unavailable(*_a, **_k):
        raise OSError("multiprocessing bị chặn bởi Application Control trên máy này")

    _mp.flags = {}
    _mp.closesocket = _mp.recv = _mp.send = _unavailable
    _sys.modules["_multiprocessing"] = _mp
