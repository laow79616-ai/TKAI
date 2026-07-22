# TKAI Roadmap

## V1.0 Release Candidate

The V1.0 framework foundation is stabilized as `1.0.0-rc.1`.

## Completed foundation

- Core runtime, configuration, command, generator, and template services.
- Plugin framework with discovery, registration, and lifecycle management.
- Workflow engine with serial/parallel execution, conditions, loops, retries,
  and events.
- Provider-neutral AI framework.
- Workflow runtime release preparation: CLI lifecycle commands, built-in
  checkpoint/resume examples, recovery tests, and release documentation.
- Provider-neutral AI foundation with offline-testable compatible adapters.

## Next milestones

1. Add production SDK adapters and credential configuration for every AI
   provider, while keeping the injected-client interface intact.
2. Add durable workflow checkpoint storage, distributed scheduling, timeout
   enforcement, and durable event delivery.
3. Add plugin version constraints, dependency resolution, and isolation.
4. Expand templates for React, Docker, PostgreSQL, Redis, and Playwright.
5. Add end-to-end generated-project validation in CI.
