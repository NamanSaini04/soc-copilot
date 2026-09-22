from pathlib import Path

from rag.ingestion import ingest_directory
from rag.retriever import LocalRetriever

ROOT = Path(__file__).resolve().parents[1]


def test_authentication_query_retrieves_auth_playbook():
    results = LocalRetriever(ingest_directory(ROOT / "knowledge_base")).search("failed login MFA credential reset")
    assert results
    assert any("authentication" in r["path"] for r in results)
    assert all(r["source_id"] and 0 <= r["score"] <= 1 for r in results)

