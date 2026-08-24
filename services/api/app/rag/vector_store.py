from __future__ import annotations

import faiss
import numpy as np


class VectorStore:
    def __init__(self, dimension: int):
        self.index = faiss.IndexFlatL2(dimension)

        self.documents: list[str] = []

    def add(
        self,
        documents: list[str],
        embeddings: list[np.ndarray],
    ) -> None:

        vectors = np.vstack(embeddings)

        self.index.add(vectors)

        self.documents.extend(documents)

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 3,
    ) -> list[str]:

        query = np.array(
            [query_embedding],
            dtype=np.float32,
        )

        indices = self.index.search(
            query,
            top_k,
        )

        results = []

        for index in indices[0]:

            if index == -1:
                continue

            results.append(
                self.documents[index]
            )

        return results