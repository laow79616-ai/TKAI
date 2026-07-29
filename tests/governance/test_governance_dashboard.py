from pathlib import Path


def test_governance_dashboard_contract() -> None:
    root = Path(__file__).parents[2]
    app = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    pages = (root / "dashboard/frontend/src/pages.tsx").read_text(encoding="utf-8")
    client = (root / "dashboard/frontend/src/api.ts").read_text(encoding="utf-8")
    for page in (
        "governance",
        "governance-policies",
        "governance-risks",
        "governance-compliance",
        "governance-approvals",
        "governance-controls",
        "governance-models",
        "governance-prompts",
        "governance-agents",
        "governance-applications",
        "governance-workflows",
        "governance-data",
        "governance-incidents",
        "governance-exceptions",
        "governance-reports",
    ):
        assert f'path="/{page}"' in app
        assert page in pages
    assert (
        "/governance/dashboard?tenant=default&workspace=default&actor=dashboard"
    ) in client
