import asyncio

from tkai.ai.runtime import OwnershipPolicy, ProviderRuntime


class Fake:
    def __init__(self):
        self.closed = False

    async def request(self, *a, **k):
        return {}

    async def close(self):
        self.closed = True

    def health_check(self):
        return True

    async def stream(self, *a, **k):
        yield b""


def test_runtime_lifecycle_and_ownership():
    async def run():
        f = Fake()
        r = ProviderRuntime(f, ownership=OwnershipPolicy.RUNTIME_OWNED)
        async with r.request_scope():
            pass
        await r.close()
        await r.close()
        assert f.closed and r.health()["transport_available"]

    asyncio.run(run())
