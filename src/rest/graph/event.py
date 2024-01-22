"""The event.py file defines the Neo4J queries for fetching events."""

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
            "CREATE (i)-[:HAS_EVENT]->(e) "  # Create a relationship between the event and the itinerary
            "CREATE (e)-[:AT]->(v) "  # Create a relationship between the event and the venue
            "RETURN e",
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
