# Architecture

The Enterprise AI General Intelligence Platform is a framework-neutral,
in-process control plane. Domain records are owned by an intelligence profile
and isolated by tenant and workspace. Awareness feeds intent and goals;
evidence-backed reasoning produces validated plans and predictions; governed
execution feeds learning, reflection, adaptation, and monitoring.

All components integrate through typed Python contracts. The optional API
adapter registers routes on a FastAPI-compatible host without making FastAPI a
core dependency. This preserves all existing TKAI platforms and allows their
services to act as evidence, policy, memory, coordination, or execution
providers.
