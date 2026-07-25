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
}
