"""Bounded knowledge-domain metadata."""

from tkai.v9.knowledge_mesh.models import Domain

DOMAIN_TYPES = (
    "platform",
    "tiktok",
    "content",
    "publishing",
    "interaction",
    "account",
    "runtime",
    "resource",
    "workflow",
    "security",
    "governance",
    "analytics",
    "business",
    "recovery",
    "compatibility",
    "framework",
    "custom_bounded_domain",
)
__all__ = ("DOMAIN_TYPES", "Domain")
