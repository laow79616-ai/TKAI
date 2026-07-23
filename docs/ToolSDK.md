# TKAI 2.0 Tool SDK

## Architecture

`tkai.sdk.tools` is a vendor-neutral, reference-only Tool SDK. It supplies
descriptors, parameter schemas, explicit context/request/result values, a
thread-safe registry, a factory, middleware, hook contracts, and deterministic
local reference tools. It is independent from the existing plugin decorator.

## Registration and decorator

`ToolRegistry` and `ToolFactory` require explicit application registration.
`@tool` derives a compact schema from a Python callable signature and registers
the resulting `FunctionTool` in either a supplied registry or the SDK-local
default registry. It does not expose a global MCP, shell, browser, HTTP, or
filesystem capability.

## Execution

Tools receive immutable requests and caller-supplied `ToolContext` values.
Synchronous execution supports validation, cancellation, and immediate timeout
states; `aexecute` is reserved as an async interface. Middleware and hook
contracts observe before/after/error boundaries without taking ownership of
dependencies.

## Reference tools

`EchoTool`, `MathTool`, and `MemoryTool` are deterministic local examples.
`MemoryTool` reads only a compatible memory object explicitly provided through
context. None reads credentials, environment values, disk, or network state.

## Current limitations

This sprint intentionally does not implement MCP, OpenAI tool calling, browser,
filesystem, HTTP, Python, SQL, shell, remote transports, or production timeout
enforcement. Reference tools are not production sandboxed executors.
