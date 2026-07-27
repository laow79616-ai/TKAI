# TikTok AI Risk Control Center Architecture

The Risk Control Center is a tenant- and workspace-isolated safety control plane. TikTok Account Center, Browser Runtime, Proxy Center, Account Farming, Content, Publishing, Data Collection, and Interaction emit bounded status and health signals. Typed policies and rules evaluate those signals; the control plane records scores, evidence references, alerts, restrictions, pauses, reviews, recovery outcomes, metrics, and audit entries.

Existing platform workflow, automation, security, audit, metrics, event, and observability infrastructure remains authoritative. Integration occurs through narrow `RiskControlPort` interfaces. The module contains no arbitrary expression evaluator, live TikTok dependency, credential storage, CAPTCHA handling, restriction circumvention, identity evasion, or anti-detection mechanism.

## Lifecycle

Profiles move through Draft, Active, Monitoring, Review Required, Paused, Recovering, Resolved, Archived, and Deleted by an explicit transition table. Invalid transitions fail closed.

## Signals, policies, and rules

Signals are enumerated health and restriction observations with bounded severity and confidence. Policy categories cover accounts, browsers, proxies, publishing, interaction, collection, schedules, concurrency, approval, and recovery. Rules allow only signal, threshold, or trend matching over validated windows, priorities, cooldowns, and versions—never code or unrestricted expressions.

## Scoring and actions

Scores combine severity, confidence, frequency, recency, and trend evidence into `[0, 100]`. Ordered configurable thresholds map scores to Low, Medium, High, and Critical. Explanations and recommended actions are retained in score history. Actions are notifications, reviews, approvals, bounded pauses/drains/releases, recovery, escalation, or an emergency kill switch. There is no restriction-bypass action.

## Restrictions, limits, pauses, and reviews

Restrictions can target features, accounts, workspaces, schedules, browser profiles, or proxies and carry reasons, expiry, and review requirements. Account/workspace/browser/proxy/session and hourly/daily/concurrency/job limits are bounded. Manual and automatic pauses retain reviewer and resume-approval context. Evidence-based reviews expire and are fully audited.

## Recovery and health

Recovery supports health recheck, session validation by reference, browser/proxy recovery references, cooldown, checkpoint resume, manual mode, maximum attempts, and outcomes. Recovery stops immediately while any platform challenge or restriction remains unresolved. Health covers account, login, session, browser, proxy, publishing, interaction, collection, and a composite score.

## Alerts, analytics, and dashboard

Alerts include severity, source, account/workspace/rule, message, acknowledgement, escalation, resolution, and history. Analytics expose risk events and distribution, pauses, restrictions, recoveries, success rate, alert volume, and score trend. The dashboard presents the same tenant-scoped operational view through `/tiktok/risk-control/dashboard`.
