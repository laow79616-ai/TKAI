# Templates

`TemplateManager` is the single template catalog API. It accepts an optional
root path and supports `list`, `manifest`, `list_templates`, `get_template`,
`validate_template`, and `validate_all` for backward compatibility.

Template manifests may be `template.yaml` or `template.json`. `TemplateManifest`
normalizes both formats into the typed metadata model. The historical
`tkai.template_engine.TemplateManager` import resolves to this same class.
