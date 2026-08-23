from __future__ import annotations

from .chunker import chunk_text
from .embeddings import OllamaEmbeddingProvider
from .loader import load_documents
from .vector_store import VectorStore
from pathlib import Path


class Retriever:

    def __init__(
        self,
        embedding_provider: OllamaEmbeddingProvider,
        knowledge_path: str = "data/knowledge",
    ):

        self.embedding_provider = embedding_provider
        self.knowledge_path = knowledge_path

        self.vector_store = None

    async def initialize(self):
        print("[RAG] 현재 작업 디렉토리:", Path.cwd())
        print("[RAG] knowledge path:", Path(self.knowledge_path).resolve())

        print("[RAG] knowledge files:")
        for path in Path(self.knowledge_path).rglob("*"):
            print("   ", path, path.stat().st_size, "bytes")

        documents = load_documents(
            self.knowledge_path
        )

        chunks = []

        for document in documents:

            text_chunks = chunk_text(
                document["content"]
            )

            chunks.extend(text_chunks)

        chunks = chunks[:10]
        print(f"[RAG] total chunks = {len(chunks)}")
        embeddings = []

        for chunk in chunks:

            embedding = await self.embedding_provider.embed(
                chunk
            )

            embeddings.append(
                embedding
            )

        dimension = len(
            embeddings[0]
        )

        self.vector_store = VectorStore(
            dimension
        )

        self.vector_store.add(
            chunks,
            embeddings,
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:

        if self.vector_store is None:
            raise RuntimeError(
                "Retriever가 초기화되지 않았습니다."
            )

        query_embedding = await self.embedding_provider.embed(
            query
        )

        return self.vector_store.search(
            query_embedding,
            top_k,
        )