from __future__ import annotations

import httpx
import numpy as np

from ..settings import Settings


class OllamaEmbeddingProvider:
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_base_url
        self.model = getattr(
            settings,
            "embedding_model",
            "nomic-embed-text:latest",
        )

    async def embed(self, text: str) -> np.ndarray:
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(
        self,
        texts: list[str],
    ) -> list[np.ndarray]:

        if not texts:
            return []

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:

            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": texts,
                },
            )

            response.raise_for_status()

            data = response.json()

        embeddings = data.get("embeddings")

        if not embeddings:
            raise ValueError(
                "Ollama에서 embedding 결과를 받지 못했습니다."
            )

        return [
            np.array(
                embedding,
                dtype=np.float32,
            )
            for embedding in embeddings
        ]