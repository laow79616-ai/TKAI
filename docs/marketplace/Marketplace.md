# Enterprise Marketplace

TKAI V2.3 provides an additive, transport-neutral Enterprise Marketplace for
agents, plugins, workflows, prompts, datasets, knowledge, models, templates,
and extensions. `EnterpriseMarketplace` is the reference in-memory service.
It performs no network access and does not change the existing Marketplace V5
or enterprise plugin marketplace contracts.

Catalog discovery supports text search, category, tag, store kind, featured,
verified, and download-ranked trending filters. Categories and tags are
derived from the latest release of every package.

The HTTP adapter exposes `/marketplace`, `/packages`, `/publishers`,
`/licenses`, `/reviews`, and `/downloads`. Existing server package and
publisher routes remain authoritative for their established V6 resources.
