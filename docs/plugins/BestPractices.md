# Plugin Best Practices

- Request only required permissions.
- Keep initialization fast, deterministic, and reversible.
- Pin dependencies and publish immutable versions.
- Avoid process-global state and background work without lifecycle cleanup.
- Never log secrets or raw environment values.
- Sign every release and verify the packaged bytes.
- Expose bounded tools and handle cancellation and timeout failures.
- Test install, enable, disable, update, rollback, and uninstall paths.
