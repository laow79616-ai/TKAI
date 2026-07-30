import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { type ApiListResponse, type EnterpriseRecord, type SearchEntry } from "./api";
import { useAuth } from "./auth";
import { Card, Loading, SearchBar, Table } from "./components";

export const dashboardPages = ["dashboard", "orchestrator", "execution-plans", "orchestrator-queues", "orchestrator-executions", "orchestrator-failures", "orchestrator-retries", "orchestrator-performance", "app-store", "app-store-categories", "app-store-details", "app-store-installed", "app-store-updates", "app-store-licenses", "app-store-subscriptions", "app-store-publishers", "app-store-reviews", "app-store-moderation", "app-store-analytics", "knowledge-bases", "collections", "documents", "ingestion", "knowledge-search", "knowledge-permissions", "connectors", "evaluation", "applications", "application-templates", "deployments", "application-usage", "application-versions", "application-permissions", "agents", "agent-runs", "plugins", "marketplace", "installed", "updates", "registry", "publishers", "packages", "downloads", "licenses", "reviews", "versions", "search", "statistics", "health", "users", "organizations", "tenants", "teams", "roles", "permissions", "license", "billing", "api-keys", "audit"] as const;
export const hyperKernelDashboardPages = ["v8-kernel", "v8-frameworks", "v8-capabilities", "v8-runtime", "v8-health", "v8-metrics", "v8-diagnostics", "v8-audit"] as const;
export const hyperCoordinationDashboardPages = ["v8-coordination", "v8-coordination-frameworks", "v8-coordination-dependencies", "v8-coordination-relationships", "v8-coordination-synchronization", "v8-coordination-compatibility", "v8-coordination-governance", "v8-coordination-health", "v8-coordination-metrics", "v8-coordination-audit"] as const;
export const hyperIntelligenceDashboardPages = ["v8-intelligence", "v8-intelligence-knowledge", "v8-intelligence-evidence", "v8-intelligence-signals", "v8-intelligence-recommendations", "v8-intelligence-compatibility", "v8-intelligence-health", "v8-intelligence-metrics", "v8-intelligence-audit"] as const;
export const intelligenceMeshDashboardPages = ["v9-intelligence", "v9-intelligence-federation", "v9-intelligence-knowledge", "v9-intelligence-evidence", "v9-intelligence-signals", "v9-intelligence-recommendations", "v9-intelligence-compatibility", "v9-intelligence-health", "v9-intelligence-metrics", "v9-intelligence-audit"] as const;
export const memoryDashboardPages = ["memory", "memory-namespaces", "memory-usage", "memory-retention", "memory-cache", "memory-retrieval", "memory-metrics"] as const;
export const capabilityDashboardPages = ["capabilities-catalog", "capabilities-registry", "capabilities-dependencies", "capabilities-health", "capabilities-metrics", "capabilities-audit", "capabilities-versions", "capabilities-lifecycle"] as const;
export const extensionDashboardPages = ["extensions", "extensions-plugins", "extensions-registry", "extensions-dependencies", "extensions-compatibility", "extensions-validation", "extensions-packages", "extensions-signatures", "extensions-health", "extensions-metrics", "extensions-audit"] as const;
export const workflowDashboardPages = ["workflows", "workflow-definitions", "workflow-planner", "workflow-dependencies", "workflow-constraints", "workflow-lifecycle", "workflow-history", "workflow-recovery", "workflow-metrics", "workflow-audit"] as const;
export const reasoningDashboardPages = ["reasoning", "reasoning-plans", "reasoning-decisions", "reasoning-strategies", "reasoning-validation", "reasoning-metrics"] as const;
export const collaborationDashboardPages = ["collaboration", "collaboration-teams", "collaboration-projects", "collaboration-sessions", "collaboration-tasks", "collaboration-timeline", "collaboration-activity", "collaboration-notifications"] as const;
export const governanceDashboardPages = ["governance", "governance-policies", "governance-risks", "governance-compliance", "governance-approvals", "governance-controls", "governance-models", "governance-prompts", "governance-agents", "governance-applications", "governance-workflows", "governance-data", "governance-incidents", "governance-exceptions", "governance-reports"] as const;
export const modelDashboardPages = ["model-platform", "models", "model-providers", "model-profiles", "model-deployments", "model-routing", "model-fallback", "model-evaluations", "model-benchmarks", "model-usage", "model-cost", "model-governance"] as const;
export const securityDashboardPages = ["security", "security-identity", "security-authentication", "security-authorization", "security-secrets", "security-threats", "security-incidents", "security-compliance", "security-audit"] as const;
export const apiManagementDashboardPages = ["api-management", "api-management-apis", "api-management-gateways", "api-management-routes", "api-management-versions", "api-management-policies", "api-management-credentials", "api-management-rate-limits", "api-management-quotas", "api-management-subscriptions", "api-management-analytics", "api-management-developer-portal"] as const;
export const integrationHubDashboardPages = ["integration-hub", "integration-hub-catalog", "integration-hub-instances", "integration-hub-mappings", "integration-hub-flows", "integration-hub-credentials", "integration-hub-health", "integration-hub-schedules", "integration-hub-failures", "integration-hub-dead-letter", "integration-hub-analytics"] as const;
export const digitalTwinDashboardPages = ["digital-twins", "twin-topology", "twin-telemetry", "twin-simulation", "twin-predictions", "twin-optimization"] as const;
export const businessIntelligenceDashboardPages = ["business-intelligence-workspaces", "business-intelligence-data-sources", "business-intelligence-datasets", "business-intelligence-semantic-models", "business-intelligence-metrics", "business-intelligence-reports", "business-intelligence-dashboards", "business-intelligence-insights", "business-intelligence-alerts", "business-intelligence-subscriptions", "business-intelligence-governance"] as const;
export const commandCenterDashboardPages = ["command-center", "command-center-operations", "command-center-agents", "command-center-automation", "command-center-incidents", "command-center-alerts", "command-center-topology", "command-center-health", "command-center-activity", "command-center-audit"] as const;
export const tiktokDashboardPages = ["tiktok-autonomous-intelligence-center", "tiktok-autonomous-operation", "tiktok-autonomous-mission-engine", "tiktok-business-intelligence", "tiktok-lead-management", "tiktok-business-workspace", "tiktok-performance-insights", "tiktok-ai-growth-center", "tiktok-ai-control-tower", "tiktok-ai-intelligent-decision-center", "tiktok-content-pipeline", "tiktok-account-center", "tiktok-browser-runtime", "tiktok-browser-cluster", "tiktok-device-center", "tiktok-proxy-center", "tiktok-ai-publishing-center", "tiktok-creator-workspace", "tiktok-campaign-center", "tiktok-data-collection", "tiktok-ai-interaction-center", "tiktok-ai-risk-control-center", "tiktok-operations-command-center", "tiktok-resource-center", "tiktok-ai-automation-engine", "tiktok-ai-execution-engine", "tiktok-local-runtime"] as const;
export const knowledgeGraphDashboardPages = ["knowledge-graphs", "knowledge-graph-entities", "knowledge-graph-relationships", "knowledge-graph-ontology", "knowledge-graph-taxonomy", "knowledge-graph-lineage", "knowledge-graph-analytics", "knowledge-graph-queries"] as const;

