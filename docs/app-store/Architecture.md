# Enterprise App Store Architecture

The TKAI V3.1 Enterprise App Store is a transport-neutral domain service exposed
under `/app-store`. It integrates with the Enterprise Workflow Platform,
Enterprise Knowledge Platform, AI Application Center, Enterprise Agent Runtime,
Plugin Marketplace, Enterprise Platform, Cloud Native deployment, AI Studio, and
Enterprise Marketplace without replacing their APIs. Docker, Kubernetes, CI/CD,
and observability remain shared platform capabilities.

The store is divided into catalog, applications, publishers, packages, releases,
installation, updates, licenses, subscriptions, reviews, moderation,
verification, compatibility, permissions, analytics, dashboard, and API
packages. In-memory repositories are intentionally replaceable persistence
boundaries. Billing is represented only by subscription and invoice references;
the existing system has no payment-processing abstraction suitable for reuse.

Every object is tenant, organization, and workspace scoped. Packages reference
immutable external artifacts and instructions are declarative. The store never
executes package shell commands or performs unrestricted network access.
