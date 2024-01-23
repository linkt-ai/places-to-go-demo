"""The pinecone module contains the Pinecone client and index.

The pinecone_index object should be exported from this module for use in other modules.
"""
from pinecone import Pinecone

from .config import settings


pinecone_client = Pinecone(
    api_key=settings.PINECONE_API_KEY, environment=settings.PINECONE_ENVIRONMENT
)
pinecone_index = pinecone_client.Index(settings.PINECONE_INDEX)
