/** Typed client for the read-only Marketplace Server V2 HTTP API. */

export interface ApiListResponse<T> { data: T[]; total: number; error: null; }
export interface ApiResourceResponse<T> { data: T; error: null; }
export interface ApiErrorResponse { error: { code: string; message: string }; }
export interface LoginRequest { username: string; password: string; }
export interface AuthenticatedUser { username: string; administrator: boolean; }
export interface LoginResponse { access_token: string; token_type: "Bearer"; expires_at: string; user: AuthenticatedUser; }
export interface Registry { registry_id: string; status: string; descriptor: Record<string, unknown>; }
export interface Publisher { publisher_id: string; status: string; descriptor: Record<string, unknown>; }
export interface Package { package_id: string; status: string; manifest: Record<string, unknown>; }
export interface Version { version_id: string; status: string; manifest: Record<string, unknown>; }
export interface SearchEntry { identifier: string; target: string; name: string; publisher?: string; package?: string; }
export interface HealthSnapshot { checks: unknown[]; statistics: Record<string, number | boolean>; closed: boolean; }
export interface StatisticsSnapshot { counters: Record<string, number>; closed: boolean; }
export interface ServerVersion { server_version: string; framework_version: string; build_metadata: Record<string, unknown>; }
export interface EnterpriseRecord { [key: string]: unknown; }
export interface AgentDefinitionRecord { agent_id: string; name: string; version: string; status: string; [key: string]: unknown; }
export interface AgentRunRecord { run_id: string; agent_id: string; workspace: string; status: string; events: unknown[]; metrics: Record<string, number>; }
export interface PluginRecord { id: string; name: string; version: string; description: string; permissions: string[]; state?: string; [key: string]: unknown; }
export interface MarketplaceRecord { package_id?: string; publisher_id?: string; license_id?: string; review_id?: string; [key: string]: unknown; }
export interface ApplicationRecord { id: string; name: string; description: string; version: string; owner: string; category: string; tags: string[]; status: string; [key: string]: unknown; }
export interface ApplicationTemplateRecord { id: string; name: string; category: string; description: string; [key: string]: unknown; }
export interface DeploymentRecord { id: string; application_id: string; version: string; environment: string; replicas: number; quota: number; status: string; [key: string]: unknown; }
export interface KnowledgeRecord { id: string; name: string; status: string; scope: { tenant: string; workspace: string; namespace: string }; [key: string]: unknown; }
export interface AppStoreRecord { id?: string; name?: string; status?: string; [key: string]: unknown; }
export interface OrchestratorSnapshot { sections: string[]; plans: number; queues: Record<string, number>; executions: number; failures: number; retries: number; performance: Record<string, unknown>; }
export interface MemoryRecord { id: string; namespace: string; tenant: string; workspace: string; owner: string; type: string; source: string; created: string; updated: string; ttl: number | null; metadata: Record<string, unknown>; }
export interface ReasoningRecord { id: string; tenant: string; workspace: string; agent: string; goal: string; strategy: string; mode: string; state: string; priority: number; metadata: Record<string, unknown>; }
export interface CollaborationDashboard { sections: string[]; projects: number; sessions: number; tasks: number; timeline: unknown[]; notifications: unknown[]; presence: Record<string, string>; metrics: Record<string, number>; }
export interface GovernanceDashboard { sections: string[]; summary: Record<string, number>; metrics: Record<string, number>; }
export interface ModelPlatformDashboard { sections: string[]; models: number; providers: number; profiles: number; usage_records: number; cost: Record<string, unknown>; metrics: Record<string, number>; }
export interface SecurityDashboard { identity: Record<string, number>; authentication: Record<string, number>; authorization: Record<string, number>; secrets: Record<string, number>; threats: unknown[]; incidents: unknown[]; compliance: Record<string, number>; audit: unknown[]; metrics: Record<string, number>; }

