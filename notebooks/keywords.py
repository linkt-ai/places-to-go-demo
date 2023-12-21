from typing import Dict, List

import pandas as pd
import numpy as np

from openai import OpenAI

FILE_PATH = "../data/keyword_vectorstore.pkl"


class KeywordVectorstore:
    """A vectorstore of the keywords.

    This is used to generate keyword sets for entities.
    """

    def _load(self) -> pd.DataFrame:
        """Loads the keyword vectorstore from the given file path.

        Returns:
            pd.DataFrame: The loaded keyword vectorstore.
        """
        return pd.read_pickle(FILE_PATH)

    def _search(self, embedding: List[float]) -> List[str]:
        """Searches for the most similar keywords to the given embedding.

        Args:
            embedding (List[float]): The embedding to search for.

        Returns:
            List[str]: The most similar keywords to the given embedding.
        """
        vectorstore = self._load()
        vectorstore["score"] = vectorstore.vector.apply(lambda x: np.dot(x, embedding))
        vectorstore.sort_values(by="score", ascending=False, inplace=True)

        top_keywords = [
            (row["keyword"], row["score"])
            for index, row in vectorstore[["keyword", "score"]].head(3).iterrows()
        ]
        return top_keywords

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
        return keyword_sets


client = OpenAI()


def embed_terms(terms: List[str]):
    response = client.embeddings.create(input=terms, model="text-embedding-ada-002")
    return [datum.embedding for datum in response.data]
