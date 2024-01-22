"""The itinerary.py file defines the Neo4J queries for fetching itineraries."""
from typing import Union

from .driver import get_driver
from ..models import Itinerary, Event


def get_itinerary(user_id: str) -> Union[Itinerary, None]:
    """Get an itinerary for a user.

    Args:
        user_id (str): The user ID.

    Returns:
        Itinerary: The itinerary for the user.
    """
    try:
        driver = get_driver()
        with driver.session() as session:
            result = session.run(
                "MATCH (n: Itinerary) "
                "WHERE n.userId = $user_id "
                "OPTIONAL MATCH (n)-[:HAS_EVENT]->(e:Event)-[:AT]->(v:Venue) "
                "RETURN n, collect({ "
                "id: e.id, "
                "title: e.title, "
                "venueId: v.id, "
                "url: e.url, "
                "thumbnailUrl: e.thumbnailUrl, "
                "startTime: apoc.date.format(e.startTime.epochMillis, 'ms', "
                "'yyyy-MM-dd\\'T\\'HH:mm:ss.SSSZ'), "
                "endTime: apoc.date.format(e.endTime.epochMillis, 'ms', "
                "'yyyy-MM-dd\\'T\\'HH:mm:ss.SSSZ') "
                "}) as events",
                {
                    "user_id": user_id,
                },
            )

            record = result.single()
            itinerary_record = record["n"]

            # Check if the first event is None
            if record["events"][0]["id"] is None:
                events = []
            else:
                events = [
                    Event(
                        id=event["id"],
                        title=event["title"],
                        venue_id=event["venueId"],
                        start_time=event["startTime"],
                        end_time=event["endTime"],
                        url=event["url"],
                        thumbnail_url=event["thumbnailUrl"],
                    )
                    for event in record["events"]
                ]

            itinerary = Itinerary(events=events, **itinerary_record)
            return itinerary
    except TypeError:
        return None


def create_itinerary(
    itinerary: Itinerary,
) -> bool:
    """Create an itinerary for a user.

    Args:
        itinerary: The itinerary to create. Expected to have no events.

    Returns:
        bool: True if the itinerary existed, False otherwise.

    Raises:
        ValueError: If the itinerary has events.
    """
    if itinerary.events:
        raise ValueError("Itinerary should not have events")

    driver = get_driver()
    with driver.session() as session:
        # Delete existing itinerary and related events
        result = session.run(
            """
            MATCH (n:Itinerary) WHERE n.userId = $user_id
            DETACH DELETE n
            RETURN n
            """,
            {"user_id": itinerary.user_id},
        )
        record = result.single()
        itinerary_existed = record is not None

        # Upsert itinerary
        session.run(
            """
            MERGE (n:Itinerary {userId: $user_id})
            ON CREATE SET n.city = $city, n.startDate = $start_date, n.endDate = $end_date
            ON MATCH SET n.city = $city, n.startDate = $start_date, n.endDate = $end_date
            RETURN n
            """,
            {
                "user_id": itinerary.user_id,
                "city": itinerary.city.value,  # Assuming city is an object with a 'name' attribute
                "start_date": itinerary.start_date.isoformat(),
                "end_date": itinerary.end_date.isoformat(),
            },
        )
        return itinerary_existed
