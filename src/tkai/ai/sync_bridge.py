"""Safe synchronous bridge for provider coroutines."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Coroutine, Iterator
from queue import Queue
from threading import Event, Thread
from typing import Any, TypeVar

from .errors import ProviderConfigurationError

T = TypeVar("T")


class SyncBridge:
    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: Thread | None = None
        self._ready = Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._ready.clear()

        def worker() -> None:
            loop = asyncio.new_event_loop()
            self._loop = loop
            self._ready.set()
            loop.run_forever()
            loop.close()

        self._thread = Thread(target=worker, daemon=True)
        self._thread.start()
        self._ready.wait()

    def _check(self) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return
        raise ProviderConfigurationError(
            "Use await provider.achat(...) inside a running event loop"
        )

    def run(self, coro: Coroutine[Any, Any, T]) -> T:
        self._check()
        self.start()
        assert self._loop
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def stream(self, items: AsyncIterator[T]) -> Iterator[T]:
        self._check()
        queue: Queue[object] = Queue(maxsize=8)
        done = object()

        async def consume() -> None:
            try:
                async for item in items:
                    queue.put(item)
            except BaseException as exc:
                queue.put(exc)
            finally:
                queue.put(done)

        self.start()
        assert self._loop
        asyncio.run_coroutine_threadsafe(consume(), self._loop)
        while True:
            item = queue.get()
            if item is done:
                return
            if isinstance(item, BaseException):
                raise item
            yield item  # type: ignore[misc]

    def close(self) -> None:
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=1)
        self._loop = None
        self._thread = None

    stop = close
