"""Human approval steps, escalation, and audit."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class Approval:
    id: str
    execution_id: str
    approvers: tuple[str, ...] = ()
    team: str | None = None
    role: str | None = None
    timeout_seconds: int = 3600
    escalation: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    decision: str | None = None
    audit: list[dict[str, str]] = field(default_factory=list)

    def decide(self, actor: str, decision: str) -> None:
        if actor not in self.approvers and actor not in {self.team, self.role}:
            raise PermissionError("Actor is not an approver.")
        if decision not in {"approved", "rejected"}:
            raise ValueError("Invalid approval decision.")
        self.decision = decision
        self.audit.append({"actor": actor, "decision": decision})

    def timed_out(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current >= self.created_at + timedelta(seconds=self.timeout_seconds)
