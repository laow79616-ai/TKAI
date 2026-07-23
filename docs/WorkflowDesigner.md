# TKAI Studio Workflow Designer

The reference Workflow Designer is a serializable React/TypeScript product-layer
model. Its canvas stores grid, zoom, pan, selection, multi-selection, and viewport
state separately from UI rendering.

Nodes support Task, Condition, Loop, Retry, Parallel, Branch, and End with id,
title, position, inputs, outputs, metadata, and enabled state. Edges are local
source/target declarations with metadata; self-connections and duplicates are
rejected by the connect helper.

The validator reports empty workflows, missing Task start or End nodes,
disconnected nodes, duplicate ids, invalid edges, and duplicate edges. Cycle
detection remains a reserved future validation extension.

The designer supports JSON import/export and store snapshot/restore. Its REST
mapping converts the visual model into the frozen Workflow API payload and uses
only existing create/update/list/delete Workflow client methods. The reference
Simple Chat Flow contains Task, Condition, and End nodes.

This sprint has no drag-and-drop UI, execution monitoring, Agent chat, backend
change, SDK change, or Runtime execution capability.
