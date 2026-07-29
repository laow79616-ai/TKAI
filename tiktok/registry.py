"""Canonical registry for completed TKAI V5 TikTok modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TikTokModule:
    """Static integration metadata for one completed TikTok module."""

    key: str
    name: str

    @property
    def package(self) -> str:
        return f"tiktok.{self.key}"


TIKTOK_MODULES = (
    TikTokModule("runtime_manager", "Runtime Manager"),
    TikTokModule("account_center", "Account Center"),
    TikTokModule("browser_runtime", "Browser Runtime"),
    TikTokModule("browser_cluster", "Browser Cluster"),
    TikTokModule("device_center", "Device Center"),
    TikTokModule("proxy_center", "Proxy Center"),
    TikTokModule("account_farming", "Account Farming"),
    TikTokModule("content_center", "Content Center"),
    TikTokModule("content_pipeline", "Content Pipeline"),
    TikTokModule("publishing_center", "Publishing Center"),
    TikTokModule("data_collection", "Data Collection Center"),
    TikTokModule("interaction_center", "Interaction Center"),
    TikTokModule("risk_control", "Risk Control Center"),
    TikTokModule("workflow_center", "Workflow Center"),
    TikTokModule("resource_center", "Resource Center"),
    TikTokModule("automation_engine", "TikTok AI Automation Engine"),
    TikTokModule("task_scheduler", "TikTok AI Task Scheduler"),
    TikTokModule("execution_engine", "Execution Engine"),
    TikTokModule("operations_center", "Operations Center"),
    TikTokModule("operations_planner", "Operations Planner"),
    TikTokModule("analytics_center", "Analytics Center"),
    TikTokModule("optimization_center", "Continuous Optimization Center"),
    TikTokModule("creator_workspace", "Creator Workspace"),
    TikTokModule("control_tower", "Control Tower"),
    TikTokModule("decision_center", "Intelligent Decision Center"),
    TikTokModule("campaign_center", "Campaign Center"),
    TikTokModule("growth_center", "Growth Center"),
    TikTokModule("performance_insights", "Performance Insights Center"),
    TikTokModule("business_workspace", "Business Workspace"),
    TikTokModule("lead_center", "Lead Management Center"),
    TikTokModule("business_intelligence_center", "Business Intelligence Center"),
    TikTokModule("autonomous_operation", "Autonomous Operation Center"),
    TikTokModule("governance_center", "Autonomous Governance Center"),
    TikTokModule("intelligence_center", "Autonomous Intelligence Center"),
    TikTokModule("knowledge_evolution", "Knowledge Evolution Center"),
    TikTokModule("decision_evolution", "Decision Evolution Center"),
)

TIKTOK_MODULE_KEYS = tuple(module.key for module in TIKTOK_MODULES)

__all__ = ("TIKTOK_MODULES", "TIKTOK_MODULE_KEYS", "TikTokModule")
