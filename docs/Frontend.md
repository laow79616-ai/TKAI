# TKAI Studio Frontend Foundation

The Studio frontend is a standalone React, TypeScript, and Vite application in
`studio/frontend`. It consumes only the frozen REST endpoints for projects,
workflows, executions, health, system, and version.

It includes typed API client contracts, local Project/Workflow/Execution and
settings/theme state, light/dark theme state, routing, application shell,
sidebar, top-level layout, and reference components for cards, tables, forms,
dialogs, status, notifications, and loading.

Pages are Dashboard, Projects, Workflow, Execution, Agents, Providers, Memory,
Tools, Plugins, Settings, and Logs. The reference Workflow Designer model is
documented in [WorkflowDesigner.md](WorkflowDesigner.md). The Execution page
also has an offline, prop-driven monitor model documented in
[ExecutionMonitor.md](ExecutionMonitor.md); it consumes only the existing
Execution REST contract and adds no backend endpoint or polling.

Agent Chat is also a local, reference-only frontend layer documented in
[AgentChat.md](AgentChat.md). Its host injects an SDK Agent bridge explicitly;
it never calls the Runtime, creates Providers, or adds a REST endpoint.

Run `npm install` and `npm run dev` in `studio/frontend` in a local Node 18+
environment. This repository validation environment has no Node/npm, so Vite
lint and typecheck must run in the frontend build environment.
