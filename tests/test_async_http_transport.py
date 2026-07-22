"""Offline tests for the owned async HTTP transport."""

import asyncio

import httpx

from tkai.providers.http import AsyncHTTPTransport


def test_get_post_headers_params_and_ownership() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers["x-test"] == "yes"
            return httpx.Response(
                200,
                json={"path": request.url.path, "query": request.url.query.decode()},
                headers={"x-request-id": "id"},
            )

        transport = AsyncHTTPTransport(transport=httpx.MockTransport(handler))
        result = await transport.get(
            "https://offline.test/items", headers={"x-test": "yes"}, params={"q": "1"}
        )
        assert result.data["path"] == "/items" and result.request_id == "id"
        await transport.close()
        await transport.close()

    asyncio.run(run())
