# Planning

Plans consist of a goal, prioritized subtasks, dependencies, and a deterministic
execution order. The planner validates unique identifiers and known dependencies,
uses topological sorting, and rejects loops. Security execution limits cap plan
size and depth before planning begins.
