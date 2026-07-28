# TKAI V5 TikTok Modules

The canonical module order is defined in `tiktok/registry.py` and reused by
integration readiness and runtime health. It contains all completed TikTok
modules from runtime, account, browser, device, proxy, content, publishing,
workflow, automation, scheduling, and execution through operations, analytics,
optimization, creator, campaign, growth, performance, business workspace, lead
management, and business intelligence.

The API factory constructs modules in dependency order and registers existing
routes once. Task Scheduler supplies the Control Tower scheduler port; it is not
duplicated by Execution Engine. No module performs live TikTok access during
import, application creation, OpenAPI generation, readiness, or diagnostics.
