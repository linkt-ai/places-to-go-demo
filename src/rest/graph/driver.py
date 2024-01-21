"""This file defines a simple helper function to get a driver for the Neo4J database."""
from neo4j import GraphDatabase, Driver

from ..config import settings


DB_USER = settings.NEO4J_DATABASE_USERNAME
DB_URL = settings.NEO4J_DATABASE_URL
DB_PASSWORD = settings.NEO4J_DATABASE_PASSWORD


def get_driver() -> Driver:
    """Get a driver for the Neo4J database.

    Returns:
        neo4j.Driver: The driver for the Neo4J database.
    """
    return GraphDatabase.driver(DB_URL, auth=(DB_USER, DB_PASSWORD))
