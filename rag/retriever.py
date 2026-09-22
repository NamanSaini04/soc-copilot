from __future__ import annotations

from dataclasses import asdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from rag.ingestion import Chunk


class LocalRetriever:
    """Auditable MVP retriever. Replaceable with sentence-transformers + FAISS."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        self.matrix = self.vectorizer.fit_transform([c.text for c in chunks])

    def search(self, query: str, top_k: int = 3, min_score: float = 0.08, section: str | None = None) -> list[dict]:
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]
        order = scores.argsort()[::-1]
        results = []
        for idx in order:
            chunk = self.chunks[int(idx)]
            score = float(scores[int(idx)])
            if score < min_score or (section and section.lower() not in chunk.section.lower()):
                continue
            results.append({**asdict(chunk), "score": round(score, 4)})
            if len(results) == top_k: break
        return results

