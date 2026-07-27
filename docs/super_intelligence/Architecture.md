# Architecture

The Enterprise AI Super Intelligence Platform is a framework-neutral,
in-process control plane. Domain records are owned by an intelligence profile
and isolated by tenant and workspace. Collective reasoning and knowledge
synthesis feed strategic plans, world models, predictions, and optimization;
governed decisions feed adaptation, improvement, evaluation, and monitoring.

All components integrate through typed Python contracts. The optional API
adapter registers routes on a FastAPI-compatible host without making FastAPI a
core dependency. This preserves all existing TKAI platforms and allows their
services to act as evidence, policy, memory, coordination, or execution
providers.
