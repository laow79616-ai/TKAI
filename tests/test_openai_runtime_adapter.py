import asyncio

from tkai.ai.models import ChatMessage, ChatRequest
from tkai.ai.openai_runtime_adapter import OpenAIProviderRuntimeAdapter
from tkai.ai.runtime import ProviderRuntime
from tkai.ai.transport_adapter import TransportAdapter


def test_mapping():
    async def run():
        r = ProviderRuntime(
            TransportAdapter(
                lambda *_: {"id": "x", "choices": [{"message": {"content": "ok"}}]}
            )
        )
        a = OpenAIProviderRuntimeAdapter(r, provider="openai", model="m", headers={})
        assert (
            await a.chat(ChatRequest((ChatMessage("user", "x"),)))
        ).request_id == "x"

    asyncio.run(run())
