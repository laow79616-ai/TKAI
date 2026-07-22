# Generators

`GeneratorEngine` transforms a template directory into an output directory.
It maintains a `VariableManager`, runs `pre_generate` and `post_generate`
hooks, and delegates file rendering to `Scaffold` and `TemplateRenderer`.

Template source files ending in `.j2`, `.jinja`, `.jinja2`, or `.tmpl` are
rendered with Jinja2 and have only that final suffix removed. Other files are
copied unchanged. `BaseGenerator` provides typed common filesystem helpers for
custom generators.
