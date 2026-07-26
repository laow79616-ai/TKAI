from knowledge_platform import KnowledgePlatform, KnowledgeStatus, Scope
from knowledge_platform.chunking import FixedSizeChunker
from knowledge_platform.citations import create_citation
from knowledge_platform.connectors import BoundedMemoryConnector, ConnectorRequest
from knowledge_platform.documents import DocumentStore
from knowledge_platform.parsing import TextParser
from knowledge_platform.permissions import PermissionService
from knowledge_platform.ranking import rank
from knowledge_platform.retrieval import Candidate


def scope(tenant: str = "tenant-a") -> Scope:
    return Scope(tenant, "workspace-a", "namespace-a")


def payload() -> dict[str, object]:
    return {
        "id": "kb-1",
        "name": "Knowledge",
        "description": "Docs",
        "owner": "alice",
        "tenant": "tenant-a",
        "workspace": "workspace-a",
        "namespace": "namespace-a",
    }


def test_lifecycle_and_tenant_isolation() -> None:
    platform = KnowledgePlatform()
    item = platform.create_base(payload())
    assert item.status is KnowledgeStatus.DRAFT
    assert (
        platform.transition(item.id, scope(), "indexing").status
        is KnowledgeStatus.INDEXING
    )
    assert (
        platform.transition(item.id, scope(), "ready").status is KnowledgeStatus.READY
    )
    try:
        platform.bases.get(item.id, scope("tenant-b"))
    except PermissionError:
        pass
    else:
        raise AssertionError("cross-tenant access must fail")


def test_documents_parsing_chunking_ranking_citations() -> None:
    store = DocumentStore()
    document = store.upload(
        {
            "id": "doc-1",
            "knowledge_base_id": "kb-1",
            "name": "Guide",
            "content_type": "text/markdown",
            "metadata": {"token": "secret"},
        },
        b"# Intro\nenterprise knowledge",
        scope(),
    )
    assert document.metadata["token"] == "[REDACTED]"
    assert store.update(document.id, b"updated", scope()).version == 2
    parsed = TextParser().parse(b"# Intro\nenterprise knowledge")
    chunks = FixedSizeChunker(size=20, overlap=2).chunk(
        document.id, parsed.text, parsed.metadata
    )
    citation = create_citation(chunks[0], page=1, section="Intro")
    assert citation.id == create_citation(chunks[0], page=1, section="Intro").id
    assert rank((Candidate(chunks[0], 10), Candidate(chunks[0], 5)))[0].score == 1


def test_permissions_connectors_metrics() -> None:
    permissions = PermissionService()
    permissions.grant("kb-1", "agent", "support", ["read", "export"])
    assert permissions.check("kb-1", "agent", "support", "read")
    connector = BoundedMemoryConnector({"a": b"A"})
    assert connector.import_documents(ConnectorRequest(("a",), limit=1)) == (b"A",)
    platform = KnowledgePlatform()
    platform.create_base(payload())
    assert platform.metrics.snapshot()["knowledge_bases_total"] == 1
