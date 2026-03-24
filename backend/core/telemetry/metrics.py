"""
Lightweight in-process telemetry counters.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Dict


class MetricsRegistry:
    """Simple async-safe counter registry."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def incr(self, name: str, value: int = 1) -> None:
        async with self._lock:
            self._counters[name] += value

    async def snapshot(self) -> Dict[str, int]:
        async with self._lock:
            return dict(self._counters)


metrics = MetricsRegistry()
