import asyncio

import pytest

from tkai.ai.errors import ProviderConfigurationError
from tkai.ai.sync_bridge import SyncBridge


def test_run_stream_and_close():
    b = SyncBridge()
    assert b.run(asyncio.sleep(0, result=3)) == 3

    async def values():
        yield 1
        yield 2

    assert list(b.stream(values())) == [1, 2]
    b.close()
    b.close()


def test_running_loop_rejected():
    async def run():
        coroutine = asyncio.sleep(0)
        with pytest.raises(ProviderConfigurationError):
            SyncBridge().run(coroutine)
        coroutine.close()

    asyncio.run(run())
