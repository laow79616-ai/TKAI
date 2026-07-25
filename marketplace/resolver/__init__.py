"""Reference-only, offline dependency resolver interfaces for Marketplace V5."""

from .errors import (
    ResolverClosedError,
    ResolverError,
    ResolverGraphError,
    ResolverInputError,
    ResolverValidationError,
)
from .graph import DependencyGraphBuilder
from .models import (
    DependencyCoordinate,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyRequirement,
    ResolutionExplanation,
    ResolutionIssue,
    ResolutionIssueCode,
    ResolutionRequest,
    ResolutionResult,
    ResolutionSnapshot,
    ResolutionStatus,
    ResolutionStrategy,
)
from .service import ReferenceResolverService
from .source import ReferenceRegistryResolutionSource, RegistryResolutionSource

__all__ = (
    "DependencyCoordinate",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyGraphBuilder",
    "DependencyNode",
    "DependencyRequirement",
    "ReferenceRegistryResolutionSource",
    "ReferenceResolverService",
    "RegistryResolutionSource",
    "ResolutionExplanation",
    "ResolutionIssue",
    "ResolutionIssueCode",
    "ResolutionRequest",
    "ResolutionResult",
    "ResolutionSnapshot",
    "ResolutionStatus",
    "ResolutionStrategy",
    "ResolverClosedError",
    "ResolverError",
    "ResolverGraphError",
    "ResolverInputError",
    "ResolverValidationError",
)
