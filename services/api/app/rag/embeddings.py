from __future__ import annotations

import numpy as np
from openai import AsyncOpenAI

from ..settings import Settings


class OpenAIEmbeddingProvider:

    def __init__(
        self,
        settings: Settings,
    ):
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key
        )

        self.model = (
            settings.openai_embedding_model
        )

    async def embed(
        self,
        text: str,
    ) -> np.ndarray:

        response = (
            await self.client.embeddings.create(
                model=self.model,
                input=text,
            )
        )

        if not response.data:
            raise ValueError(
                "OpenAI embedding 결과가 없습니다."
            )

        return np.array(
            response.data[0].embedding,
            dtype=np.float32,
        )

    async def embed_batch(
        self,
        texts: list[str],
    ) -> list[np.ndarray]:

        if not texts:
            return []

        response = (
            await self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
        )

        if not response.data:
            raise ValueError(
                "OpenAI embedding 결과가 없습니다."
            )

        # API 응답 순서대로 정렬
        data = sorted(
            response.data,
            key=lambda item: item.index,
        )

        return [
            np.array(
                item.embedding,
                dtype=np.float32,
            )
            for item in data
        ]