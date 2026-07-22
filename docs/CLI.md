# AI CLI Guide

`tkai ai` is a thin presentation layer. It parses options, invokes
`AICommandService`, and formats service results; provider, transport, runtime,
capability, and fallback logic remain in framework services.

## Commands

```text
tkai ai doctor [--json | --text]
tkai ai providers [--json]
tkai ai capabilities [--provider NAME] [--model NAME] [--json]
tkai ai fallback [--json]
tkai ai validate-config [--json]
tkai ai version [--json]
tkai ai info [--json]
```

`doctor` defaults to text. `validate-config` invokes only provider registry,
configuration, and capability diagnostics. `providers` reports aliases,
default selection, provider capability summary, and model override count.

Existing `tkai ai list`, `models`, `chat`, `embed`, and `info NAME` commands
remain compatibility commands. `tkai ai info` without a name shows the new
framework summary.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Successful command or diagnostics without errors |
| 1 | Validation diagnostics reported an error |
| 2 | Invalid or missing configuration |
| 3 | Runtime/provider service error |

Commands print concise error messages and do not print tracebacks. JSON output
uses only safe framework metadata; credentials and authorization headers are
never included.
