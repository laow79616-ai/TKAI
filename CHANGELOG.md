# Changelog

## 1.0.0-rc.1

### Added

- Plugin discovery, loading, registry, and lifecycle APIs.
- Bundled discoverable plugin manifests for Python, Docker, Git, OpenAI,
  Claude, Gemini, Telegram, and TikTok.
- Workflow tasks, steps, event bus, executor, and serial/parallel scheduler.
- Unified AI provider interfaces and identities for OpenAI, Claude, Gemini,
  DeepSeek, Qwen, and OpenRouter.

### Changed

- Unified configuration state handling through `Settings` and the compatible
  `ConfigManager` persistence facade.
- Unified the two historical `TemplateManager` import paths behind one API.
- Added packaging and quality-tool configuration to `pyproject.toml`.

### Fixed

- Prevented `tkai.__main__` from executing the CLI when imported.
- Prevented template discovery from treating `__pycache__` as a template.

## 0.2.1

- Initial packaged TKAI command-line and template-generation release.
