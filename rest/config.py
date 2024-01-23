"""The logger module sets up the logger for the application."""
import os
import sys
import logging

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Setup the logger to be used throughout the application
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

load_dotenv(".env")


class Settings(BaseSettings):
    """This class defines the application settings.

    Attributes:
        NEO4J_DATABASE_USERNAME: The username for the Neo4J database.
        NEO4J_DATABASE_URL: The URL for the Neo4J database.
        NEO4J_DATABASE_PASSWORD: The password for the Neo4J database.

        CLERK_SECRET_KEY: The secret key for Clerk.

        PINECONE_API_KEY: The API key for Pinecone.
        PINECONE_ENVIRONMENT: The environment for Pinecone.
        PINECONE_INDEX: The index for Pinecone.
    """

    # Neo4J Database Settings
    NEO4J_DATABASE_USERNAME: str = os.getenv("NEO4J_DATABASE_USERNAME")
    NEO4J_DATABASE_URL: str = os.getenv("NEO4J_DATABASE_URL")
    NEO4J_DATABASE_PASSWORD: str = os.getenv("NEO4J_DATABASE_PASSWORD")

    CLERK_SECRET_KEY: str = os.getenv("CLERK_SECRET_KEY")

    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX")


# Initialize this module's settings when the file is first defined
settings = Settings()
