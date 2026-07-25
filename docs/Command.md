# Commands

The Typer application is exposed as `tkai.cli:app` and provides `info`, `new`,
`template`, `version`, `doctor`, and `init` commands. Each command package owns
its own Typer sub-application and does not depend on another command module.

The `new` command uses `GeneratorEngine`; template commands use the unified
`TemplateManager`. This keeps CLI behavior separate from framework services.
