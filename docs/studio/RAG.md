# Retrieval-Augmented Generation

The RAG pipeline composes a retriever, ranker, bounded context builder, citation
builder, and precision/recall evaluator. Citations preserve document identity,
source, and a bounded excerpt. Context size is capped before inference and every
query increments `rag_queries`.
