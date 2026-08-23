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
            "nomic-embed-text",
        )

    async def embed(self, text: str) -> np.ndarray:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
            )

            response.raise_for_status()

            data = response.json()

        return np.array(
            data["embedding"],
            dtype=np.float32,
        )