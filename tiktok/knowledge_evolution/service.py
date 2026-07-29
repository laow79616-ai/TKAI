"""Explainable knowledge aggregation, versioning, comparison, and advice."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import (
    KNOWLEDGE_SOURCES,
    ReadOnlyKnowledgePort,
    ReferenceOnlyKnowledgePort,
)
from .metrics import KnowledgeMetrics
from .models import (
    KnowledgeComparison,
    KnowledgeContext,
    KnowledgeProfile,
    KnowledgeRecommendation,
    KnowledgeVersion,
    RecommendationPriority,
    SourceEvidence,
    validate_confidence,
)


class TikTokKnowledgeEvolutionCenter:
    """Refines knowledge without executing, configuring, or publishing."""

    def __init__(
        self, sources: Mapping[str, ReadOnlyKnowledgePort] | None = None
    ) -> None:
        supplied = sources or {}
        self.sources = {
            name: supplied.get(name, ReferenceOnlyKnowledgePort(name))
            for name in KNOWLEDGE_SOURCES
        }
        self.profiles: dict[str, KnowledgeProfile] = {}
        self.versions: dict[str, KnowledgeVersion] = {}
        self.comparisons: dict[str, KnowledgeComparison] = {}
        self.recommendations: dict[str, KnowledgeRecommendation] = {}
        self.history: list[dict[str, Any]] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = KnowledgeMetrics()

    @staticmethod
    def _require(context: KnowledgeContext, action: str) -> None:
        required = f"tiktok:knowledge:{action}"
        if (
            required not in context.permissions
            and "tiktok:knowledge:admin" not in context.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: object, context: KnowledgeContext) -> None:
        if (
            getattr(item, "tenant", None) != context.tenant
            or getattr(item, "workspace", None) != context.workspace
        ):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(self, context: KnowledgeContext, action: str, resource: str) -> None:
        self.audit.append(
            {
                "actor": context.actor,
                "tenant": context.tenant,
                "workspace": context.workspace,
                "action": action,
                "resource": resource,
            }
        )

    def create_profile(
        self, profile: KnowledgeProfile, context: KnowledgeContext
    ) -> KnowledgeProfile:
        """Register refinement scope; this never mutates source modules."""
        self._require(context, "curate")
        self._scoped(profile, context)
        profile.validate()
        unknown = set(profile.sources) - set(self.sources)
        if unknown:
            raise ValueError(f"Unknown bounded knowledge sources: {sorted(unknown)}")
        if profile.id in self.profiles:
            raise ValueError("Knowledge profile ID must be unique.")
        self.profiles[profile.id] = profile
        self.metrics.increment("tiktok_knowledge_profiles_total")
        self._record(context, "profile.created", profile.id)
        return profile

    def aggregate(
        self, profile_id: str, subject: str, context: KnowledgeContext
    ) -> tuple[SourceEvidence, ...]:
        self._require(context, "read")
        profile = self.profiles[profile_id]
        self._scoped(profile, context)
        evidence: list[SourceEvidence] = []
        for source in profile.sources:
            snapshot = self.sources[source].read_knowledge(subject, context)
            if (
                snapshot.get("tenant") != context.tenant
                or snapshot.get("workspace") != context.workspace
            ):
                raise PermissionError("Adapter returned knowledge outside scope.")
            raw_confidence = snapshot.get("confidence", 0.0)
            if not isinstance(raw_confidence, (int, float)):
                raise ValueError("Source confidence must be numeric.")
            confidence = float(raw_confidence)
            validate_confidence(confidence)
            evidence.append(
                SourceEvidence(
                    source=source,
                    reference=f"{source}://{subject}",
                    summary=str(snapshot.get("summary", "")),
                    confidence=confidence,
                    integrity_reference=str(snapshot.get("integrity_reference", "")),
                )
            )
        return tuple(evidence)

    def evolve(
        self,
        version_id: str,
        profile_id: str,
        subject: str,
        summary: str,
        context: KnowledgeContext,
    ) -> KnowledgeVersion:
        self._require(context, "curate")
        if version_id in self.versions:
            raise ValueError("Knowledge version ID must be unique.")
        started = perf_counter()
        evidence = self.aggregate(profile_id, subject, context)
        if not evidence or not summary:
            raise ValueError("Knowledge evolution requires evidence and a summary.")
        existing = sorted(
            (
                item
                for item in self.versions.values()
                if item.profile_id == profile_id
                and item.tenant == context.tenant
                and item.workspace == context.workspace
            ),
            key=lambda item: item.number,
        )
        previous = existing[-1] if existing else None
        confidence = sum(item.confidence for item in evidence) / len(evidence)
        item = KnowledgeVersion(
            id=version_id,
            profile_id=profile_id,
            tenant=context.tenant,
            workspace=context.workspace,
            number=len(existing) + 1,
            summary=summary,
            confidence=confidence,
            evidence=evidence,
            explanation=(
                f"Version {len(existing) + 1} synthesized {len(evidence)} "
                "bounded source snapshots."
            ),
            previous_version_id=previous.id if previous else None,
        )
        self.versions[version_id] = item
        self.history.append({"type": "evolution", **asdict(item)})
        self.metrics.increment("tiktok_knowledge_versions_total")
        self.metrics.observe("tiktok_knowledge_confidence", confidence)
        self.metrics.observe(
            "tiktok_knowledge_latency_seconds", perf_counter() - started
        )
        self._record(context, "version.created", version_id)
        return item

    def compare(
        self,
        comparison_id: str,
        from_version_id: str,
        to_version_id: str,
        context: KnowledgeContext,
    ) -> KnowledgeComparison:
        self._require(context, "read")
        before = self.versions[from_version_id]
        after = self.versions[to_version_id]
        self._scoped(before, context)
        self._scoped(after, context)
        if before.profile_id != after.profile_id:
            raise ValueError("Only versions of the same profile can be compared.")
        item = KnowledgeComparison(
            id=comparison_id,
            tenant=context.tenant,
            workspace=context.workspace,
            from_version_id=before.id,
            to_version_id=after.id,
            summary_changed=before.summary != after.summary,
            confidence_delta=round(after.confidence - before.confidence, 6),
            explanation=(
                f"Compared profile {before.profile_id} versions "
                f"{before.number} and {after.number}."
            ),
        )
        self.comparisons[comparison_id] = item
        self.history.append({"type": "comparison", **asdict(item)})
        self._record(context, "versions.compared", comparison_id)
        return item

    def recommend(
        self,
        recommendation_id: str,
        version_id: str,
        title: str,
        rationale: str,
        context: KnowledgeContext,
        *,
        confidence: float,
        priority: RecommendationPriority = RecommendationPriority.MEDIUM,
    ) -> KnowledgeRecommendation:
        self._require(context, "curate")
        validate_confidence(confidence)
        version = self.versions[version_id]
        self._scoped(version, context)
        if not title or not rationale:
            raise ValueError("Recommendations require a title and rationale.")
        item = KnowledgeRecommendation(
            id=recommendation_id,
            version_id=version_id,
            tenant=context.tenant,
            workspace=context.workspace,
            title=title,
            rationale=rationale,
            confidence=confidence,
            priority=priority,
            evidence_references=tuple(
                evidence.reference for evidence in version.evidence
            ),
        )
        self.recommendations[recommendation_id] = item
        self.history.append({"type": "recommendation", **asdict(item)})
        self.metrics.increment("tiktok_knowledge_recommendations_total")
        self._record(context, "recommendation.created", recommendation_id)
        return item

    def _items(
        self, store: Mapping[str, Any], context: KnowledgeContext
    ) -> list[dict[str, Any]]:
        self._require(context, "read")
        return [
            asdict(item)
            for item in store.values()
            if getattr(item, "tenant", None) == context.tenant
            and getattr(item, "workspace", None) == context.workspace
        ]

    def evolution(self, context: KnowledgeContext) -> list[dict[str, Any]]:
        self._require(context, "read")
        return [
            item
            for item in self.history
            if item["tenant"] == context.tenant
            and item["workspace"] == context.workspace
        ]

    def analytics(self, context: KnowledgeContext) -> dict[str, float]:
        versions = self._items(self.versions, context)
        return {
            "profiles_total": float(len(self._items(self.profiles, context))),
            "versions_total": float(len(versions)),
            "recommendations_total": float(
                len(self._items(self.recommendations, context))
            ),
            "average_confidence": (
                sum(float(item["confidence"]) for item in versions) / len(versions)
                if versions
                else 0.0
            ),
            "latency_seconds": self.metrics.values["tiktok_knowledge_latency_seconds"],
        }

    def dashboard(self, context: KnowledgeContext) -> dict[str, Any]:
        return {
            "sections": [
                "knowledge_overview",
                "knowledge_sources",
                "knowledge_versions",
                "evolution_timeline",
                "recommendations",
                "analytics",
                "history",
            ],
            "knowledge_overview": {
                "read_only": True,
                "direct_execution": False,
                "runtime_configuration_mutation": False,
                "publishing": False,
                "restriction_bypass": False,
            },
            "knowledge_sources": list(self.sources),
            "knowledge_versions": self._items(self.versions, context),
            "evolution_timeline": self.evolution(context),
            "recommendations": self._items(self.recommendations, context),
            "analytics": self.analytics(context),
            "history": self.evolution(context),
        }
