import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { type ApiListResponse, type EnterpriseRecord, type SearchEntry } from "./api";
import { useAuth } from "./auth";
import { Card, Loading, SearchBar, Table } from "./components";

export const dashboardPages = ["dashboard", "applications", "application-templates", "deployments", "application-usage", "application-versions", "application-permissions", "agents", "agent-runs", "plugins", "marketplace", "installed", "updates", "registry", "publishers", "packages", "downloads", "licenses", "reviews", "versions", "search", "statistics", "health", "users", "organizations", "tenants", "teams", "roles", "permissions", "license", "billing", "api-keys", "audit"] as const;

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
  const { client } = useAuth(); const version = useRequest(() => client.version()); const health = useRequest(() => client.health()); const statistics = useRequest(() => client.statistics());
  return <><h1>Dashboard</h1><div className="cards"><Card><h2>Server Version</h2><p>{version.value?.server_version ?? "Loading…"}</p></Card><Card><h2>Health Summary</h2><p>{health.value?.checks.length ?? "…"} checks</p></Card><Card><h2>Statistics Summary</h2><p>{statistics.value?.data.counters.total_records ?? "…"} records</p></Card></div></>;
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

export function SearchPage() {
  const { client } = useAuth(); const [keyword, setKeyword] = useState(""); const [target, setTarget] = useState(""); const [results, setResults] = useState<ApiListResponse<SearchEntry> | null>(null); const [error, setError] = useState<string | null>(null);
  const submit = () => { client.search(keyword, target).then(setResults).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Search failed.")); };
  return <Card><h1>Search</h1><SearchBar value={keyword} onChange={setKeyword} onSubmit={submit} /><label>Target<select value={target} onChange={(event) => setTarget(event.target.value)}><option value="">All</option><option value="registry">Registry</option><option value="publisher">Publisher</option><option value="package">Package</option><option value="version">Version</option></select></label>{error && <p role="alert">{error}</p>}{results && <p>{results.total} results</p>}</Card>;
}

export function StatisticsPage() { const { client } = useAuth(); const state = useRequest(() => client.statistics()); return <Card><h1>Statistics</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value.data.counters, null, 2)}</pre> : <Loading />}</Card>; }
export function HealthPage() { const { client } = useAuth(); const state = useRequest(() => client.health()); return <Card><h1>Health</h1>{state.error && <p role="alert">{state.error}</p>}{state.value ? <pre>{JSON.stringify(state.value.statistics, null, 2)}</pre> : <Loading />}</Card>; }
export function EnterprisePage({ title, load }: { title: string; load(): Promise<ApiListResponse<EnterpriseRecord>> }) { const state = useRequest(load); return <Card><h1>{title}</h1>{state.error && <p role="alert">Unauthorized or unavailable: {state.error}</p>}{!state.value && !state.error && <Loading />}{state.value && (state.value.total ? <Table><tbody>{state.value.data.map((item,index) => <tr key={index}><td>{JSON.stringify(item)}</td></tr>)}</tbody></Table> : <p>No records.</p>)}</Card>; }
export function NotFoundPage() { return <Card><h1>404</h1><p>Page not found.</p></Card>; }
