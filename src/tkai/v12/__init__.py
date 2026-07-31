"""TKAI V12 Autonomous AI Platform: local metadata only."""

from .dependency_engine import DependencyAnalyzer, DependencyFinding
from .discovery import DiscoveryPolicy, LocalDiscovery
from .models import (
    AgentProfile,
    AgentType,
    ContractProfile,
    HealthStatus,
    InterfaceProfile,
    KnowledgeProfile,
    Lifecycle,
    MemoryProfile,
    MemoryType,
    MetadataProfile,
    ModelProfile,
    PluginProfile,
    Relationship,
    RelationshipType,
    SkillProfile,
    WorkflowEdge,
    WorkflowNode,
    WorkflowNodeType,
    WorkflowProfile,
    validate_safe_metadata,
)
from .platform import COMPONENTS, METRIC_NAMES, V12Platform
from .registry import BoundedRegistry
from .validation_engine import ValidationResult, validate_platform

__version__ = "12.0.0"

__all__ = (
    "AgentProfile",
    "AgentType",
    "BoundedRegistry",
    "COMPONENTS",
    "ContractProfile",
    "DependencyAnalyzer",
    "DependencyFinding",
    "DiscoveryPolicy",
    "HealthStatus",
    "InterfaceProfile",
    "KnowledgeProfile",
    "Lifecycle",
    "LocalDiscovery",
    "METRIC_NAMES",
    "MemoryProfile",
    "MemoryType",
    "MetadataProfile",
    "ModelProfile",
    "PluginProfile",
    "Relationship",
    "RelationshipType",
    "SkillProfile",
    "V12Platform",
    "ValidationResult",
    "WorkflowEdge",
    "WorkflowNode",
    "WorkflowNodeType",
    "WorkflowProfile",
    "__version__",
    "validate_platform",
    "validate_safe_metadata",
)
