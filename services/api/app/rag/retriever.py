from __future__ import annotations

from pathlib import Path

from .chunker import chunk_text
from .embeddings import OllamaEmbeddingProvider
from .loader import load_documents
from .vector_store import VectorStore


class Retriever:

    def __init__(
        self,
        embedding_provider: OllamaEmbeddingProvider,
        knowledge_path: str | None = None,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = None
        self.initialized = False

        # retriever.py 위치:
        # services/api/app/rag/retriever.py
        #
        # parents[1] = services/api/app
        base_dir = Path(__file__).resolve().parents[1]

        if knowledge_path is None:
            self.knowledge_path = (
                base_dir / "data" / "knowledge"
            )
        else:
            self.knowledge_path = Path(
                knowledge_path
            ).resolve()

        print(
            f"[RAG] knowledge path: {self.knowledge_path}"
        )

    async def initialize(self):
        print("[RAG] initialize 시작")

        documents = load_documents(self.knowledge_path)
        print(f"[RAG] documents = {len(documents)}")

        chunks = []

        for document in documents:
            text_chunks = chunk_text(document["content"])
            chunks.extend(text_chunks)

        print(f"[RAG] total chunks = {len(chunks)}")

        if not chunks:
            raise RuntimeError(
                f"RAG 지식 문서에서 Chunk를 생성하지 못했습니다. "
                f"knowledge_path={self.knowledge_path}"
            )

        # ⭐ 한 번에 embedding
        print(f"[RAG] embedding batch 시작: {len(chunks)}개")

        embeddings = await self.embedding_provider.embed_batch(chunks)

        print("[RAG] 모든 embedding 완료")

        dimension = len(embeddings[0])

        self.vector_store = VectorStore(dimension)

        self.vector_store.add(
            chunks,
            embeddings,
        )

        print("[RAG] vector store 초기화 완료")

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:

        if not self.initialized:
            raise RuntimeError(
                "Retriever가 초기화되지 않았습니다."
            )

        query_embedding = (
            await self.embedding_provider.embed(
                query
            )
        )

        return self.vector_store.search(
            query_embedding,
            top_k,
        )