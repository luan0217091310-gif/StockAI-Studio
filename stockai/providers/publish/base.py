"""Quy tắc đăng chung (R-PUB-1..4) + retry."""

import asyncio
from collections.abc import Awaitable, Callable

import httpx

from stockai.errors import TransientError
from stockai.models import PublishResult


async def with_retry(fn: Callable[[], Awaitable[PublishResult]], attempts: int = 3) -> tuple[PublishResult, int]:
    """R-PUB-3: retry tối đa 3 lần cho timeout/5xx/429, backoff lũy thừa; không retry 4xx khác."""
    last: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            return await fn(), i
        except (httpx.TimeoutException, httpx.TransportError, TransientError) as e:
            last = e
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429,) or e.response.status_code >= 500:
                last = e
            else:
                raise
        await asyncio.sleep(2 ** i)
    raise TransientError(f"Hết số lần thử: {last}")


def raise_for(r: httpx.Response) -> None:
    if r.status_code == 429 or r.status_code >= 500:
        raise TransientError(f"HTTP {r.status_code}: {r.text[:200]}")
    r.raise_for_status()
