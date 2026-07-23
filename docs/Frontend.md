# TKAI Studio Frontend Foundation

The Studio frontend is a standalone React, TypeScript, and Vite application in
`studio/frontend`. It consumes only the frozen REST endpoints for projects,
workflows, executions, health, system, and version.

It includes typed API client contracts, local Project/Workflow/Execution and
settings/theme state, light/dark theme state, routing, application shell,
sidebar, top-level layout, and reference components for cards, tables, forms,
dialogs, status, notifications, and loading.

Pages are Dashboard, Projects, Workflow, Execution, Agents, Providers, Memory,
Tools, Plugins, Settings, and Logs. They are navigation placeholders only; no
Workflow Designer, execution monitor, Agent chat, or backend API changes are
included.

Run `npm install` and `npm run dev` in `studio/frontend` in a local Node 18+
environment. This repository validation environment has no Node/npm, so Vite
lint and typecheck must run in the frontend build environment.
