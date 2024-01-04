from typing import List

import pandas as pd
import numpy as np
from openai import OpenAI


CATEGORIES = [
    "Restaurant",
    "Activity",
    "Museum",
    "Outdoor Exploration",
    "Shopping",
    "Nightlife",
    "Historical Site",
    "Amusement Park",
    "Experience",
    "Relaxation",
]


class CategoryVectorstore:
    def __init__(self):
        embeddings = self._embed(CATEGORIES)
        data = [
            {"category": category, "embedding": embedding}
            for category, embedding in zip(CATEGORIES, embeddings)
        ]
        self.vectorstore = pd.DataFrame(data)

    def _embed(self, terms: List[str]) -> List[List[float]]:
        response = OpenAI().embeddings.create(
            model="text-embedding-ada-002",
            input=terms,
        )
        return [result.embedding for result in response.data]

    def _search(self, embedding: List[float]) -> str:
        """Search for the closest category to a given embedding"""
        vectorstore = self.vectorstore.copy()
        vectorstore["score"] = vectorstore.embedding.apply(
            lambda x: np.dot(x, embedding)
        )
        vectorstore.sort_values(by="score", ascending=False, inplace=True)

        category = vectorstore.iloc[0].category
        return category

    def search_categories(self, embeddings: List[List[float]]) -> List[str]:
        """Search for the closest category to a list of embeddings"""
        results = [self._search(embedding) for embedding in embeddings]
        assert len(results) == len(embeddings)
        return results

    def get_categories(self, terms: List[str]) -> List[str]:
        """Get the categories for a list of terms"""
        embeddings = self._embed(terms)
        results = [self._search(embedding) for embedding in embeddings]
        assert len(results) == len(terms)
        return results
