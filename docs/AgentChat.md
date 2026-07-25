# TKAI Studio Agent Chat

Studio Agent Chat is an offline, serializable reference product layer. It owns
conversation presentation state, not provider/runtime execution. It does not
change the frozen Studio REST contract, TKAI SDK public API, V1.x Runtime,
Workflow Designer, or Execution Monitor.

## Conversation model

A `Conversation` has an explicit session ID, ordered immutable-style message
values, and a local `ConversationMemory` context. Messages carry a user,
assistant, system, or tool role; a UI status; safe JSON metadata; optional tool
calls; and optional workflow/execution references. The state can be JSON
snapshotted and restored after basic validation. The reference implementation
does not persist memory, write files, or read user configuration.

## Explicit Agent SDK bridge

The frontend declares `AgentSDKAdapter`, an explicit host-injected bridge whose
`chat` implementation may delegate to `tkai.sdk.Agent.chat`. This boundary is
intentional: the frontend neither imports nor calls a Runtime, creates a
provider, accesses credentials, or performs a hidden network request. A host
must configure any real SDK adapter separately.

## Chat UI contracts

`AgentChatPage`, conversation sidebar/history, message, input, typing/status,
tool-call, workflow, execution, empty, and error components are prop-driven
contracts only. They do not fetch directly and retain no background timers.

## Execution, workflows, memory, and tools

Chat output may link to a workflow ID, tool-call summary, and execution ID.
`loadConversationExecution` consumes only the existing typed
`GET /executions/{execution_id}` client method, allowing the Execution Monitor
to present that record. It adds no endpoint and does not fabricate execution
events. Conversation memory is an explicit bounded-in-usage context value; it
is not a persistent Memory SDK backend.

## Reference data and limitations

The included reference conversation demonstrates a deterministic assistant
reply, tool summary, workflow link, and execution link solely for tests,
documentation, and UI contracts. There is no Agent Chat REST endpoint,
streaming transport, WebSocket, authentication, database persistence, real
provider, or automatic execution. The validation environment has no frontend
dependency installation, so Vite lint/typecheck remain for a Node-enabled
frontend build environment; offline Python source-contract tests are used here.
