"""Optional FastAPI application factory for read-only Marketplace Server routes."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module
from os import environ
from types import ModuleType
from typing import Any, cast

from api_management import ApiManagementPlatform
from api_management.api import register_api_management_routes
from app_store import EnterpriseAppStore
from app_store.api import register_app_store_routes
from applications import ApplicationCenter
from applications.api import register_application_routes
from collaboration import CollaborationScope, EnterpriseAICollaborationPlatform
from collaboration.api import register_collaboration_routes
from command_center import CommandCenterPlatform
from command_center.api import register_command_center_routes
from data_platform import DataPlatform
from data_platform.api import register_data_routes
from governance import EnterpriseAIGovernancePlatform, GovernanceScope
from governance.api import register_governance_routes
from knowledge_graph import KnowledgeGraphPlatform
from knowledge_graph.api import register_knowledge_graph_routes
from knowledge_platform import KnowledgePlatform
from knowledge_platform.api import register_knowledge_routes
from local_runtime.api import register_local_runtime_routes
from marketplace.api import MarketplaceApi
from marketplace.enterprise_store import EnterpriseMarketplace
from memory_engine import EnterpriseAIMemoryEngine, MemoryScope
from memory_engine.api import register_memory_routes
from model_platform import ModelPlatform, ModelScope
from model_platform.api import register_model_routes
from orchestrator import EnterpriseAIOrchestrator
from orchestrator.api import register_orchestrator_routes
from reasoning_engine import EnterpriseAIReasoningEngine, ReasoningScope
from reasoning_engine.api import register_reasoning_routes
from security_platform import SecurityPlatform
from security_platform.api import register_security_routes
from server.production import ProductionConfigurationLoader, ProductionRuntime
from tiktok.account_center import TikTokAccountCenter
from tiktok.account_center.api import register_tiktok_routes
from tiktok.account_farming import (
    BoundedAccountCenterAdapter,
    ExistingBrowserRuntimeAdapter,
    ExistingProxyCenterAdapter,
    TikTokAccountFarming,
)
from tiktok.account_farming.api import register_account_farming_routes
from tiktok.analytics_center import TikTokAIAnalyticsCenter
from tiktok.analytics_center.api import register_analytics_center_routes
from tiktok.browser_cluster import TikTokBrowserCluster
from tiktok.browser_cluster.api import register_browser_cluster_routes
from tiktok.browser_runtime import AccountCenterStatusAdapter, TikTokBrowserRuntime
from tiktok.browser_runtime.api import register_browser_runtime_routes
from tiktok.content_center import (
    ExistingAccountCenterAdapter as ContentAccountAdapter,
)
from tiktok.content_center import (
    ExistingBrowserRuntimeAdapter as ContentBrowserAdapter,
)
from tiktok.content_center import (
    ExistingFarmingAdapter,
    TikTokContentCenter,
)
from tiktok.content_center import (
    ExistingProxyCenterAdapter as ContentProxyAdapter,
)
from tiktok.content_center.api import register_content_center_routes
from tiktok.data_collection import (
    ExistingAccountCenterAdapter as DataAccountAdapter,
)
from tiktok.data_collection import ExistingProxyCenterAdapter as DataProxyAdapter
from tiktok.data_collection import TikTokDataCollectionCenter
from tiktok.data_collection.api import register_data_collection_routes
from tiktok.device_center import TikTokDeviceCenter
from tiktok.device_center.api import register_device_center_routes
from tiktok.interaction_center import TikTokInteractionCenter
from tiktok.interaction_center.api import register_interaction_routes
from tiktok.operations_center import TikTokOperationsCommandCenter
from tiktok.operations_center.api import register_operations_center_routes
from tiktok.proxy_center import BrowserRuntimeProxyAdapter, TikTokProxyCenter
from tiktok.proxy_center.api import register_proxy_center_routes
from tiktok.publishing_center import (
    ExistingAccountCenterAdapter as PublishingAccountAdapter,
)
from tiktok.publishing_center import (
    ExistingBrowserPublisher,
    ExistingContentCenterAdapter,
    ExistingFarmingPolicy,
    ExistingProxyPolicy,
    TikTokPublishingCenter,
)
from tiktok.publishing_center.api import register_publishing_center_routes
from tiktok.risk_control import TikTokRiskControlCenter
from tiktok.risk_control.api import register_risk_control_routes
from tiktok.workflow_center import TikTokWorkflowOrchestrationCenter
from tiktok.workflow_center.api import register_workflow_center_routes
from tkai.agent import AgentApi
from tkai.enterprise import EnterprisePlatform
from tkai.enterprise.api import register_enterprise_platform_routes
from tkai.plugins.api import register_plugin_routes
from tkai.plugins.marketplace import EnterprisePluginMarketplace
from workflow_platform import WorkflowPlatform
from workflow_platform.api import register_workflow_routes

from .auth.router import register_routes as register_auth_routes
from .dependencies import ApiDependencies
from .errors import (
    authentication_error_type,
    foundation_error_types,
    foundation_exception_handler,
)
from .middleware import (
    ExceptionMiddleware,
    ObservabilityMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    SecurityHeadersMiddleware,
)
from .models import ApiListResponse, ApiResourceResponse
from .openapi import openapi_metadata
from .prometheus import prometheus_endpoint
from .routers import (
    get_package_endpoint,
    get_publisher_endpoint,
    get_registry_endpoint,
    get_version_endpoint,
    health_endpoint,
    list_package_endpoint,
    list_publisher_endpoint,
    list_registry_endpoint,
    list_version_endpoint,
    metadata_endpoint,
    search_endpoint,
    statistics_endpoint,
    version_endpoint,
)
from .routers.agent import (
    create_endpoint as create_agent_endpoint,
)
from .routers.agent import (
    delete_run_endpoint as delete_agent_run_endpoint,
)
from .routers.agent import (
    get_run_endpoint as get_agent_run_endpoint,
)
from .routers.agent import (
    list_endpoint as list_agent_endpoint,
)
from .routers.agent import (
    run_endpoint as run_agent_endpoint,
)
from .routers.enterprise import register_routes as register_enterprise_routes


def create_app(
    *,
    dependencies: ApiDependencies | None = None,
    app_factory: Callable[..., Any] | None = None,
    production_runtime: ProductionRuntime | None = None,
    plugin_marketplace: EnterprisePluginMarketplace | None = None,
    enterprise_marketplace: EnterpriseMarketplace | None = None,
) -> Any:
    """Create an isolated FastAPI application with only read-only endpoints.

    FastAPI remains an optional host dependency. Tests and embedding callers can
    inject a compatible factory; this module never starts a server or performs
    network I/O.
    """
    selected = dependencies or ApiDependencies.create()
    runtime = production_runtime or ProductionRuntime(
        ProductionConfigurationLoader.load(environment=environ),
        closers=_dependency_closers(selected),
    )
    fastapi_module = _fastapi_module() if app_factory is None else None
    factory = (
        cast(Callable[..., Any], fastapi_module.FastAPI)
        if fastapi_module is not None
        else app_factory
    )
    if factory is None:
        raise RuntimeError("An HTTP application factory is required.")
    app = factory(
        **openapi_metadata(selected.server_config),
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    _attach_dependencies(app, selected)
    _attach_production_runtime(app, runtime)
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware, runtime=runtime)
    app.add_middleware(RateLimitMiddleware, runtime=runtime)
    app.add_middleware(ObservabilityMiddleware, runtime=runtime)
    for error_type in (*foundation_error_types(), authentication_error_type()):
        app.add_exception_handler(error_type, foundation_exception_handler)
    register_auth_routes(
        app,
        selected.authentication_service,
        fastapi_module=fastapi_module,
    )
    register_enterprise_routes(
        app, selected.enterprise_service, selected.authentication_service
    )
    plugins = plugin_marketplace or EnterprisePluginMarketplace()
    register_plugin_routes(app, plugins)
    store = enterprise_marketplace or EnterpriseMarketplace()
    marketplace_api = MarketplaceApi(store)
    for path, endpoint in (
        ("/marketplace", marketplace_api.catalog),
        ("/licenses", marketplace_api.licenses),
        ("/reviews", marketplace_api.reviews),
        ("/downloads", marketplace_api.downloads),
    ):
        app.add_api_route(path, endpoint, methods=["GET"], tags=["marketplace"])
    register_enterprise_platform_routes(app, EnterprisePlatform())
    application_center = ApplicationCenter()
    register_application_routes(app, application_center)
    app.state.application_center = application_center
    knowledge_platform = KnowledgePlatform()
    register_knowledge_routes(app, knowledge_platform)
    app.state.knowledge_platform = knowledge_platform
    knowledge_graph = KnowledgeGraphPlatform()
    register_knowledge_graph_routes(app, knowledge_graph)
    app.state.knowledge_graph = knowledge_graph
    workflow_platform = WorkflowPlatform()
    register_workflow_routes(app, workflow_platform)
    app.state.workflow_platform = workflow_platform
    app_store = EnterpriseAppStore()
    register_app_store_routes(app, app_store)
    app.state.app_store = app_store
    api_management = ApiManagementPlatform()
    register_api_management_routes(app, api_management)
    app.state.api_management = api_management
    orchestrator = EnterpriseAIOrchestrator()
    register_orchestrator_routes(app, orchestrator)
    app.state.orchestrator = orchestrator
    memory_engine = EnterpriseAIMemoryEngine()
    dashboard_memory_scope = MemoryScope("default", "default", "dashboard")
    memory_engine.security.grant(
        dashboard_memory_scope,
        {"memory:read", "memory:write", "memory:delete", "memory:retention"},
    )
    register_memory_routes(app, memory_engine)
    app.state.memory_engine = memory_engine
    reasoning_engine = EnterpriseAIReasoningEngine()
    dashboard_reasoning_scope = ReasoningScope("default", "default", "dashboard")
    reasoning_engine.security.grant(
        dashboard_reasoning_scope,
        {
            "reasoning:read",
            "reasoning:write",
            "reasoning:execute",
            "reasoning:plan",
            "reasoning:decide",
            "reasoning:validate",
            "reasoning:simulate",
            "reasoning:optimize",
        },
    )
    register_reasoning_routes(app, reasoning_engine)
    app.state.reasoning_engine = reasoning_engine
    collaboration = EnterpriseAICollaborationPlatform()
    dashboard_collaboration_scope = CollaborationScope(
        "default", "default", "dashboard"
    )
    collaboration.security.grant(
        dashboard_collaboration_scope,
        {
            "collaboration:admin",
            "collaboration:read",
            "collaboration:write",
            "collaboration:message",
            "collaboration:memory:read",
            "collaboration:memory:write",
            "collaboration:task",
            "collaboration:handoff",
        },
    )
    collaboration.create_workspace(
        {
            "id": "default",
            "organization": "default",
            "name": "Default Workspace",
            "members": ["dashboard"],
            "roles": {"dashboard": "administrator"},
        },
        dashboard_collaboration_scope,
    )
    register_collaboration_routes(app, collaboration)
    app.state.collaboration = collaboration
    governance = EnterpriseAIGovernancePlatform()
    dashboard_governance_scope = GovernanceScope("default", "default", "dashboard")
    governance.security.grant(
        dashboard_governance_scope,
        {
            "governance:read",
            "governance:report:read",
            "governance:report:export",
        },
    )
    register_governance_routes(app, governance)
    app.state.governance = governance
    data_platform = DataPlatform()
    register_data_routes(app, data_platform)
    app.state.data_platform = data_platform
    model_platform = ModelPlatform()
    dashboard_model_scope = ModelScope("default", "default", "dashboard")
    model_platform.security.grant(
        dashboard_model_scope,
        {
            "models:admin",
            "models:read",
            "models:write",
            "models:approve",
            "models:route",
            "models:deploy",
            "models:evaluate",
            "models:govern",
            "models:invoke",
        },
    )
    register_model_routes(app, model_platform)
    app.state.model_platform = model_platform
    security_platform = SecurityPlatform()
    register_security_routes(app, security_platform)
    app.state.security_platform = security_platform
    command_center = CommandCenterPlatform()
    register_command_center_routes(app, command_center)
    app.state.command_center = command_center
    register_local_runtime_routes(app)
    tiktok_account_center = TikTokAccountCenter()
    register_tiktok_routes(app, tiktok_account_center)
    app.state.tiktok_account_center = tiktok_account_center
    tiktok_browser_runtime = TikTokBrowserRuntime(
        account_status=AccountCenterStatusAdapter(tiktok_account_center)
    )
    register_browser_runtime_routes(app, tiktok_browser_runtime)
    app.state.tiktok_browser_runtime = tiktok_browser_runtime
    tiktok_browser_cluster = TikTokBrowserCluster()
    register_browser_cluster_routes(app, tiktok_browser_cluster)
    app.state.tiktok_browser_cluster = tiktok_browser_cluster
    tiktok_device_center = TikTokDeviceCenter()
    register_device_center_routes(app, tiktok_device_center)
    app.state.tiktok_device_center = tiktok_device_center
    tiktok_proxy_center = TikTokProxyCenter()
    register_proxy_center_routes(app, tiktok_proxy_center)
    app.state.tiktok_proxy_center = tiktok_proxy_center
    app.state.tiktok_browser_proxy_port = BrowserRuntimeProxyAdapter(
        tiktok_proxy_center
    )
    tiktok_account_farming = TikTokAccountFarming(
        accounts=BoundedAccountCenterAdapter(tiktok_account_center),
        browsers=ExistingBrowserRuntimeAdapter(tiktok_browser_runtime),
        proxies=ExistingProxyCenterAdapter(tiktok_proxy_center),
    )
    register_account_farming_routes(app, tiktok_account_farming)
    app.state.tiktok_account_farming = tiktok_account_farming
    tiktok_content_center = TikTokContentCenter(
        accounts=ContentAccountAdapter(tiktok_account_center),
        browsers=ContentBrowserAdapter(tiktok_browser_runtime),
        proxies=ContentProxyAdapter(tiktok_proxy_center),
        farming=ExistingFarmingAdapter(tiktok_account_farming),
    )
    register_content_center_routes(app, tiktok_content_center)
    app.state.tiktok_content_center = tiktok_content_center
    tiktok_publishing_center = TikTokPublishingCenter(
        content=ExistingContentCenterAdapter(tiktok_content_center),
        accounts=PublishingAccountAdapter(tiktok_account_center),
        publisher=ExistingBrowserPublisher(tiktok_browser_runtime),
        proxy_policy=ExistingProxyPolicy(tiktok_proxy_center),
        farming_policy=ExistingFarmingPolicy(tiktok_account_farming),
    )
    register_publishing_center_routes(app, tiktok_publishing_center)
    app.state.tiktok_publishing_center = tiktok_publishing_center
    tiktok_data_collection_center = TikTokDataCollectionCenter(
        accounts=DataAccountAdapter(tiktok_account_center),
        proxies=DataProxyAdapter(tiktok_proxy_center),
    )
    register_data_collection_routes(app, tiktok_data_collection_center)
    app.state.tiktok_data_collection_center = tiktok_data_collection_center
    tiktok_interaction_center = TikTokInteractionCenter()
    register_interaction_routes(app, tiktok_interaction_center)
    app.state.tiktok_interaction_center = tiktok_interaction_center
    tiktok_risk_control_center = TikTokRiskControlCenter()
    register_risk_control_routes(app, tiktok_risk_control_center)
    app.state.tiktok_risk_control_center = tiktok_risk_control_center
    tiktok_workflow_center = TikTokWorkflowOrchestrationCenter()
    register_workflow_center_routes(app, tiktok_workflow_center)
    app.state.tiktok_workflow_center = tiktok_workflow_center
    tiktok_operations_center = TikTokOperationsCommandCenter()
    register_operations_center_routes(app, tiktok_operations_center)
    app.state.tiktok_operations_center = tiktok_operations_center
    tiktok_analytics_center = TikTokAIAnalyticsCenter()
    register_analytics_center_routes(app, tiktok_analytics_center)
    app.state.tiktok_analytics_center = tiktok_analytics_center
    agent_api = AgentApi(selected.agent_runtime)
    app.add_api_route(
        "/agents", create_agent_endpoint(agent_api), methods=["POST"], tags=["agents"]
    )
    app.add_api_route(
        "/agents", list_agent_endpoint(agent_api), methods=["GET"], tags=["agents"]
    )
    app.add_api_route(
        "/agents/run",
        run_agent_endpoint(agent_api),
        methods=["POST"],
        tags=["agents"],
    )
    app.add_api_route(
        "/agents/run/{run_id}",
        get_agent_run_endpoint(agent_api),
        methods=["GET"],
        tags=["agents"],
    )
    app.add_api_route(
        "/agents/run/{run_id}",
        delete_agent_run_endpoint(agent_api),
        methods=["DELETE"],
        tags=["agents"],
    )
    app.add_api_route(
        "/health", health_endpoint(selected), methods=["GET"], tags=["health"]
    )
    app.add_api_route(
        "/health/live",
        lambda: runtime.health.snapshot().to_dict(),
        methods=["GET"],
        tags=["health"],
    )
    app.add_api_route(
        "/health/ready",
        lambda: runtime.health.snapshot().to_dict(),
        methods=["GET"],
        tags=["health"],
    )
    app.add_api_route(
        "/health/startup",
        lambda: runtime.health.snapshot().to_dict(),
        methods=["GET"],
        tags=["health"],
    )
    app.add_api_route(
        "/metrics",
        prometheus_endpoint(
            runtime,
            selected.agent_runtime.metrics,
            plugins.metrics,
            store.metrics,
            application_center.metrics,
            knowledge_platform.metrics,
            knowledge_graph.metrics,
            workflow_platform.metrics,
            orchestrator.metrics,
            memory_engine.metrics,
            reasoning_engine.metrics,
            collaboration.metrics,
            governance.metrics,
            model_platform.metrics,
            security_platform.metrics,
            command_center.metrics,
        ),
        methods=["GET"],
        tags=["operations"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/version", version_endpoint(selected), methods=["GET"], tags=["server"]
    )
    app.add_api_route(
        "/metadata", metadata_endpoint(selected), methods=["GET"], tags=["server"]
    )
    app.add_api_route(
        "/registry",
        list_registry_endpoint(selected),
        methods=["GET"],
        tags=["registry"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/registry/{registry_id}",
        get_registry_endpoint(selected),
        methods=["GET"],
        tags=["registry"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/publishers",
        list_publisher_endpoint(selected),
        methods=["GET"],
        tags=["publisher"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/publishers/{publisher_id}",
        get_publisher_endpoint(selected),
        methods=["GET"],
        tags=["publisher"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/packages",
        list_package_endpoint(selected),
        methods=["GET"],
        tags=["package"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/packages/{package_id}",
        get_package_endpoint(selected),
        methods=["GET"],
        tags=["package"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/versions",
        list_version_endpoint(selected),
        methods=["GET"],
        tags=["version"],
        response_model=ApiListResponse,
    )
    app.add_api_route(
        "/versions/{version_id}",
        get_version_endpoint(selected),
        methods=["GET"],
        tags=["version"],
        response_model=ApiResourceResponse,
    )
    app.add_api_route(
        "/search", search_endpoint(selected), methods=["GET"], tags=["search"]
    )
    app.add_api_route(
        "/statistics",
        statistics_endpoint(selected),
        methods=["GET"],
        tags=["statistics"],
    )
    return app


def _fastapi_module() -> ModuleType:
    """Load FastAPI only when a real HTTP application is explicitly requested."""
    try:
        return cast(ModuleType, import_module("fastapi"))
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "FastAPI is required to create the Marketplace Server HTTP application."
        ) from error


def _attach_dependencies(app: Any, dependencies: ApiDependencies) -> None:
    """Attach dependencies to this app only; no process-wide singleton is used."""
    if not hasattr(app, "state"):
        app.state = type("ApiState", (), {})()
    app.state.api_dependencies = dependencies


def _attach_production_runtime(app: Any, runtime: ProductionRuntime) -> None:
    """Attach and lifecycle-manage runtime state on this app instance only."""
    if not hasattr(app, "state"):
        app.state = type("ApiState", (), {})()
    app.state.production_runtime = runtime
    if hasattr(app, "add_event_handler"):
        app.add_event_handler("startup", runtime.start)
        app.add_event_handler("shutdown", runtime.close)


def _dependency_closers(
    dependencies: ApiDependencies,
) -> tuple[Callable[[], None], ...]:
    """Collect explicit service close methods without modifying Foundation contracts."""
    services = (
        dependencies.health_service,
        dependencies.authentication_service,
        dependencies.registry_service,
        dependencies.publisher_service,
        dependencies.package_service,
        dependencies.version_service,
        dependencies.search_service,
        dependencies.statistics_service,
        dependencies.agent_runtime,
    )
    closers: list[Callable[[], None]] = []
    for service in services:
        close = getattr(service, "close", None)
        if callable(close):
            closers.append(cast(Callable[[], None], close))
    return tuple(closers)
