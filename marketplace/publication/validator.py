"""Deterministic structural publication validator for reference-only services."""

from __future__ import annotations

from ..publisher import Publisher, PublisherTier
from .models import (
    PublicationDecision,
    PublicationIssue,
    PublicationPolicy,
    PublicationPolicyResult,
    PublicationRequest,
    PublicationResult,
)

_TIER_ORDER = {
    PublisherTier.COMMUNITY: 0,
    PublisherTier.VERIFIED: 1,
    PublisherTier.OFFICIAL: 2,
    PublisherTier.ENTERPRISE: 3,
}


class ReferencePublicationValidator:
    """Evaluate request shape and local policy without remote ownership checks."""

    def __init__(self, publisher: Publisher) -> None:
        self._publisher = publisher

    def evaluate(
        self, request: PublicationRequest, policy: PublicationPolicy
    ) -> PublicationPolicyResult:
        """Return deterministic policy issues sorted by code and field."""
        manifest = request.package_manifest
        issues: list[PublicationIssue] = []
        if (
            not policy.allow_community_submission
            and self._publisher.tier is PublisherTier.COMMUNITY
        ):
            issues.append(
                PublicationIssue(
                    "community_not_allowed",
                    "Community publisher submissions are not allowed.",
                    "publisher_tier",
                )
            )
        if (
            policy.required_publisher_tier is not None
            and _TIER_ORDER[self._publisher.tier]
            < _TIER_ORDER[policy.required_publisher_tier]
        ):
            issues.append(
                PublicationIssue(
                    "publisher_tier_required",
                    "Publisher tier does not meet the required level.",
                    "publisher_tier",
                )
            )
        if not policy.allow_prerelease and manifest.version.prerelease is not None:
            issues.append(
                PublicationIssue(
                    "prerelease_not_allowed",
                    "Prerelease package versions are not allowed.",
                    "version",
                )
            )
        if not policy.allow_empty_dependencies and not manifest.dependencies:
            issues.append(
                PublicationIssue(
                    "dependencies_required",
                    "Package dependencies must be declared.",
                    "dependencies",
                )
            )
        compatibility = manifest.compatibility
        if not policy.allow_unknown_compatibility_targets and any(
            value is None
            for value in (
                compatibility.runtime,
                compatibility.sdk,
                compatibility.studio,
                compatibility.enterprise,
                compatibility.cloud,
            )
        ):
            issues.append(
                PublicationIssue(
                    "compatibility_required",
                    "All compatibility targets must be declared.",
                    "compatibility",
                )
            )
        if len(manifest.tags) > policy.max_tag_count:
            issues.append(
                PublicationIssue(
                    "tag_limit_exceeded",
                    "Package tag count exceeds the local policy limit.",
                    "tags",
                )
            )
        if len(request.metadata.values) > policy.max_metadata_entries:
            issues.append(
                PublicationIssue(
                    "metadata_limit_exceeded",
                    "Publication metadata count exceeds the local policy limit.",
                    "metadata",
                )
            )
        ordered = tuple(sorted(issues, key=lambda issue: (issue.code, issue.field)))
        decision = PublicationDecision.REJECT if ordered else PublicationDecision.ACCEPT
        return PublicationPolicyResult(decision, ordered)

    def validate(
        self, request: PublicationRequest, policy: PublicationPolicy
    ) -> PublicationResult:
        """Validate required local structure and then apply the declarative policy."""
        issues: list[PublicationIssue] = []
        manifest = request.package_manifest
        if not str(request.publication_id):
            issues.append(
                PublicationIssue(
                    "publication_id_required",
                    "Publication id is required.",
                    "publication_id",
                )
            )
        if not request.publisher_id:
            issues.append(
                PublicationIssue(
                    "publisher_id_required", "Publisher id is required.", "publisher_id"
                )
            )
        if not manifest.package_id:
            issues.append(
                PublicationIssue(
                    "package_id_required", "Package id is required.", "package_id"
                )
            )
        if manifest.version.major < 0:
            issues.append(
                PublicationIssue(
                    "version_invalid", "Package version is invalid.", "version"
                )
            )
        policy_result = self.evaluate(request, policy)
        ordered = tuple(
            sorted(
                tuple(issues) + policy_result.issues,
                key=lambda issue: (issue.code, issue.field),
            )
        )
        decision = PublicationDecision.REJECT if ordered else policy_result.decision
        return PublicationResult(
            request.publication_id, request.requested_status, decision, ordered
        )
