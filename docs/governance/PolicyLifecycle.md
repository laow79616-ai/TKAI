# Policy Lifecycle

Policies contain an ID, name, description, scope, owner, version, rules,
controls, and metadata. Valid transitions are:

`draft -> review -> approved -> active -> suspended -> active`

Policies may move from active or suspended to deprecated, then archived.
Draft, review, and approved policies may also be archived where defined.
Archived policies are terminal. Invalid transitions fail closed.
