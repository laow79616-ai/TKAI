import { Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth";
import { ErrorBoundary, Header, Sidebar } from "./components";
import {
  AgentDefinitionsPage, AgentRunDetailsPage, AgentRunsPage,
  ApplicationDeploymentsPage, ApplicationPermissionsPage, ApplicationsPage,
  ApplicationTemplatesPage, ApplicationUsagePage, ApplicationVersionsPage,
  AppStorePage,
  CollectionsPage, DocumentsPage, KnowledgeBasesPage, KnowledgeStatusPage,
  dashboardPages, memoryDashboardPages, reasoningDashboardPages, DashboardHome, DownloadsPage, EnterprisePage, HealthPage,
  LicensesPage, LoginPage, MarketplacePage, NotFoundPage, PackagesPage,
  PluginDetailsPage, PluginPermissionsPage, PluginsPage, PublishersPage,
  RegistryPage, ReviewsPage, SearchPage, StatisticsPage, VersionsPage,
  MemoryPage, OrchestratorPage, ReasoningPage,
} from "./pages";

function Shell() {
  const { token, logout } = useAuth(); const navigate = useNavigate();
  if (!token) return <Navigate to="/login" replace />;
  return <div className="dashboard-shell"><Sidebar pages={[...dashboardPages, ...memoryDashboardPages, ...reasoningDashboardPages]} /><main><Header onLogout={() => { logout().finally(() => navigate("/login")); }} /><ErrorBoundary><Outlet /></ErrorBoundary></main></div>;
}

export function App() {
  return <Routes><Route path="/login" element={<LoginPage />} /><Route element={<Shell />}>
    <Route path="/dashboard" element={<DashboardHome />} />
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
