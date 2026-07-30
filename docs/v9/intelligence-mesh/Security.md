# Security

Reads are RBAC-compatible and constrained by tenant, workspace, and knowledge
namespace. Metadata passes through recursive secret filtering. Never place
credentials, evidence payloads, hidden reasoning, or chain-of-thought in mesh
metadata.
