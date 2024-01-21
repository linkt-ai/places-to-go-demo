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
                "MATCH (n: Itinerary)-[:HAS_EVENT]->(e:Event) WHERE n.userId = $user_id RETURN n, collect(e) as events",
                {
                    "user_id": user_id,
                },
            )

            record = result.single()
            itinerary_record = record["n"]
            events = record["events"]

            events = [Event(**event) for event in events]
            itinerary = Itinerary(events=events, **itinerary_record)
            return itinerary
    except TypeError:
        return None


def create_itinerary(
    itinerary: Itinerary,
) -> Itinerary:
    """Create an itinerary for a user.

    Args:
        itinerary: The itinerary to create. Expected to have no events.

    Returns:
        Itinerary: The itinerary for the user.

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
            MATCH (n:Itinerary {userId: $user_id})-[r:HAS_EVENT]->(e:Event)
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