export class ApiClientError extends Error {
  constructor(public readonly status: number, message: string) { super(message); }
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class MarketplaceApiClient {
  constructor(private readonly baseUrl = configuredBaseUrl, private readonly token?: string) {}

  withToken(token: string | undefined): MarketplaceApiClient { return new MarketplaceApiClient(this.baseUrl, token); }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("content-type", "application/json");
    if (this.token) headers.set("authorization", `Bearer ${this.token}`);
    const response = await fetch(`${this.baseUrl}${path}`, { ...init, headers });
    const body = await response.json() as T | ApiErrorResponse;
    if (!response.ok) {
      const error = body as ApiErrorResponse;
      throw new ApiClientError(response.status, error.error?.message ?? "Request failed.");
    }
    return body as T;
  }

  login(request: LoginRequest) { return this.request<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify(request) }); }
  me() { return this.request<AuthenticatedUser>("/auth/me"); }
  logout() { return this.request<{ revoked: boolean }>("/auth/logout", { method: "POST" }); }
  version() { return this.request<ServerVersion>("/version"); }
  health() { return this.request<HealthSnapshot>("/health"); }
  statistics() { return this.request<ApiResourceResponse<StatisticsSnapshot>>("/statistics"); }
  registries() { return this.request<ApiListResponse<Registry>>("/registry"); }
  registry(id: string) { return this.request<ApiResourceResponse<Registry>>(`/registry/${encodeURIComponent(id)}`); }
  publishers() { return this.request<ApiListResponse<Publisher>>("/publishers"); }
  packages() { return this.request<ApiListResponse<Package>>("/packages"); }
  versions() { return this.request<ApiListResponse<Version>>("/versions"); }
  search(keyword = "", target = "") {
    const query = new URLSearchParams();
    if (keyword) query.set("keyword", keyword);
    if (target) query.set("target", target);
    const suffix = query.size ? `?${query}` : "";
    return this.request<ApiListResponse<SearchEntry>>(`/search${suffix}`);
  }
  users() { return this.request<ApiListResponse<EnterpriseRecord>>("/users"); }
  organizations() { return this.request<ApiListResponse<EnterpriseRecord>>("/organizations"); }
  teams() { return this.request<ApiListResponse<EnterpriseRecord>>("/teams"); }
  roles() { return this.request<ApiListResponse<EnterpriseRecord>>("/roles"); }
  apiKeys() { return this.request<ApiListResponse<EnterpriseRecord>>("/api-keys"); }
  audit() { return this.request<ApiListResponse<EnterpriseRecord>>("/audit"); }
  enterprise(resource: string) { return this.request<ApiListResponse<EnterpriseRecord>>(`/enterprise/${resource}`); }
  agents() { return this.request<ApiListResponse<AgentDefinitionRecord>>("/agents"); }
  applications() { return this.request<ApiListResponse<ApplicationRecord>>("/applications"); }
  applicationTemplates() { return this.request<ApiListResponse<ApplicationTemplateRecord>>("/templates"); }
  applicationDeployments() { return this.request<ApiListResponse<DeploymentRecord>>("/deployments"); }
  applicationVersions() { return this.request<ApiListResponse<EnterpriseRecord>>("/applications/versions"); }
  applicationDashboard() { return this.request<Record<string, unknown>>("/applications/dashboard"); }
  appStore(resource = "") {
    const path = resource ? `/app-store/${resource}` : "/app-store";
    const scope = new URLSearchParams({ tenant: "default", organization: "default", workspace: "default" });
    return this.request<ApiListResponse<AppStoreRecord> | Record<string, unknown>>(`${path}?${scope}`);
  }
  orchestrator() { return this.request<OrchestratorSnapshot>("/orchestrator?tenant=default&actor=dashboard"); }
  memories(namespace = "") {
    const query = new URLSearchParams({ tenant: "default", workspace: "default", owner: "dashboard" });
    if (namespace) query.set("namespace", namespace);
    return this.request<{ data: MemoryRecord[] }>(`/memory?${query}`);
  }
  memoryCache() { return this.request<Record<string, number>>("/memory/cache"); }
  memoryNamespaces() { return this.request<{ data: string[] }>("/memory/namespaces?tenant=default&workspace=default&owner=dashboard"); }
  reasoning() { return this.request<{ data: ReasoningRecord[] }>("/reasoning?tenant=default&workspace=default&actor=dashboard"); }
  collaborationDashboard() { return this.request<CollaborationDashboard>("/collaboration/dashboard?tenant=default&workspace=default&actor=dashboard"); }
  governanceDashboard() { return this.request<GovernanceDashboard>("/governance/dashboard?tenant=default&workspace=default&actor=dashboard"); }
  modelPlatform(resource = "model-platform") {
    const query = new URLSearchParams({ tenant: "default", workspace: "default", actor: "dashboard" });
    return this.request<Record<string, unknown>>(`/${resource}?${query}`);
  }
  security(resource = "dashboard") {
    const query = new URLSearchParams({ tenant: "default", workspace: "default", actor: "dashboard" });
    return this.request<SecurityDashboard | Record<string, unknown>>(`/security/${resource}?${query}`);
  }
  apiManagement(resource = "dashboard") {
    const query = new URLSearchParams({ tenant: "default", workspace: "default", actor: "dashboard" });
    return this.request<Record<string, unknown>>(`/api-management/${resource}?${query}`);
  }
  integrationHub(resource = "analytics") {
    const query = new URLSearchParams({ tenant: "default", workspace: "default", actor: "dashboard" });
    return this.request<Record<string, unknown>>(`/integration-hub/${resource}?${query}`);
  }
  digitalTwin(resource = "digital-twins") {
    const query = new URLSearchParams({ tenant: "default", workspace: "default", actor: "dashboard" });
    return this.request<Record<string, unknown> | unknown[]>(`/${resource}?${query}`);
  }
  plans() { return this.request<ApiListResponse<EnterpriseRecord>>("/plans?tenant=default&actor=dashboard"); }
  executions() { return this.request<ApiListResponse<EnterpriseRecord>>("/executions?tenant=default&actor=dashboard"); }
  queues() { return this.request<Record<string, unknown>>("/queues"); }
  knowledgeBases() { return this.request<ApiListResponse<KnowledgeRecord>>("/knowledge-bases?tenant=default&workspace=default&namespace=default"); }
  knowledge(resource: string) { return this.request<ApiListResponse<EnterpriseRecord>>(`/${resource}?tenant=default&workspace=default&namespace=default`); }
  agentRun(id: string) { return this.request<AgentRunRecord>(`/agents/run/${encodeURIComponent(id)}`); }
  plugins() { return this.request<ApiListResponse<PluginRecord>>("/plugins"); }
  marketplace() { return this.request<ApiListResponse<MarketplaceRecord>>("/marketplace"); }
  marketplaceLicenses() { return this.request<ApiListResponse<MarketplaceRecord>>("/licenses"); }
  marketplaceReviews() { return this.request<ApiListResponse<MarketplaceRecord>>("/reviews"); }
  marketplaceDownloads() { return this.request<ApiListResponse<MarketplaceRecord>>("/downloads"); }
  installPlugin(id: string, version?: string) { return this.request<PluginRecord>("/plugins/install", { method: "POST", body: JSON.stringify({ id, version }) }); }
  enablePlugin(id: string) { return this.request<PluginRecord>("/plugins/enable", { method: "POST", body: JSON.stringify({ id }) }); }
  disablePlugin(id: string) { return this.request<PluginRecord>("/plugins/disable", { method: "POST", body: JSON.stringify({ id }) }); }
  updatePlugin(id: string, version?: string) { return this.request<PluginRecord>("/plugins/update", { method: "POST", body: JSON.stringify({ id, version }) }); }
  uninstallPlugin(id: string) { return this.request<PluginRecord>(`/plugins/${encodeURIComponent(id)}`, { method: "DELETE" }); }
}
