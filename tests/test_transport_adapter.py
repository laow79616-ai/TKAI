import asyncio

from tkai.ai.transport_adapter import TransportAdapter


def test_legacy_adapter_request_close():
    async def run():
        adapter = TransportAdapter(lambda path, payload, headers: {"ok": path})
        assert (await adapter.request("POST", "/x"))["ok"] == "/x"
        await adapter.close()
        assert not adapter.health_check()

    asyncio.run(run())
