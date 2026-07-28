import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";
import { ErrorBoundary, Header, Sidebar } from "./components";
import {
  AgentDefinitionsPage, AgentRunDetailsPage, AgentRunsPage,
  ApplicationDeploymentsPage, ApplicationPermissionsPage, ApplicationsPage,
  ApplicationTemplatesPage, ApplicationUsagePage, ApplicationVersionsPage,
  AppStorePage,
  CollectionsPage, DocumentsPage, KnowledgeBasesPage, KnowledgeStatusPage,
  dashboardPages, memoryDashboardPages, reasoningDashboardPages, collaborationDashboardPages, governanceDashboardPages, modelDashboardPages, securityDashboardPages, apiManagementDashboardPages, integrationHubDashboardPages, digitalTwinDashboardPages, businessIntelligenceDashboardPages, commandCenterDashboardPages, knowledgeGraphDashboardPages, tiktokDashboardPages, DashboardHome, DownloadsPage, EnterprisePage, HealthPage, TikTokInteractionCenterPage, TikTokRiskControlCenterPage, TikTokOperationsCenterPage, TikTokResourceCenterPage, TikTokAutomationEnginePage, TikTokExecutionEnginePage, TikTokAIControlTowerPage, TikTokLocalRuntimePage,
  LicensesPage, LoginPage, MarketplacePage, NotFoundPage, PackagesPage,
  PluginDetailsPage, PluginPermissionsPage, PluginsPage, PublishersPage,
  RegistryPage, ReviewsPage, SearchPage, StatisticsPage, VersionsPage,
  MemoryPage, OrchestratorPage, ReasoningPage, CollaborationPage, GovernancePage, ModelPlatformPage, SecurityPlatformPage, ApiManagementPage, IntegrationHubPage, DigitalTwinPage, BusinessIntelligencePage, CommandCenterPage, KnowledgeGraphPage, TikTokAccountCenterPage, TikTokBrowserRuntimePage, TikTokBrowserClusterPage, TikTokDeviceCenterPage, TikTokProxyCenterPage, TikTokPublishingCenterPage, TikTokCreatorWorkspacePage, TikTokDataCollectionPage,
} from "./pages";

function Shell() {
  const { token, logout } = useAuth(); const navigate = useNavigate();
  if (!token) return <Navigate to="/login" replace />;
  return <div className="dashboard-shell"><Sidebar pages={[...dashboardPages, ...memoryDashboardPages, ...reasoningDashboardPages, ...collaborationDashboardPages, ...governanceDashboardPages, ...modelDashboardPages, ...securityDashboardPages, ...apiManagementDashboardPages, ...integrationHubDashboardPages, ...digitalTwinDashboardPages, ...businessIntelligenceDashboardPages, ...commandCenterDashboardPages, ...knowledgeGraphDashboardPages, ...tiktokDashboardPages]} /><main><Header onLogout={() => { logout().finally(() => navigate("/login")); }} /><ErrorBoundary><Outlet /></ErrorBoundary></main></div>;
}

