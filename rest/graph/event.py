"""The event.py file defines the Neo4J queries for fetching events."""
from datetime import datetime

from .driver import get_driver
from ..models import Event


def create_event(event: Event, user_id: str) -> bool:
    """Create an event in the database."""
    driver = get_driver()

    with driver.session() as session:
        session.run(
            "MATCH (v: Venue {id: $venue_id}) "  # Find the venue with the given ID
            "MATCH (i: Itinerary {userId: $user_id}) "  # Find the user's itinerary
            "CREATE (e: Event {id: $id, startTime: $start_time, endTime: $end_time, \
                title: $title, url: $url, thumbnailUrl: $thumbnail_url}) "
            # Create a relationship between the event and the itinerary
            "CREATE (i)-[:HAS_EVENT]->(e) "
            # Create a relationship between the event and the venue
            "CREATE (e)-[:AT]->(v) " "RETURN e",
            {
                "venue_id": event.venue_id,
                "user_id": user_id,
                "id": event.id,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "title": event.title,
                "url": event.url,
                "thumbnail_url": event.thumbnail_url,
            },
        )
        return None


def update_event(event_id: str, start: datetime, end: datetime) -> bool:
    """Update the start and end times of an event.

    Args:
        event_id (str): The ID of the event to update.
        start (datetime): The new start time of the event.
        end (datetime): The new end time of the event.

    Returns:
        bool: True if the event was updated, False otherwise.
    """
    driver = get_driver()

    with driver.session() as session:
        result = session.run(
            "MATCH (e: Event {id: $event_id}) "
            "SET e.startTime = $start, e.endTime = $end "
            "RETURN e",
            {
                "event_id": event_id,
                "start": start,
                "end": end,
            },
        )

        summary = result.consume()
        updated_props = summary.counters.properties_set
        return updated_props > 0


def delete_event(event_id: str) -> bool:
    """Delete an event from the database.

    Args:
        event_id (str): The ID of the event to delete.

    Returns:
        bool: True if the event was deleted, False otherwise.
    """

    driver = get_driver()

    with driver.session() as session:
        result = session.run(
            "MATCH (e: Event {id: $event_id}) DETACH DELETE e",
            {
                "event_id": event_id,
            },
        )

        summary = result.consume()
        deleted_nodes = summary.counters.nodes_deleted
        return deleted_nodes > 0
