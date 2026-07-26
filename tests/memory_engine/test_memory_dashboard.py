from pathlib import Path


def test_memory_dashboard_routes_client_and_sections() -> None:
    root = Path(__file__).parents[2]
    app = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    pages = (root / "dashboard/frontend/src/pages.tsx").read_text(encoding="utf-8")
    client = (root / "dashboard/frontend/src/api.ts").read_text(encoding="utf-8")
    for page in (
        "memory",
        "memory-namespaces",
        "memory-usage",
        "memory-retention",
        "memory-cache",
        "memory-retrieval",
        "memory-metrics",
    ):
        assert f'path="/{page}"' in app
        assert page in pages
    assert '"/memory/namespaces?' in client
    assert '"/memory/cache"' in client