export function App() {
  return <Routes><Route path="/login" element={<LoginPage />} /><Route element={<Shell />}>
    <Route path="/dashboard" element={<DashboardHome />} />
    <Route path="/tiktok-account-center" element={<TikTokAccountCenterPage />} />
    <Route path="/tiktok-browser-runtime" element={<TikTokBrowserRuntimePage />} />
    <Route path="/tiktok-browser-cluster" element={<TikTokBrowserClusterPage />} />
    <Route path="/tiktok-device-center" element={<TikTokDeviceCenterPage />} />
    <Route path="/tiktok-proxy-center" element={<TikTokProxyCenterPage />} />
    <Route path="/tiktok-ai-publishing-center" element={<TikTokPublishingCenterPage />} />
    <Route path="/tiktok-creator-workspace" element={<TikTokCreatorWorkspacePage />} />
    <Route path="/tiktok-data-collection" element={<TikTokDataCollectionPage />} />
    <Route path="/tiktok-ai-interaction-center" element={<TikTokInteractionCenterPage />} />
    <Route path="/tiktok-ai-risk-control-center" element={<TikTokRiskControlCenterPage />} />
    <Route path="/tiktok-operations-command-center" element={<TikTokOperationsCenterPage />} />
    <Route path="/tiktok-resource-center" element={<TikTokResourceCenterPage />} />
    <Route path="/tiktok-ai-automation-engine" element={<TikTokAutomationEnginePage />} />
    <Route path="/tiktok-ai-execution-engine" element={<TikTokExecutionEnginePage />} />
    <Route path="/tiktok-ai-control-tower" element={<TikTokAIControlTowerPage />} />
    <Route path="/tiktok-local-runtime" element={<TikTokLocalRuntimePage />} />
    <Route path="/collaboration" element={<CollaborationPage />} />
    <Route path="/collaboration-teams" element={<CollaborationPage title="Teams" />} />
    <Route path="/collaboration-projects" element={<CollaborationPage title="Projects" />} />
    <Route path="/collaboration-sessions" element={<CollaborationPage title="Sessions" />} />
    <Route path="/collaboration-tasks" element={<CollaborationPage title="Tasks" />} />
    <Route path="/collaboration-timeline" element={<CollaborationPage title="Timeline" />} />
    <Route path="/collaboration-activity" element={<CollaborationPage title="Activity" />} />
    <Route path="/collaboration-notifications" element={<CollaborationPage title="Notifications" />} />
    <Route path="/governance" element={<GovernancePage />} />
    <Route path="/governance-policies" element={<GovernancePage title="Policies" />} />
    <Route path="/governance-risks" element={<GovernancePage title="Risk Register" />} />
    <Route path="/governance-compliance" element={<GovernancePage title="Compliance" />} />
    <Route path="/governance-approvals" element={<GovernancePage title="Approvals" />} />
    <Route path="/governance-controls" element={<GovernancePage title="Controls" />} />
    <Route path="/governance-models" element={<GovernancePage title="Models" />} />
    <Route path="/governance-prompts" element={<GovernancePage title="Prompts" />} />
    <Route path="/governance-agents" element={<GovernancePage title="Agents" />} />
    <Route path="/governance-applications" element={<GovernancePage title="Applications" />} />
    <Route path="/governance-workflows" element={<GovernancePage title="Workflows" />} />
    <Route path="/governance-data" element={<GovernancePage title="Data" />} />
    <Route path="/governance-incidents" element={<GovernancePage title="Incidents" />} />
    <Route path="/governance-exceptions" element={<GovernancePage title="Exceptions" />} />
    <Route path="/governance-reports" element={<GovernancePage title="Reports" />} />
    <Route path="/model-platform" element={<ModelPlatformPage />} />
    <Route path="/models" element={<ModelPlatformPage title="Model Registry" resource="models" />} />
    <Route path="/model-providers" element={<ModelPlatformPage title="Providers" resource="model-providers" />} />
    <Route path="/model-profiles" element={<ModelPlatformPage title="Profiles" resource="model-profiles" />} />
    <Route path="/model-deployments" element={<ModelPlatformPage title="Deployments" resource="model-deployments" />} />
    <Route path="/model-routing" element={<ModelPlatformPage title="Routing" resource="model-routing" />} />
    <Route path="/model-fallback" element={<ModelPlatformPage title="Fallback" resource="model-fallback" />} />
    <Route path="/model-evaluations" element={<ModelPlatformPage title="Evaluation" resource="model-evaluations" />} />
    <Route path="/model-benchmarks" element={<ModelPlatformPage title="Benchmarks" resource="model-benchmarks" />} />
    <Route path="/model-usage" element={<ModelPlatformPage title="Usage" resource="model-usage" />} />
    <Route path="/model-cost" element={<ModelPlatformPage title="Cost" resource="model-cost" />} />
    <Route path="/model-governance" element={<ModelPlatformPage title="Governance" resource="model-governance" />} />
    <Route path="/security" element={<SecurityPlatformPage />} />
    <Route path="/security-identity" element={<SecurityPlatformPage title="Identity" resource="identity" />} />
    <Route path="/security-authentication" element={<SecurityPlatformPage title="Authentication" />} />
    <Route path="/security-authorization" element={<SecurityPlatformPage title="Authorization" />} />
    <Route path="/security-secrets" element={<SecurityPlatformPage title="Secrets" resource="secrets" />} />
    <Route path="/security-threats" element={<SecurityPlatformPage title="Threats" />} />
    <Route path="/security-incidents" element={<SecurityPlatformPage title="Incidents" resource="incidents" />} />
    <Route path="/security-compliance" element={<SecurityPlatformPage title="Compliance" resource="compliance" />} />
    <Route path="/security-audit" element={<SecurityPlatformPage title="Audit" />} />
    <Route path="/api-management" element={<ApiManagementPage />} />
    <Route path="/api-management-apis" element={<ApiManagementPage title="APIs" resource="apis" />} />
    <Route path="/api-management-gateways" element={<ApiManagementPage title="Gateways" resource="gateways" />} />
    <Route path="/api-management-routes" element={<ApiManagementPage title="Routes" resource="routes" />} />
    <Route path="/api-management-versions" element={<ApiManagementPage title="Versions" resource="versions" />} />
    <Route path="/api-management-policies" element={<ApiManagementPage title="Policies" resource="policies" />} />
    <Route path="/api-management-credentials" element={<ApiManagementPage title="Credentials" resource="keys" />} />
    <Route path="/api-management-rate-limits" element={<ApiManagementPage title="Rate Limits" resource="rate-limits" />} />
    <Route path="/api-management-quotas" element={<ApiManagementPage title="Quotas" resource="quotas" />} />
    <Route path="/api-management-subscriptions" element={<ApiManagementPage title="Subscriptions" resource="subscriptions" />} />
    <Route path="/api-management-analytics" element={<ApiManagementPage title="Analytics" resource="analytics" />} />
    <Route path="/api-management-developer-portal" element={<ApiManagementPage title="Developer Portal" resource="developer-portal" />} />
    <Route path="/integration-hub" element={<IntegrationHubPage />} />
    <Route path="/integration-hub-catalog" element={<IntegrationHubPage title="Integration Catalog" resource="catalog" />} />
    <Route path="/integration-hub-instances" element={<IntegrationHubPage title="Connector Instances" resource="instances" />} />
    <Route path="/integration-hub-mappings" element={<IntegrationHubPage title="Mappings" resource="mappings" />} />
    <Route path="/integration-hub-flows" element={<IntegrationHubPage title="Integration Flows" resource="flows" />} />
    <Route path="/integration-hub-credentials" element={<IntegrationHubPage title="Credentials" resource="credentials" />} />
    <Route path="/integration-hub-health" element={<IntegrationHubPage title="Connector Health" resource="health" />} />
    <Route path="/integration-hub-schedules" element={<IntegrationHubPage title="Schedules" resource="schedules" />} />
    <Route path="/integration-hub-failures" element={<IntegrationHubPage title="Failures" resource="failures" />} />
    <Route path="/integration-hub-dead-letter" element={<IntegrationHubPage title="Dead Letter" resource="dead-letter" />} />
    <Route path="/integration-hub-analytics" element={<IntegrationHubPage title="Integration Analytics" resource="analytics" />} />
    <Route path="/digital-twins" element={<DigitalTwinPage />} />
    <Route path="/twin-topology" element={<DigitalTwinPage title="Twin Topology" resource="entities" />} />
    <Route path="/twin-telemetry" element={<DigitalTwinPage title="Twin Telemetry" resource="state" />} />
    <Route path="/twin-simulation" element={<DigitalTwinPage title="Twin Simulation" resource="simulation" />} />
    <Route path="/twin-predictions" element={<DigitalTwinPage title="Twin Predictions" resource="predictions" />} />
    <Route path="/twin-optimization" element={<DigitalTwinPage title="Twin Optimization" resource="optimization" />} />
    <Route path="/business-intelligence-workspaces" element={<BusinessIntelligencePage title="BI Workspaces" />} />
    <Route path="/business-intelligence-data-sources" element={<BusinessIntelligencePage title="BI Data Sources" resource="data-sources" />} />
    <Route path="/business-intelligence-datasets" element={<BusinessIntelligencePage title="BI Datasets" resource="datasets" />} />
    <Route path="/business-intelligence-semantic-models" element={<BusinessIntelligencePage title="Semantic Models" resource="semantic-models" />} />
    <Route path="/business-intelligence-metrics" element={<BusinessIntelligencePage title="BI Metrics" resource="metrics" />} />
    <Route path="/business-intelligence-reports" element={<BusinessIntelligencePage title="BI Reports" resource="reports" />} />
    <Route path="/business-intelligence-dashboards" element={<BusinessIntelligencePage title="BI Dashboards" resource="dashboards" />} />
    <Route path="/business-intelligence-insights" element={<BusinessIntelligencePage title="BI Insights" resource="insights" />} />
    <Route path="/business-intelligence-alerts" element={<BusinessIntelligencePage title="BI Alerts" resource="alerts" />} />
    <Route path="/business-intelligence-subscriptions" element={<BusinessIntelligencePage title="BI Subscriptions" resource="subscriptions" />} />
    <Route path="/business-intelligence-governance" element={<BusinessIntelligencePage title="BI Governance" resource="governance" />} />
    <Route path="/command-center" element={<CommandCenterPage />} />
    <Route path="/command-center-operations" element={<CommandCenterPage title="Live Operations" resource="operations" />} />
    <Route path="/command-center-agents" element={<CommandCenterPage title="Agents" resource="topology" />} />
    <Route path="/command-center-automation" element={<CommandCenterPage title="Automation" resource="tasks" />} />
    <Route path="/command-center-incidents" element={<CommandCenterPage title="Incidents" resource="incidents" />} />
    <Route path="/command-center-alerts" element={<CommandCenterPage title="Alerts" resource="alerts" />} />
    <Route path="/command-center-topology" element={<CommandCenterPage title="Topology" resource="topology" />} />
    <Route path="/command-center-health" element={<CommandCenterPage title="Health" resource="health" />} />
    <Route path="/command-center-activity" element={<CommandCenterPage title="Activity" resource="activity" />} />
    <Route path="/command-center-audit" element={<CommandCenterPage title="Audit" resource="activity" />} />
    <Route path="/knowledge-graphs" element={<KnowledgeGraphPage />} />
    <Route path="/knowledge-graph-entities" element={<KnowledgeGraphPage title="Knowledge Entities" resource="entities" />} />
    <Route path="/knowledge-graph-relationships" element={<KnowledgeGraphPage title="Knowledge Relationships" resource="relationships" />} />
    <Route path="/knowledge-graph-ontology" element={<KnowledgeGraphPage title="Ontology" resource="ontology" />} />
    <Route path="/knowledge-graph-taxonomy" element={<KnowledgeGraphPage title="Taxonomy" resource="taxonomy" />} />
    <Route path="/knowledge-graph-lineage" element={<KnowledgeGraphPage title="Lineage" resource="lineage" />} />
    <Route path="/knowledge-graph-analytics" element={<KnowledgeGraphPage title="Graph Analytics" resource="analytics" />} />
    <Route path="/knowledge-graph-queries" element={<KnowledgeGraphPage title="Graph Queries" resource="queries" />} />
    <Route path="/memory" element={<MemoryPage />} />
    <Route path="/reasoning" element={<ReasoningPage />} />
    <Route path="/reasoning-plans" element={<ReasoningPage title="Plans" />} />
    <Route path="/reasoning-decisions" element={<ReasoningPage title="Decisions" />} />
    <Route path="/reasoning-strategies" element={<ReasoningPage title="Strategies" />} />
    <Route path="/reasoning-validation" element={<ReasoningPage title="Validation" />} />
    <Route path="/reasoning-metrics" element={<ReasoningPage title="Metrics" />} />
    <Route path="/memory-namespaces" element={<MemoryPage title="Namespaces" resource="namespaces" />} />
    <Route path="/memory-usage" element={<MemoryPage title="Usage" />} />
    <Route path="/memory-retention" element={<MemoryPage title="Retention" />} />
    <Route path="/memory-cache" element={<MemoryPage title="Cache" resource="cache" />} />
    <Route path="/memory-retrieval" element={<MemoryPage title="Retrieval" />} />
    <Route path="/memory-metrics" element={<MemoryPage title="Metrics" />} />
    <Route path="/orchestrator" element={<OrchestratorPage />} />
    <Route path="/execution-plans" element={<OrchestratorPage title="Execution Plans" />} />
    <Route path="/orchestrator-queues" element={<OrchestratorPage title="Queues" />} />
    <Route path="/orchestrator-executions" element={<OrchestratorPage title="Executions" />} />
    <Route path="/orchestrator-failures" element={<OrchestratorPage title="Failures" />} />
    <Route path="/orchestrator-retries" element={<OrchestratorPage title="Retries" />} />
    <Route path="/orchestrator-performance" element={<OrchestratorPage title="Performance" />} />
    <Route path="/applications" element={<ApplicationsPage />} />
    <Route path="/app-store" element={<AppStorePage title="Store Home" />} />
    <Route path="/app-store-categories" element={<AppStorePage title="Categories" resource="applications" />} />
    <Route path="/app-store-details" element={<AppStorePage title="Application Details" resource="applications" />} />
    <Route path="/app-store-installed" element={<AppStorePage title="Installed Applications" resource="installations" />} />
    <Route path="/app-store-updates" element={<AppStorePage title="App Store Updates" resource="updates" />} />
    <Route path="/app-store-licenses" element={<AppStorePage title="App Store Licenses" resource="licenses" />} />
    <Route path="/app-store-subscriptions" element={<AppStorePage title="Subscriptions" resource="subscriptions" />} />
    <Route path="/app-store-publishers" element={<AppStorePage title="App Store Publishers" resource="publishers" />} />
    <Route path="/app-store-reviews" element={<AppStorePage title="App Store Reviews" resource="reviews" />} />
    <Route path="/app-store-moderation" element={<AppStorePage title="Moderation" resource="moderation" />} />
    <Route path="/app-store-analytics" element={<AppStorePage title="App Store Analytics" />} />
    <Route path="/application-templates" element={<ApplicationTemplatesPage />} />
    <Route path="/deployments" element={<ApplicationDeploymentsPage />} />
    <Route path="/application-usage" element={<ApplicationUsagePage />} />
    <Route path="/application-versions" element={<ApplicationVersionsPage />} />
    <Route path="/application-permissions" element={<ApplicationPermissionsPage />} />
    <Route path="/knowledge-bases" element={<KnowledgeBasesPage />} />
    <Route path="/collections" element={<CollectionsPage />} />
    <Route path="/documents" element={<DocumentsPage />} />
    <Route path="/ingestion" element={<KnowledgeStatusPage title="Ingestion Jobs" />} />
    <Route path="/knowledge-search" element={<KnowledgeStatusPage title="Knowledge Search" />} />
    <Route path="/knowledge-permissions" element={<KnowledgeStatusPage title="Knowledge Permissions" />} />
    <Route path="/connectors" element={<KnowledgeStatusPage title="Connectors" />} />
    <Route path="/evaluation" element={<KnowledgeStatusPage title="Evaluation" />} />
    <Route path="/agents" element={<AgentDefinitionsPage />} />
    <Route path="/agent-runs" element={<AgentRunsPage />} />
    <Route path="/agent-runs/:id" element={<AgentRunDetailsPage />} />
    <Route path="/plugins" element={<PluginsPage />} />
    <Route path="/marketplace" element={<MarketplacePage />} />
    <Route path="/installed" element={<PluginsPage title="Installed Plugins" />} />
    <Route path="/updates" element={<PluginsPage title="Plugin Updates" />} />
    <Route path="/plugins/:id" element={<PluginDetailsPage />} />
    <Route path="/plugins/:id/permissions" element={<PluginPermissionsPage />} />
    <Route path="/registry" element={<RegistryPage />} />
    <Route path="/publishers" element={<PublishersPage />} />
    <Route path="/packages" element={<PackagesPage />} />
    <Route path="/downloads" element={<DownloadsPage />} />
    <Route path="/licenses" element={<LicensesPage />} />
    <Route path="/reviews" element={<ReviewsPage />} />
    <Route path="/versions" element={<VersionsPage />} />
    <Route path="/search" element={<SearchPage />} />
    <Route path="/statistics" element={<StatisticsPage />} />
    <Route path="/health" element={<HealthPage />} />
    <EnterpriseRoutes />
  </Route><Route path="/" element={<Navigate to="/dashboard" replace />} /><Route path="*" element={<NotFoundPage />} /></Routes>;
}

export function EnterpriseRoutes() {
  const { client } = useAuth();
  return <><Route path="/users" element={<EnterprisePage title="Users" load={() => client.users()} />} /><Route path="/organizations" element={<EnterprisePage title="Organizations" load={() => client.organizations()} />} /><Route path="/tenants" element={<EnterprisePage title="Tenants" load={() => client.enterprise("tenants")} />} /><Route path="/teams" element={<EnterprisePage title="Teams" load={() => client.teams()} />} /><Route path="/roles" element={<EnterprisePage title="Roles" load={() => client.roles()} />} /><Route path="/permissions" element={<EnterprisePage title="Permissions" load={() => client.enterprise("permissions")} />} /><Route path="/license" element={<EnterprisePage title="License" load={() => client.enterprise("license")} />} /><Route path="/billing" element={<EnterprisePage title="Billing" load={() => client.enterprise("billing")} />} /><Route path="/api-keys" element={<EnterprisePage title="API Keys" load={() => client.apiKeys()} />} /><Route path="/audit" element={<EnterprisePage title="Audit Logs" load={() => client.audit()} />} /></>;
}
