from pathlib import Path


def test_orchestrator_dashboard_routes_and_client() -> None:
    root = Path(__file__).parents[2]
    app = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    pages = (root / "dashboard/frontend/src/pages.tsx").read_text(encoding="utf-8")
    client = (root / "dashboard/frontend/src/api.ts").read_text(encoding="utf-8")
    for page in (
        "execution-plans",
        "orchestrator-queues",
        "orchestrator-executions",
        "orchestrator-failures",
        "orchestrator-retries",
        "orchestrator-performance",
    ):
        assert page in app
        assert page in pages
    assert '"/orchestrator?tenant=default&actor=dashboard"' in client
