"""Event Bus: phát sự kiện → WebSocket + bảng job_events (R-RUN-5)."""

import asyncio
from datetime import UTC, datetime

from stockai.secrets import redact


class EventBus:
    def __init__(self):
        self._subs: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)

    def publish(self, event: dict) -> None:
        event.setdefault("ts", datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"))
        if "message" in event:
            event["message"] = redact(event["message"])
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


bus = EventBus()
