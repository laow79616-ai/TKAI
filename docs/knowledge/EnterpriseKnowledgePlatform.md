# Enterprise Knowledge Platform

## Architecture

`knowledge_platform` is a dependency-light, tenant-scoped domain layer. Its
stores are bounded reference implementations. Parsing, embedding, retrieval,
reranking, connector, URL import, caching, and benchmark behaviors are contracts.

## Knowledge lifecycle

Knowledge bases move through Draft, Indexing, Ready, Paused, Failed, Archived,
and Deleted states using an explicit transition graph.

## Ingestion

PDF, DOCX, TXT, Markdown, HTML, CSV, and JSON are accepted within content and
size policy. URL import fetches one validated URL only. Connector requests name
explicit resource IDs and have hard limits; crawling is not implemented.

## Parsing

Parsers return metadata, page and section boundaries, encoding information, and
structured recoverable or terminal errors.

## Chunking

Fixed and recursive strategies support overlap, token limits, and metadata
preservation. Semantic chunking is an interface.

## Embeddings

Providers declare dimensions. The service validates batches, retries transient
failures, enforces timeouts, and exposes a cache interface. Credentials come
from deployment configuration and are never stored here.

## Retrieval

Vector and keyword contracts receive tenant, workspace, and namespace scope.
Hybrid retrieval merges candidates using filters and bounded Top K.

## Ranking

Ranking normalizes scores, applies thresholds, deduplicates, and limits results.
Model reranking is an interface.

## Citations

Citations include document, page, section, chunk, source URL, excerpt, and a
deterministic stable ID.

## Permissions

Private, team, organization, tenant, and public visibility are distinct from
Read, Write, Manage, Share, and Export grants. Sharing supports users, teams,
organizations, applications, agents, and workflows.

## Connectors

Google Drive, SharePoint, OneDrive, S3-compatible, database, and website
interfaces are provided. The memory implementation is bounded and performs no
filesystem or network access.

## Evaluation

Regression datasets and benchmarks cover relevance, citation accuracy, coverage,
and latency.

## Security

Every resource is isolated by tenant, workspace, and namespace. File size,
document count, content type, Top K, explicit connector resource, and connector
result limits are mandatory. Sensitive metadata is redacted. Core code performs
no unrestricted filesystem or network access and logs no credentials.
