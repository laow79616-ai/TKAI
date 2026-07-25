# Configuration

`Settings` is the single nested-settings implementation. It supports dotted
keys, deep merge, reset, defensive copies, and environment loading.

`ConfigManager` subclasses `Settings` to retain its established YAML loading
and saving API. Precedence is defaults, then user configuration, then project
configuration. User configuration is `~/.tkai/config.yaml`; project
configuration is `.tkai/config.yaml` below the selected root.
