from __future__ import annotations

from pathlib import Path

from .chunker import chunk_text
from .embeddings import OpenAIEmbeddingProvider
from .loader import load_documents
from .vector_store import VectorStore


class Retriever:

    def __init__(
        self,
        embedding_provider: OpenAIEmbeddingProvider,
        knowledge_path: str | None = None,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store: VectorStore | None = None
        self.initialized = False

        # =====================================================
        # knowledge path
        #
        # services/api/app/rag/retriever.py
        #                    ↓
        # services/api/app
        #                    ↓
        # services/api/app/data/knowledge
        # =====================================================

        base_dir = Path(__file__).resolve().parents[1]

        if knowledge_path is None:
            self.knowledge_path = (
                base_dir
                / "data"
                / "knowledge"
            )
        else:
            self.knowledge_path = Path(
                knowledge_path
            ).resolve()

        print(
            f"[RAG] knowledge path: "
            f"{self.knowledge_path}"
        )

    async def initialize(self) -> None:

        # 이미 초기화되어 있으면 다시 하지 않음
        if self.initialized:
            print("[RAG] 이미 초기화됨")
            return

        print("[RAG] initialize 시작")

        # -----------------------------------------------------
        # 1. 문서 로딩
        # -----------------------------------------------------

        documents = load_documents(
            self.knowledge_path
        )

        print(
            f"[RAG] documents = {len(documents)}"
        )

        # -----------------------------------------------------
        # 2. Chunk 생성
        # -----------------------------------------------------

        chunks: list[str] = []

        for document in documents:

            text_chunks = chunk_text(
                document["content"]
            )

            chunks.extend(text_chunks)

        print(
            f"[RAG] total chunks = {len(chunks)}"
        )

        if not chunks:
            raise RuntimeError(
                "RAG 지식 문서에서 Chunk를 "
                "생성하지 못했습니다. "
                f"knowledge_path={self.knowledge_path}"
            )

        # -----------------------------------------------------
        # 3. Embedding
        # -----------------------------------------------------

        print(
            f"[RAG] embedding batch 시작: "
            f"{len(chunks)}개"
        )

        embeddings = (
            await self.embedding_provider.embed_batch(
                chunks
            )
        )

        print(
            f"[RAG] embedding 완료: "
            f"{len(embeddings)}개"
        )

        if not embeddings:
            raise RuntimeError(
                "Embedding 결과가 없습니다."
            )

        if len(embeddings) != len(chunks):
            raise RuntimeError(
                "Chunk와 embedding 개수가 "
                "일치하지 않습니다."
            )

        # -----------------------------------------------------
        # 4. Vector Store 생성
        # -----------------------------------------------------

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

        # ⭐ 중요
        self.initialized = True

        print(
            "[RAG] vector store 초기화 완료"
        )

    async def retrieve(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[str]:

        if not self.initialized:
            raise RuntimeError(
                "Retriever가 초기화되지 않았습니다."
            )

        if self.vector_store is None:
            raise RuntimeError(
                "Vector store가 초기화되지 않았습니다."
            )

        # Query embedding
        query_embedding = (
            await self.embedding_provider.embed(
                query
            )
        )

        # Similarity search
        return self.vector_store.search(
            query_embedding,
            top_k,
        )