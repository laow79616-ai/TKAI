"""Policy-awareness evaluation without policy execution."""


def assess(
    *,
    eligible: bool = True,
    paused: bool = False,
    maintenance: bool = False,
    kill_switch: bool = False,
) -> dict[str, object]:
    blocked = tuple(
        name
        for name, active in (
            ("paused", paused),
            ("maintenance", maintenance),
            ("kill-switch", kill_switch),
        )
        if active
    )
    return {
        "eligible": eligible and not blocked,
        "blocked_by": blocked,
        "approval_required": True,
        "automatic_approval": False,
    }


__all__ = ("assess",)
