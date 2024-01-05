from typing import Dict, List

import pandas as pd
import numpy as np

from openai import OpenAI

FILE_PATH = "../data/persona_dataframe.pkl"


class PersonaVectorstore:
    """A vectorstore of the personas.

    This is used to generate persona relationships for entities.
    """

    def __init__(self, num_results: int = 3):
        """Initializes the persona vectorstore.

        Args:
            num_results (int, optional): The number of results to return. Defaults to 3.
        """
        self.num_results = num_results
        self.vectorstore = pd.read_pickle(FILE_PATH)

    def _search(self, embedding: List[float]) -> List[str]:
        """Searches for the most similar personas to the given embedding.

        Args:
            embedding (List[float]): The embedding to search for.

        Returns:
            List[str]: The most similar personas to the given embedding.
        """
        # Compute the raw similarit scores
        vectorstore = self.vectorstore.copy()
        vectorstore["score"] = vectorstore.embeddings.apply(
            lambda x: np.dot(x, embedding)
        )

        # Normalize scores using Min-Max normalization
        min_score = vectorstore.score.min()
        max_score = vectorstore.score.max()
        vectorstore["score"] = vectorstore.score.apply(
            lambda x: (x - min_score) / (max_score - min_score)
        )

        # Sort by score and return the top results
        vectorstore.sort_values(by="score", ascending=False, inplace=True)
        top_personas = vectorstore.head(self.num_results)

        # Variable thresholds based on the current number of selected personas
        threshold_1 = 0.75
        threshold_2 = 0.65

        selected_personas = []
        for _, row in top_personas.iterrows():
            if len(selected_personas) < 1 and row.score:
                selected_personas.append((row.persona, row.score))
            elif len(selected_personas) < 2 and row.score >= threshold_1:
                selected_personas.append((row.persona, row.score))
            elif len(selected_personas) < 3 and row.score >= threshold_2:
                selected_personas.append((row.persona, row.score))

        return selected_personas

    def search_keywords(self, embeddings: List[List[float]]) -> List[List[str]]:
        """Search for the most similar keywords to the given embeddings.

        Args:
            embeddings (List[List[float]]): The embeddings to search for.

        Returns:
            List[List[str]]: The most similar keywords to the given embeddings.
        """
        results = [self._search(embedding) for embedding in embeddings]
        assert len(results) == len(embeddings)
        return results

    def get_keywords(self, posts_query_terms: List[str]) -> Dict[str, str]:
        """Gets the most similar keywords to the given posts.

        Args:
            posts (Dict[str, str]): The posts to get the keywords for.
                - { post_id: post_query_term }

        Returns:
            Dict[str, str]: The most similar keywords to the given posts.
        """
        # Embed all the post query terms
        embeddings = embed_terms(posts_query_terms)

        # Search for the most similar keywords to the embeddings
        keyword_sets = [self._search(embedding) for embedding in embeddings]

        # Return the keyword sets. These should be zipped with the posts: zip(posts, keyword_sets), and then
        # the posts can be annotated with the keywords to create the cypher entities.
        assert len(keyword_sets) == len(posts_query_terms)
        return keyword_sets


client = OpenAI()


def embed_terms(terms: List[str]):
    """Helper function to embed terms."""
    response = client.embeddings.create(input=terms, model="text-embedding-ada-002")
    return [datum.embedding for datum in response.data]