function useRequest<T>(load: () => Promise<T>) {
  const [value, setValue] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { let active = true; load().then((result) => { if (active) setValue(result); }).catch((reason: unknown) => { if (active) setError(reason instanceof Error ? reason.message : "Request failed."); }); return () => { active = false; }; }, []);
  return { value, error };
}

function RecordList({ title, load }: { title: string; load(): Promise<ApiListResponse<unknown>> }) {
  const { value, error } = useRequest(load);
  return <Card><h1>{title}</h1>{error && <p role="alert">{error}</p>}{!value && !error && <Loading />}{value && <Table><tbody>{value.data.map((item, index) => { const record = item as Record<string, unknown>; return <tr key={String(record.registry_id ?? record.publisher_id ?? record.package_id ?? record.version_id ?? index)}><td>{JSON.stringify(record)}</td></tr>; })}</tbody></Table>}</Card>;
}

export function LoginPage() {
  const { login, token } = useAuth(); const navigate = useNavigate(); const [username, setUsername] = useState(""); const [password, setPassword] = useState(""); const [error, setError] = useState<string | null>(null);
  if (token) return <Navigate to="/dashboard" replace />;
  return <Card><h1>Login</h1><form onSubmit={(event) => { event.preventDefault(); login({ username, password }).then(() => navigate("/dashboard")).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Login failed.")); }}><label>Username<input value={username} onChange={(event) => setUsername(event.target.value)} /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label><button type="submit">Sign in</button></form>{error && <p role="alert">{error}</p>}</Card>;
}

export function DashboardHome() {
  const { client } = useAuth();
  const version = useRequest(() => client.version());
  const health = useRequest(() => client.health());
  const statistics = useRequest(() => client.statistics());
  return <><h1>Dashboard</h1><div className="cards"><Card><h2>Server Version</h2><p>{version.value?.server_version ?? "Loading..."}</p></Card><Card><h2>Health Summary</h2><p>{health.value?.checks.length ?? "..."} checks</p></Card><Card><h2>Statistics Summary</h2><p>{statistics.value?.data.counters.total_records ?? "..."} records</p></Card></div></>;
}

export function CapabilityFrameworkPage({ title = "Capability Catalog", resource = "catalog" }: { title?: string; resource?: string }) {
  const { client } = useAuth();
  const state = useRequest(() => client.capabilities(resource));
  return <Card><h1>{title}</h1><p>Read-only TKAI V7 unified capability control plane.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>;
}

export function ExtensionFrameworkPage({ title = "Extensions", resource = "catalog" }: { title?: string; resource?: string }) {
  const { client } = useAuth();
  const state = useRequest(() => client.extensions(resource));
  return <Card><h1>{title}</h1><p>Read-only TKAI V7 internal extension and plugin metadata. Code execution and remote discovery are disabled.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>;
}

export function WorkflowFrameworkPage({ title = "Workflow Overview", resource = "registry" }: { title?: string; resource?: string }) {
  const { client } = useAuth();
  const state = useRequest(() => client.workflows(resource));
  return <Card><h1>{title}</h1><p>Read-only TKAI V7 workflow metadata orchestration. Runtime execution is disabled.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>;
}

export function RegistryPage() { const { client } = useAuth(); return <RecordList title="Registry" load={() => client.registries()} />; }
export function PublishersPage() { const { client } = useAuth(); return <RecordList title="Publishers" load={() => client.publishers()} />; }
export function PackagesPage() { const { client } = useAuth(); return <RecordList title="Packages" load={() => client.packages()} />; }
export function MarketplacePage() { const { client } = useAuth(); return <RecordList title="Enterprise Marketplace" load={() => client.marketplace()} />; }
export function DownloadsPage() { const { client } = useAuth(); return <RecordList title="Downloads" load={() => client.marketplaceDownloads()} />; }
export function LicensesPage() { const { client } = useAuth(); return <RecordList title="Licenses" load={() => client.marketplaceLicenses()} />; }
export function ReviewsPage() { const { client } = useAuth(); return <RecordList title="Reviews" load={() => client.marketplaceReviews()} />; }
export function VersionsPage() { const { client } = useAuth(); return <RecordList title="Versions" load={() => client.versions()} />; }
export function AgentDefinitionsPage() { const { client } = useAuth(); return <RecordList title="Agent Definitions" load={() => client.agents()} />; }
export function AgentRunsPage() { return <Card><h1>Agent Runs</h1><p>Open a run to inspect status, events, outputs, and metrics.</p></Card>; }
export function AgentRunDetailsPage() { return <Card><h1>Run Details</h1><p>Agent run events, outputs, and metrics are available through the run API.</p></Card>; }
export function PluginsPage({ title = "Plugins" }: { title?: string }) { const { client } = useAuth(); return <RecordList title={title} load={() => client.plugins()} />; }
export function PluginDetailsPage() { return <Card><h1>Plugin Details</h1><p>Review plugin metadata, lifecycle, tools, signing status, and requested permissions.</p></Card>; }
export function PluginPermissionsPage() { return <Card><h1>Plugin Permissions</h1><p>Filesystem, network, environment, secrets, API, database, workflow, and agent grants are shown here.</p></Card>; }
export function ApplicationsPage() { const { client } = useAuth(); return <RecordList title="AI Applications" load={() => client.applications()} />; }
export function ApplicationTemplatesPage() { const { client } = useAuth(); return <RecordList title="Application Templates" load={() => client.applicationTemplates()} />; }
export function ApplicationDeploymentsPage() { const { client } = useAuth(); return <RecordList title="Application Deployments" load={() => client.applicationDeployments()} />; }
export function ApplicationVersionsPage() { const { client } = useAuth(); return <RecordList title="Application Versions" load={() => client.applicationVersions()} />; }
export function ApplicationUsagePage() { const { client } = useAuth(); const state = useRequest(() => client.applicationDashboard()); return <Card><h1>Application Usage</h1>{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function ApplicationPermissionsPage() { return <Card><h1>Application Permissions</h1><p>Manage view, edit, publish, deploy, run, and administrator grants.</p></Card>; }
export function KnowledgeBasesPage() { const { client } = useAuth(); return <RecordList title="Knowledge Bases" load={() => client.knowledgeBases()} />; }
export function CollectionsPage() { const { client } = useAuth(); return <RecordList title="Collections" load={() => client.knowledge("collections")} />; }
export function DocumentsPage() { const { client } = useAuth(); return <RecordList title="Documents" load={() => client.knowledge("documents")} />; }
export function KnowledgeStatusPage({ title }: { title: string }) { return <Card><h1>{title}</h1><p>Tenant-scoped enterprise knowledge controls and status.</p></Card>; }
export function AppStorePage({ title, resource = "" }: { title: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.appStore(resource)); return <Card><h1>{title}</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function OrchestratorPage({ title = "Enterprise AI Orchestrator" }: { title?: string }) { const { client } = useAuth(); const state = useRequest(() => client.orchestrator()); return <Card><h1>{title}</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function ReasoningPage({ title = "Reasoning Sessions" }: { title?: string }) { const { client } = useAuth(); const state = useRequest(() => client.reasoning()); return <Card><h1>{title}</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function CollaborationPage({ title = "Enterprise AI Collaboration" }: { title?: string }) { const { client } = useAuth(); const state = useRequest(() => client.collaborationDashboard()); return <Card><h1>{title}</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function GovernancePage({ title = "Enterprise AI Governance" }: { title?: string }) { const { client } = useAuth(); const state = useRequest(() => client.governanceDashboard()); return <Card><h1>{title}</h1><p>Governance records support oversight workflows and do not claim certification or legal compliance.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function ModelPlatformPage({ title = "Enterprise AI Model Platform", resource = "model-platform" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.modelPlatform(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped model operations use credential references; secrets are never displayed.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function SecurityPlatformPage({ title = "Enterprise AI Security Platform", resource = "dashboard" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.security(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped zero-trust controls expose references and security posture without revealing credentials.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function ApiManagementPage({ title = "Enterprise AI API Management", resource = "dashboard" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.apiManagement(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped API lifecycle, gateway, policy, credential-reference, subscription, quota, and analytics controls.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function IntegrationHubPage({ title = "Enterprise AI Integration Hub", resource = "analytics" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.integrationHub(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped connector catalog, instances, declarative mappings, flows, credential references, health, schedules, failures, and analytics.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function DigitalTwinPage({ title = "Enterprise AI Digital Twin Platform", resource = "digital-twins" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.digitalTwin(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped twins, topology, telemetry, simulation, predictions, and optimization with versioned state and audited lifecycle controls.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function BusinessIntelligencePage({ title = "Enterprise AI Business Intelligence Platform", resource = "workspaces" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.businessIntelligence(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped workspaces, governed semantic models, bounded analytics, reports, dashboards, insights, alerts, and subscriptions.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function CommandCenterPage({ title = "Enterprise AI Command Center", resource = "overview" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.commandCenter(resource)); return <Card><h1>{title}</h1><p>Unified tenant-scoped control planes, live operations, incident response, topology, health, activity, and audit.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function KnowledgeGraphPage({ title = "Enterprise AI Knowledge Graph", resource = "graphs" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.knowledgeGraph(resource)); return <Card><h1>{title}</h1><p>Tenant-scoped graphs, entities, relationships, semantics, lineage, bounded queries, reasoning, and analytics.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokBrowserRuntimePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokBrowserRuntime()); return <Card><h1>TikTok Browser Runtime</h1><p>Tenant-scoped browser instances, profiles, account bindings, pool, queue, health, encrypted sessions, storage, and bounded recovery.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokBrowserClusterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokBrowserCluster()); return <Card><h1>TikTok Browser Cluster</h1><p>Local, tenant-isolated nodes, instances, fair queues, bounded resources, health, recovery, telemetry, and statistics. Recovery stops for unresolved TikTok restrictions.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokDeviceCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokDeviceCenter()); return <Card><h1>TikTok Device Center</h1><p>Unified local Android, iOS reference, emulator, simulator reference, and virtual-device inventory with profiles, fair scheduling, bounded allocation, health, recovery, telemetry, and statistics. Recovery stops for unresolved TikTok restrictions or challenges.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokProxyCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokProxyCenter()); return <Card><h1>TikTok Proxy Center</h1><p>Tenant-scoped inventory, health, regions, countries, groups, bindings, pool, queue, statistics, and failure operations. Credentials remain secret references.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAccountCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokDashboard()); return <Card><h1>TikTok Account Center</h1><p>Tenant-scoped accounts, login health, risk, groups, tags, sessions, cookies, and browser bindings.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokPublishingCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokPublishingCenter()); return <Card><h1>TikTok AI Publishing Center</h1><p>Tenant-scoped queue, calendar, schedules, approvals, retries, failures, history, analytics, and statistics. Publishing respects TikTok platform security and anti-abuse controls.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokCreatorWorkspacePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokCreatorWorkspace()); return <Card><h1>TikTok Creator Workspace</h1><p>Plan and review projects, calendars, creative assets, drafts, templates, reviews, approvals, and analytics. Publishing plans remain approval-gated and execute through the existing Publishing Center.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokCampaignCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokCampaignCenter()); return <Card><h1>TikTok Campaign Center</h1><p>Coordinate campaign overview, plans, schedules, approvals, monitoring, analytics, and history through existing TikTok modules. Campaigns never publish directly and remain approval-gated.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokContentPipelinePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokContentPipeline()); return <Card><h1>Enterprise TikTok Content Pipeline</h1><p>Tenant-scoped intake, validation, explainable quality, reviews, approvals, packaging, checkpoints, recovery, and reference-only publishing handoff. This pipeline never publishes directly.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokGrowthCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokGrowthCenter()); return <Card><h1>Enterprise TikTok AI Growth Center</h1><p>Bounded goals, KPIs, trends, opportunities, offline forecasts, analytics, and approval-gated execution proposals. Recommendations remain advisory until approved.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokPerformanceInsightsPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokPerformanceInsights()); return <Card><h1>TikTok Performance Insights Center</h1><p>Unified, explainable, read-only performance profiles, datasets, metrics, comparisons, trends, anomaly references, bounded forecasts, advisory insights, recommendations, reports, snapshots, and history.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokBusinessWorkspacePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokBusinessWorkspace()); return <Card><h1>TikTok Business Workspace</h1><p>Unified projects, operations, campaigns, calendars, members, approvals, analytics, and history. Publishing and execution remain approval-gated proposals delegated to existing TikTok modules.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokLeadManagementPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokLeadManagement()); return <Card><h1>TikTok Lead Management Center</h1><p>Consent-aware lead intake, deduplication, qualification, explainable scoring, assignment, manual follow-up proposals, bounded handoffs, history, and analytics. No direct outreach is executed.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokBusinessIntelligencePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokBusinessIntelligence()); return <Card><h1>TikTok Business Intelligence Center</h1><p>Unified, read-only dashboards, KPIs, comparisons, trends, bounded forecasts, reports, snapshots, exports, governance, and explainable advisory insights across TikTok business operations.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokDataCollectionPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokDataCollection()); return <Card><h1>TikTok Data Collection Center</h1><p>Tenant-scoped projects, jobs, datasets, pipelines, execution history, analytics, and encrypted storage references. Collection runs only through configured platform adapters.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokInteractionCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokInteractionCenter()); return <Card><h1>TikTok AI Interaction Center</h1><p>Projects, tasks, drafts, localized templates, review and approval queues, analytics, history, statistics, and notifications with strict tenant isolation.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokRiskControlCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokRiskControlCenter()); return <Card><h1>TikTok AI Risk Control Center</h1><p>Safety monitoring, bounded policies and rules, explainable scores, alerts, restrictions, approvals, coordinated pauses, health, recovery, analytics, and audit.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
type OperationsDashboard = {
  sections?: string[];
  overview?: Record<string, unknown>;
  health?: Record<string, unknown>;
};

const operationMetricLabels: Record<string, string> = {
  total_accounts: "Total accounts",
  active_accounts: "Active accounts",
  paused_accounts: "Paused accounts",
  restricted_accounts: "Restricted accounts",
  active_browsers: "Active browsers",
  browser_failures: "Browser failures",
  healthy_proxies: "Healthy proxies",
  unhealthy_proxies: "Unhealthy proxies",
  running_workflows: "Running workflows",
  queued_tasks: "Queued tasks",
  publishing_jobs: "Publishing jobs",
  collection_jobs: "Collection jobs",
  interaction_tasks: "Interaction tasks",
  risk_alerts: "Risk alerts",
  open_incidents: "Open incidents",
};

function displayOperationValue(value: unknown): string {
  if (typeof value === "number") return new Intl.NumberFormat().format(value);
  if (typeof value === "boolean") return value ? "Enabled" : "Disabled";
  if (typeof value === "string") return value.replaceAll("_", " ");
  return value == null ? "—" : String(value);
}

function operationStatusTone(value: unknown): string {
  const status = String(value ?? "unknown").toLowerCase();
  if (["healthy", "active", "ready", "running", "ok", "operational"].some((item) => status.includes(item))) return "healthy";
  if (["failed", "critical", "restricted", "offline", "error"].some((item) => status.includes(item))) return "critical";
  if (["warning", "degraded", "paused", "maintenance", "recovering"].some((item) => status.includes(item))) return "warning";
  return "neutral";
}

export function TikTokOperationsCenterPage() {
  const { client } = useAuth();
  const state = useRequest(() => client.tiktokOperationsCenter());
  const dashboard = (state.value ?? {}) as OperationsDashboard;
  const overview = dashboard.overview ?? {};
  const health = dashboard.health ?? {};
  const statuses = (overview.unified_status ?? {}) as Record<string, unknown>;
  const scoreValue = health.score ?? health.health_score ?? health.composite_score;
  const metricEntries = Object.entries(operationMetricLabels);
  const issueCount = Number(overview.risk_alerts ?? 0) + Number(overview.open_incidents ?? 0) + Number(overview.browser_failures ?? 0) + Number(overview.unhealthy_proxies ?? 0);

  return <div className="operations-v2">
    <div className="operations-hero">
      <div>
        <p className="operations-eyebrow">TikTok Cloud Control Platform</p>
        <h1>Operations Command Center</h1>
        <p>Live operational visibility across accounts, infrastructure, workflows, risk, and recovery.</p>
      </div>
      <div className={`operations-overall ${issueCount ? "warning" : "healthy"}`}>
        <span className="operations-pulse" />
        <div><small>Platform status</small><strong>{issueCount ? "Attention required" : "All systems operational"}</strong></div>
      </div>
    </div>

    {state.error && <div className="operations-error" role="alert"><strong>Dashboard unavailable</strong><span>{state.error}</span></div>}
    {!state.value && !state.error && <Card><Loading /></Card>}

    {state.value && <>
      <section className="operations-kpis" aria-label="Key operational metrics">
        {metricEntries.slice(0, 6).map(([key, label]) => <article key={key}>
          <span>{label}</span>
          <strong>{displayOperationValue(overview[key])}</strong>
          <small className={Number(overview[key] ?? 0) > 0 && ["browser_failures", "paused_accounts", "restricted_accounts"].includes(key) ? "metric-alert" : ""}>
            {["browser_failures", "paused_accounts", "restricted_accounts"].includes(key) ? "requires review" : "current"}
          </small>
        </article>)}
      </section>

      <div className="operations-grid">
        <section className="operations-panel operations-platform">
          <div className="operations-panel-heading"><div><p className="operations-eyebrow">Infrastructure</p><h2>Platform health</h2></div>{scoreValue != null && <strong className="health-score">{displayOperationValue(scoreValue)}<small>/ 100</small></strong>}</div>
          <div className="status-list">
            {Object.entries(statuses).length ? Object.entries(statuses).map(([key, value]) => <div className="status-row" key={key}>
              <span className={`status-dot ${operationStatusTone(value)}`} />
              <span>{key.replace(/_status$/, "").replaceAll("_", " ")}</span>
              <strong className={`status-pill ${operationStatusTone(value)}`}>{displayOperationValue(value)}</strong>
            </div>) : <p className="operations-empty">No module status has been reported.</p>}
          </div>
        </section>

        <section className="operations-panel">
          <div className="operations-panel-heading"><div><p className="operations-eyebrow">Workload</p><h2>Live operations</h2></div><span className="live-badge">Live</span></div>
          <div className="workload-grid">
            {metricEntries.slice(6).map(([key, label]) => <div key={key}><span>{label}</span><strong>{displayOperationValue(overview[key])}</strong></div>)}
          </div>
        </section>

        <section className="operations-panel operations-attention">
          <div className="operations-panel-heading"><div><p className="operations-eyebrow">Safety &amp; response</p><h2>Needs attention</h2></div><span className={`attention-count ${issueCount ? "warning" : ""}`}>{issueCount}</span></div>
          <div className="attention-list">
            {[
              ["Open incidents", overview.open_incidents],
              ["Risk alerts", overview.risk_alerts],
              ["Browser failures", overview.browser_failures],
              ["Unhealthy proxies", overview.unhealthy_proxies],
            ].map(([label, value]) => <div key={String(label)}><span>{String(label)}</span><strong>{displayOperationValue(value)}</strong></div>)}
          </div>
          <p className="operations-safety-note">Recovery remains blocked while TikTok restrictions or unresolved challenges are active.</p>
        </section>
      </div>
    </>}
  </div>;
}
export function TikTokResourceCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokResourceCenter()); return <Card><h1>TikTok Resource Center</h1><p>Unified tenant-isolated inventory, reservations, leases, allocations, quotas, capacity, utilization, health, recovery, telemetry, and statistics for local TikTok resources.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAutomationEnginePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokAutomationEngine()); return <Card><h1>TikTok AI Automation Engine</h1><p>Approved local automations, reusable plans, executions, triggers, conditions, queues, monitoring, recovery, and analytics with bounded concurrency and restriction-safe stops.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokExecutionEnginePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokExecutionEngine()); return <Card><h1>TikTok AI Execution Engine</h1><p>Approval-gated plan execution through existing workflow, automation, scheduler, runtime, resource, browser, device, account, proxy, and risk systems, with checkpoints, rollback, verification, monitoring, and analytics.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAutonomousOperationPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokAutonomousOperation()); return <Card><h1>TikTok Autonomous Operation Center</h1><p>Approval-gated missions coordinate existing scheduler, automation, execution, workflow, and runtime services. Restrictions and unresolved challenges always stop execution and recovery.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAutonomousMissionEnginePage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokMissionEngine()); return <Card><h1>TikTok Autonomous Mission Engine</h1><p>Monitor the approval-gated mission queue, worker dispatch, dependency health, checkpoints, recovery, and analytics. Execution is delegated to existing TikTok services, and unresolved restrictions stop dispatch and recovery.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAutonomousIntelligenceCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokIntelligenceCenter()); return <Card><h1>TikTok Autonomous Intelligence Center</h1><p>Read-only, explainable cross-module reasoning, evidence, predictions, and advisory recommendations. It never executes actions or publishes.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAIControlTowerPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokControlTower()); return <Card><h1>TikTok AI Control Tower</h1><p>Unified, read-only operational cockpit for health, topology, runtime, resources, accounts, browsers, devices, proxies, workflows, scheduling, automation, execution, recovery, publishing, collection, interaction, risk, analytics, alerts, and activity.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokAIIntelligentDecisionCenterPage() { const { client } = useAuth(); const state = useRequest(() => client.tiktokDecisionCenter()); return <Card><h1>TikTok AI Intelligent Decision Center</h1><p>Explainable and reviewable decision support using scoped, read-only TikTok platform data. Recommendations remain advisory until an authorized reviewer approves an execution proposal handoff.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function TikTokLocalRuntimePage() { const { client } = useAuth(); const state = useRequest(() => client.localRuntime()); return <Card><h1>TikTok Local Deployment &amp; Runtime Center</h1><p>Loopback-only service status, URLs, ports, directories, database health, backup state, and last health check. Use scripts\start-tkai.ps1 and scripts\stop-tkai.ps1 for lifecycle control.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function HyperKernelPage({ title = "Kernel Overview", resource = "kernel" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.hyperKernel(resource === "audit" ? "kernel" : resource)); return <Card><h1>{title}</h1><p>TKAI V8 execution-independent, metadata-driven coordination.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(resource === "audit" ? (state.value as { audit?: unknown }).audit ?? [] : state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function HyperCoordinationPage({ title = "Coordination Overview", resource = "profiles" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.hyperCoordination(resource === "audit" ? "governance" : resource)); return <Card><h1>{title}</h1><p>Reference-only cross-framework metadata coordination. Approved references never authorize execution.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function HyperIntelligencePage({ title = "Hyper Intelligence Overview", resource = "profiles" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.hyperIntelligence(resource === "audit" ? "profiles" : resource)); return <Card><h1>{title}</h1><p>Metadata-only intelligence spanning V6 AI Centers and V7/V8 Frameworks. Recommendations are advisory and never authorize execution.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(resource === "audit" ? (state.value as { audit?: unknown }).audit ?? [] : state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function IntelligenceMeshPage({ title = "Intelligence Mesh Overview", resource = "profiles" }: { title?: string; resource?: string }) { const { client } = useAuth(); const state = useRequest(() => client.adaptiveIntelligenceMesh(resource === "audit" ? "profiles" : resource)); return <Card><h1>{title}</h1><p>Reference-only federation across V6, V7, V8, and V9. Safe summaries and recommendations are advisory, non-executable, and never expose hidden reasoning.</p>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(resource === "audit" ? (state.value as { audit?: unknown }).audit ?? [] : state.value, null, 2)}</pre> : <Loading />}</Card>; }
export function MemoryPage({ title = "Memory Overview", resource = "memory" }: { title?: string; resource?: "memory" | "namespaces" | "cache" }) { const { client } = useAuth(); const state = useRequest<unknown>(() => resource === "namespaces" ? client.memoryNamespaces() : resource === "cache" ? client.memoryCache() : client.memories()); return <Card><h1>{title}</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value, null, 2)}</pre> : <Loading />}</Card>; }

export function SearchPage() {
  const { client } = useAuth(); const [keyword, setKeyword] = useState(""); const [target, setTarget] = useState(""); const [results, setResults] = useState<ApiListResponse<SearchEntry> | null>(null); const [error, setError] = useState<string | null>(null);
  const submit = () => { client.search(keyword, target).then(setResults).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Search failed.")); };
  return <Card><h1>Search</h1><SearchBar value={keyword} onChange={setKeyword} onSubmit={submit} /><label>Target<select value={target} onChange={(event) => setTarget(event.target.value)}><option value="">All</option><option value="registry">Registry</option><option value="publisher">Publisher</option><option value="package">Package</option><option value="version">Version</option></select></label>{error && <p role="alert">{error}</p>}{results && <p>{results.total} results</p>}</Card>;
}

export function StatisticsPage() { const { client } = useAuth(); const state = useRequest(() => client.statistics()); return <Card><h1>Statistics</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value.data.counters, null, 2)}</pre> : <Loading />}</Card>; }
export function HealthPage() { const { client } = useAuth(); const state = useRequest(() => client.health()); return <Card><h1>Health</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value.statistics, null, 2)}</pre> : <Loading />}</Card>; }
export function EnterprisePage({ title, load }: { title: string; load(): Promise<ApiListResponse<EnterpriseRecord>> }) { const state = useRequest(load); return <Card><h1>{title}</h1>{state.error && <p role="alert">Unauthorized or unavailable: {state.error}</p>}{!state.value && !state.error && <Loading />}{state.value && (state.value.total ? <Table><tbody>{state.value.data.map((item,index) => <tr key={index}><td>{JSON.stringify(item)}</td></tr>)}</tbody></Table> : <p>No records.</p>)}</Card>; }
export function NotFoundPage() { return <Card><h1>404</h1><p>Page not found.</p></Card>; }
