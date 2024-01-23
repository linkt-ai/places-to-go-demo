"""The event.py file defines the data models for the Event resource."""
from datetime import datetime
from uuid import uuid4

from .base import BaseModel
from .venue import YelpVenue


class Event(BaseModel):
    """The Event class defines the data model for an event.

    Attributes:
        id (str): The event ID.
        start_time (datetime): The start time of the event.
        end_time (datetime): The end time of the event.
        title (str): The title of the event.
        url (str): The URL of the event.
        thumbnail_url (str): The thumbnail URL of the event.
    """

    id: str
    venue_id: str
    start_time: datetime
    end_time: datetime
    title: str
    url: str
    thumbnail_url: str

    def __init__(self, convert: bool = True, **kwargs) -> None:
        if convert:
            kwargs = {self._camel_to_snake(k): v for k, v in kwargs.items()}

        super().__init__(**kwargs)

    @property
    def context(self) -> str:
        """Return the context of the event to be used by the LLM."""
        start = self.start_time.strftime("%Y-%m-%d %H:%M")
        end = self.end_time.strftime("%Y-%m-%d %H:%M")
        return EVENT_CONTEXT_TEMPLATE.format(title=self.title, start=start, end=end)

    @classmethod
    def create_event(
        cls,
        start_time: str,
        end_time: str,
        venue: YelpVenue,
        itinerary: ".itinerary.Itinerary",
    ) -> "Event":
        """Create an event from a start date, end date, venue, and itinerary.

        Args:
            start_time (str): The start date of the event.
            end_time (str): The end date of the event.
            venue (Venue): The venue of the event.
            itinerary (Itinerary): The itinerary of the event.

        Returns:
            Event: The event.

        Raises:
            InvalidEventTimeError: If the event time is invalid.
            CitiesDoNotMatchError: If the venue city does not match the itinerary city.
            EventTimeOverlapError: If the event overlaps with an existing event.
        """
        # Make the times aware of the destination TZ
        aware_start, aware_end = itinerary.make_times_aware(start_time, end_time)

        # Check if the event is valid with the itinerary
        itinerary.validate_new_event(venue.city, aware_start, aware_end)

        # We shold add in a check to also look at the itineraries current events to ensure
        # that the event does not overlap with any existing events

        return cls(
            id=str(uuid4()),
            venue_id=venue.id,
            start_time=aware_start,
            end_time=aware_end,
            title=venue.name,
            url=venue.url,
            thumbnail_url=venue.thumbnail_url,
        )


EVENT_CONTEXT_TEMPLATE = """
    {title}
    ----------------------------------------------
    Start: {start}
    End: {end}
"""
