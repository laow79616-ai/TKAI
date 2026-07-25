"""Immutable, deterministic Verification and Trust Foundation descriptors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _copy(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


class VerificationStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class VerificationLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class VerificationIssueCode(str, Enum):
    MISSING_MANIFEST = "missing_manifest"
    INVALID_PUBLICATION = "invalid_publication"
    PUBLISHER_LEVEL = "publisher_level"
    DEPENDENCY_METADATA = "dependency_metadata"
    COMPATIBILITY_METADATA = "compatibility_metadata"
    INSTALLER_RESULT = "installer_result"


class TrustLevel(str, Enum):
    UNKNOWN = "unknown"
    COMMUNITY = "community"
    VERIFIED = "verified"
    OFFICIAL = "official"
    ENTERPRISE = "enterprise"


class TrustDecision(str, Enum):
    ALLOW = "allow"
    REJECT = "reject"
    REVIEW = "review"


@dataclass(frozen=True, slots=True)
class VerificationRequest:
    subject: object
    level: VerificationLevel = VerificationLevel.BASIC
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _copy(self.metadata))


@dataclass(frozen=True, slots=True)
class VerificationIssue:
    code: VerificationIssueCode
    message: str


@dataclass(frozen=True, slots=True)
class VerificationResult:
    status: VerificationStatus
    issues: tuple[VerificationIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "issues",
            tuple(sorted(self.issues, key=lambda x: (x.code.value, x.message))),
        )


@dataclass(frozen=True, slots=True)
class VerificationReport:
    request: VerificationRequest
    result: VerificationResult


@dataclass(frozen=True, slots=True)
class VerificationStatistics:
    total: int
    passed: int
    warning: int
    failed: int


@dataclass(frozen=True, slots=True)
class VerificationSnapshot:
    reports: tuple[VerificationReport, ...] = ()
    statistics: VerificationStatistics = VerificationStatistics(0, 0, 0, 0)
    closed: bool = False


@dataclass(frozen=True, slots=True)
class TrustRule:
    name: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class TrustPolicy:
    minimum: TrustLevel = TrustLevel.COMMUNITY
    publisher_required: bool = False
    allow_prerelease: bool = True
    dependency_policy: str = "declared"
    rules: tuple[TrustRule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "rules", tuple(self.rules))


@dataclass(frozen=True, slots=True)
class TrustReport:
    level: TrustLevel
    decision: TrustDecision
    policy: TrustPolicy


@dataclass(frozen=True, slots=True)
class TrustStatistics:
    total: int
    allow: int
    reject: int
    review: int


@dataclass(frozen=True, slots=True)
class TrustSnapshot:
    reports: tuple[TrustReport, ...] = ()
    statistics: TrustStatistics = TrustStatistics(0, 0, 0, 0)
    closed: bool = False
