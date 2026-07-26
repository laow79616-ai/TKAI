# Enterprise AI Studio

TKAI V2.3 AI Studio is a project-scoped authoring surface for prompts, chat,
knowledge, RAG, model profiles, evaluations, and visual workflows. It composes
the existing Agent Runtime, Workflow SDK, provider SDK, enterprise identity,
plugin marketplace, observability, and deployment layers; it does not replace
or duplicate them.

Projects are portable versioned bundles. Archive is non-destructive, clone uses
a fresh identity, and import never trusts a bundle's original local identifier.
The `/api` resource families are projects, prompts, chat, sessions, knowledge,
rag, models, evaluation, and workflows.

The dashboard exposes Projects, Prompt Studio, Chat Studio, Knowledge, RAG,
Models, Evaluation, and Workflow Studio. All server-side authorization remains
enforced by the Enterprise Platform.
