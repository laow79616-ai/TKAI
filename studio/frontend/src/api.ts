/** Typed client for the frozen Studio REST response contract. */

export interface ApiSuccess<T> { success: true; data: T; request_id: string; timestamp: string; }
export interface ApiError { success: false; error: { code: string; message: string }; request_id: string; timestamp: string; }
export type ApiResponse<T> = ApiSuccess<T> | ApiError;
export interface Project { project_id: string; name: string; description: string; metadata: Record<string, unknown>; created_at: string; }
export interface Workflow { workflow_id: string; project_id: string; name: string; nodes: unknown[]; edges: string[][]; metadata: Record<string, unknown>; }
export interface Execution { execution_id: string; workflow_id: string; project_id: string | null; status: string; output: unknown; error: string | null; created_at: string; }

export class StudioApiClient {
  constructor(private readonly baseUrl = "/api") {}
  private async request<T>(path: string, init?: RequestInit): Promise<ApiResponse<T>> {
    const response = await fetch(`${this.baseUrl}${path}`, { headers: { "content-type": "application/json", ...(init?.headers ?? {}) }, ...init });
    return response.json() as Promise<ApiResponse<T>>;
  }
  projects() { return this.request<Project[]>("/projects"); }
  workflows() { return this.request<Workflow[]>("/workflows"); }
  executions() { return this.request<Execution[]>("/executions"); }
  health() { return this.request<Record<string, unknown>>("/health"); }
  system() { return this.request<Record<string, unknown>>("/system"); }
  version() { return this.request<Record<string, unknown>>("/version"); }
}
