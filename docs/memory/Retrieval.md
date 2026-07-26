# Memory Retrieval

Search supports keyword, similarity, and hybrid scoring. Every query is first
restricted to tenant and workspace; owner-private and shared-memory visibility
is then applied. Namespace and exact metadata filters run before ranking.
`top_k` bounds the response and `threshold` drops weak results. The reference
index uses token cosine similarity and can be replaced by a vector/search
backend while retaining `SearchQuery` and `SearchResult`.
