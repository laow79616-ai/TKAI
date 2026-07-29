# ruff: noqa: F405
from datetime import timedelta

import pytest

from tiktok.governance_center.api import ROUTES, register_governance_center_routes
from tiktok.governance_center.metrics import METRIC_NAMES
from tiktok.governance_center.models import *  # noqa: F403, F405
from tiktok.governance_center.service import TikTokAutonomousGovernanceCenter


def ctx(w="w"):
    return AccessContext("t", w, "owner", frozenset({"tiktok:governance-center:admin"}))


def profile(w="w"):
    return GovernanceProfile(
        "p",
        "Governance",
        "bounded",
        "t",
        w,
        "owner",
        frozenset({GovernanceScope.PLATFORM}),
    )


def test_lifecycle_scope_and_rules():
    s = TikTokAutonomousGovernanceCenter()
    s.create_profile(profile(), ctx())
    s.transition_profile("p", Lifecycle.REVIEW, ctx())
    with pytest.raises(ValueError):
        s.transition_profile("p", Lifecycle.ACTIVE, ctx())
    with pytest.raises(PermissionError):
        s.transition_profile("p", Lifecycle.APPROVED, ctx("other"))
    s.create_policy(
        Policy(
            "pol",
            "p",
            "safety",
            "t",
            "w",
            frozenset({GovernanceScope.PLATFORM}),
            "bounded",
        ),
        ctx(),
    )
    with pytest.raises(ValueError):
        s.create_rule(
            PolicyRule(
                "r",
                "pol",
                "t",
                "w",
                GovernanceScope.PLATFORM,
                {"expression": "exec(x)"},
                1,
                1,
                1,
                "deny",
            ),
            ctx(),
        )


def test_safety_change_evidence():
    s = TikTokAutonomousGovernanceCenter()
    s.request_approval(Approval("a", "mission", "m", "t", "w", "mission"), ctx())
    s.decide_approval("a", True, "reviewer", ctx())
    assert s.govern("mission_engine", "m", ctx(), approval_id="a")["execute"] is False
    assert not s.govern("mission_engine", "m", ctx(), frozenset({"captcha_bypass"}))[
        "allowed"
    ]
    with pytest.raises(PermissionError):
        s.request_exception(
            ExceptionRequest(
                "e",
                "p",
                None,
                "t",
                "w",
                "unsafe",
                GovernanceScope.PLATFORM,
                utcnow() + timedelta(hours=1),
                ("review",),
                frozenset({"security_bypass"}),
            ),
            ctx(),
        )
    with pytest.raises(ValueError):
        s.request_change(
            ChangeRequest(
                "c",
                "runtime_manager",
                "t",
                "w",
                "1",
                "2",
                "upgrade",
                RiskLevel.HIGH,
                "impact",
                (),
                (),
                "",
                "",
                "validate",
                "rollback",
            ),
            ctx(),
        )
    with pytest.raises(ValueError):
        s.add_evidence(
            Evidence("ev", "policy", "p", "t", "w", "ref", "hash", False), ctx()
        )


def test_api_dashboard_metrics():
    class App:
        def __init__(self):
            self.paths = []

        def add_api_route(self, path, endpoint, **kwargs):
            self.paths.append(path)

    s = TikTokAutonomousGovernanceCenter()
    s.create_profile(profile(), ctx())
    assert len(s.dashboard(ctx())["sections"]) == 18
    assert all(n in s.metrics.render_prometheus() for n in METRIC_NAMES)
    app = App()
    register_governance_center_routes(app, s)
    assert set(ROUTES).issubset(app.paths)
