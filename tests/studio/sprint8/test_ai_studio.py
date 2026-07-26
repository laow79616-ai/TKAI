"""Sprint-8 Enterprise AI Studio domain and contract tests."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

import pytest

from studio.api import STUDIO_RESOURCE_PATHS, studio_v23_routes
from studio.chat import Attachment, ChatStudio
from studio.dashboard import STUDIO_DASHBOARD_PAGES
from studio.evaluation import EvaluationCase, EvaluationStudio
from studio.knowledge import Chunk, Document, KnowledgeService
from studio.metrics import STUDIO_METRICS, StudioMetrics
from studio.models import ModelProfile, ModelProvider, ModelRegistry
from studio.projects import ProjectManager
from studio.prompts import PromptStudio
from studio.rag import RagPipeline, RetrievedDocument
from studio.workflows import (
    NodeType,
    VisualWorkflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowStudio,
)


class Ids:
    def __init__(self) -> None:
        self.value = 0

    def __call__(self, prefix: str) -> str:
        self.value += 1
        return f"{prefix}-{self.value}"


class Chunker:
    def chunk(self, document: Document) -> Sequence[Chunk]:
        return (Chunk(document.document_id, 0, document.content),)


class Embedder:
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        return tuple((float(len(text)),) for text in texts)


class Index:
    def __init__(self) -> None:
        self.items: list[Chunk] = []

    def add(
        self,
        namespace: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[Sequence[float]],
    ) -> None:
        assert namespace and len(chunks) == len(vectors)
        self.items.extend(chunks)

    def search(
        self, namespace: str, vector: Sequence[float], limit: int
    ) -> Sequence[Chunk]:
        return self.items[:limit]


class Retriever:
    def retrieve(self, query: str, limit: int) -> Sequence[RetrievedDocument]:
        return (
            RetrievedDocument("doc-1", f"{query} answer", 0.8, "kb://one"),
            RetrievedDocument("doc-2", "secondary", 0.2, "kb://two"),
        )[:limit]


class Ranker:
    def rank(
        self, query: str, documents: Sequence[RetrievedDocument]
    ) -> Sequence[RetrievedDocument]:
        return tuple(sorted(documents, key=lambda item: -item.score))


def test_project_lifecycle_clone_export_and_import() -> None:
    manager = ProjectManager(Ids())
    original = manager.create("Alpha")
    renamed = manager.rename(original.project_id, "Beta")
    archived = manager.archive(original.project_id)
    clone = manager.clone(original.project_id)
    imported = manager.import_project(manager.export_project(clone.project_id))

    assert renamed.name == "Beta"
    assert archived.archived is True
    assert clone.project_id != original.project_id
    assert imported.project_id != clone.project_id
    assert manager.list() == (clone, imported)


def test_prompt_versions_preview_diff_validation_and_testing() -> None:
    studio = PromptStudio(Ids())
    first = studio.create("Hello {{name}}")
    studio.version(first.prompt_id, "Welcome {{name}}")

    assert studio.preview(first.prompt_id, {"name": "Ada"}) == "Welcome Ada"
    assert studio.test(first.prompt_id, (({"name": "Ada"}, "Ada"),)) == (True,)
    assert "-Hello" in studio.diff(first.prompt_id, 1, 2)
    with pytest.raises(ValueError, match="syntax"):
        studio.create("Bad {{name}")


def test_chat_sessions_stream_history_attachments_and_portability() -> None:
    studio = ChatStudio(Ids())
    session = studio.create_session("project-1")
    studio.add_message(
        session.session_id,
        "user",
        "hello",
        (Attachment("a.txt", "text/plain", "store://a", 5),),
    )

    async def chunks():
        for value in ("a", "b"):
            yield value

    async def collect() -> list[str]:
        return [value async for value in studio.stream(chunks())]

    assert asyncio.run(collect()) == ["a", "b"]
    restored = studio.import_session(studio.export_session(session.session_id))
    assert restored.messages[0].attachments[0].name == "a.txt"


def test_knowledge_ingestion_rag_citations_and_metrics() -> None:
    metrics = StudioMetrics()
    index = Index()
    knowledge = KnowledgeService(Ids(), Chunker(), Embedder(), index, metrics)
    base = knowledge.create_base("project-1", "Docs")
    collection = knowledge.create_collection(base.knowledge_id, "Guides", "tenant-a")
    knowledge.add_documents(
        base.knowledge_id,
        collection.collection_id,
        (Document("doc-1", "TKAI guide"),),
    )
    result = RagPipeline(Retriever(), Ranker(), metrics).query("TKAI")

    assert index.items[0].content == "TKAI guide"
    assert result.citations[0].source == "kb://one"
    assert RagPipeline.evaluate(result, {"doc-1"}) == {
        "precision": 0.5,
        "recall": 1.0,
    }
    assert metrics.snapshot()["knowledge_documents"] == 1
    assert metrics.snapshot()["rag_queries"] == 1


def test_models_evaluation_workflow_api_dashboard_and_metrics_contracts() -> None:
    registry = ModelRegistry()
    registry.register(ModelProfile("primary", ModelProvider.OPENAI, "gpt"))
    registry.register(ModelProfile("fallback", ModelProvider.OLLAMA, "local"))
    registry.set_default("chat", "primary", ("fallback",))
    assert registry.resolve("chat", {"primary"}).profile_id == "fallback"

    evaluation = EvaluationStudio(Ids())
    baseline = evaluation.run("baseline", (EvaluationCase("one", "a", "A"),), str.upper)
    candidate = evaluation.run(
        "candidate", (EvaluationCase("one", "a", "A"),), str.upper
    )
    assert evaluation.regression(baseline.run_id, candidate.run_id)

    workflow = VisualWorkflow(
        "flow-1",
        "project-1",
        "Agent flow",
        (
            WorkflowNode("agent", NodeType.AGENT),
            WorkflowNode("checkpoint", NodeType.CHECKPOINT),
        ),
        (WorkflowEdge("agent", "checkpoint"),),
    )
    run = WorkflowStudio(Ids(), lambda _: ("checkpoint",)).save(workflow)
    assert run.name == "Agent flow"

    assert {item.path.removeprefix("/api") for item in studio_v23_routes()} == set(
        STUDIO_RESOURCE_PATHS
    )
    assert len(STUDIO_DASHBOARD_PAGES) == 8
    assert set(StudioMetrics().snapshot()) == set(STUDIO_METRICS)
