/** Minimal typed local stores; server data remains owned by the REST API. */

import type { Execution, Project, Workflow } from "./api";
export type Theme = "light" | "dark";
export interface StudioState { projects: Project[]; workflows: Workflow[]; executions: Execution[]; theme: Theme; }
export const initialState: StudioState = { projects: [], workflows: [], executions: [], theme: "dark" };
export const toggleTheme = (state: StudioState): StudioState => ({ ...state, theme: state.theme === "dark" ? "light" : "dark" });
