from pathlib import Path


def test_collaboration_dashboard_contract() -> None:
    root = Path(__file__).parents[2]
    app = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    pages = (root / "dashboard/frontend/src/pages.tsx").read_text(encoding="utf-8")
    client = (root / "dashboard/frontend/src/api.ts").read_text(encoding="utf-8")
    for page in (
        "collaboration",
        "collaboration-teams",
        "collaboration-projects",
        "collaboration-sessions",
        "collaboration-tasks",
        "collaboration-timeline",
        "collaboration-activity",
        "collaboration-notifications",
    ):
        assert f'path="/{page}"' in app
        assert page in pages
    dashboard_path = (
        "/collaboration/dashboard?tenant=default&workspace=default&actor=dashboard"
    )
    assert dashboard_path in client
