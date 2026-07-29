# V8 Compatibility

V8 is additive. It does not replace or alter V6/V7 kernels, TikTok modules,
existing OpenAPI routes, the dashboard, or AI Studio. Compatibility registry
defaults explicitly publish these promises:

- TKAI V6 (`6.x`)
- TKAI V7 (`7.x`)
- existing TikTok modules
- existing OpenAPI
- existing Dashboard
- existing AI Studio

The V8 server integration only adds `/v8/*` GET routes. No existing route,
response, package version, action, or business rule is changed.
