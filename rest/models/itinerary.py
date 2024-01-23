"""The itinerary.py file definees the data models for the Itinerary resource."""
from datetime import date, datetime
from typing import List, Tuple

from dateutil import parser

from .base import BaseModel
from .event import Event
from .venue import City


class CitiesDoNotMatchError(Exception):
    """The EventCreationError class defines the exception raised when an event cannot be created."""

    def __init__(self, venue_city: City, itinerary_city: City):
        self.venue_city = venue_city
        self.itinerary_city = itinerary_city

    def __str__(self):
        return f"Venue city ({self.venue_city}) and itinerary city \
            ({self.itinerary_city}) do not match."


class InvalidStartAndEndTimeError(Exception):
    """The InvalidStartAndEndTimeError class defines the exception raised when an event has an
    invalid start time or end time.
    """

    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time = start_time
        self.end_time = end_time

    def __str__(self):
        return f"Start time ({self.start_time}) is after end time ({self.end_time})."


class InvalidEventTimeError(Exception):
    """The InvalidTimeError class defines the exception raised when an invalid time is used."""

    def __init__(
        self, start_time: datetime, end_time: datetime, start_date: date, end_date: date
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return f"Start time ({self.start_time}) and end time ({self.end_time}) are not within \
             the range for start date ({self.start_date}) and end date ({self.end_date})."


class EventTimeOverlapError(Exception):
    """The EventTimeOverlapError class defines the exception raised when an event overlaps with
    another event."""

    def __init__(
        self, start_time: datetime, end_time: datetime, existing_even_name: str
    ):
        self.start_time = start_time
        self.end_time = end_time

        self.existing_event = existing_even_name

    def __str__(self):
        return f"Proposed event with start time {self.start_time} and end time \
            {self.end_time} overlaps with existing event ({self.existing_event})."


class Itinerary(BaseModel):
    """The Itinerary class defines the data model for an itinerary.

    Attributes:
        events (List[Event]): The events in the itinerary.
        city (City): The city of the itinerary.
        user_id (str): The user ID of the itinerary.
        start_date (date): The start date of the itinerary.
        end_date (date): The end date of the itinerary.
    """

    events: List[Event]
    city: City
    user_id: str
    start_date: date
    end_date: date

    def __init__(self, convert: bool = True, **kwargs) -> None:
        if convert:
            kwargs = {self._camel_to_snake(k): v for k, v in kwargs.items()}

        super().__init__(**kwargs)

    @property
    def context(self) -> str:
        """Get the context of the itinerary to inject into new LLM conversations."""
        events_str = "\n".join([event.context for event in self.events])
        start = self.start_date.strftime("%Y-%m-%d")
        end = self.end_date.strftime("%Y-%m-%d")
        return ITINERARY_CONTEXT_TEMPLATE.format(
            city=self.city,
            start_date=start,
            end_date=end,
            events=events_str,
        )

    def pop_event(self, event_id: str) -> Event:
        """Remove an event from the itinerary.

        Args:
            event_id (str): The ID of the event to get.

        Returns:
            Event: The event.
        """
        for event in self.events:
            # If we find the matching event
            if event.id == event_id:
                # Remove it from the itinerary and return it to the caller
                self.events.remove(event)
                return event

        return None

    def make_times_aware(
        self, start_time: str, end_time: str
    ) -> Tuple[datetime, datetime]:
        """Make the start time and end time aware of the itinerary's timezone.

        Args:
            start_time (datetime): The start time.
            end_time (datetime): The end time.

        Returns:
            Tuple[datetime, datetime]: The start time and end time in the itinerary's timezone.
        """
        naive_start = parser.parse(start_time)
        naive_end = parser.parse(end_time)

        tz = City.get_timezone(self.city)

        aware_start = tz.localize(naive_start)
        aware_end = tz.localize(naive_end)

        return aware_start, aware_end

    def validate_new_event(
        self, city: City, start_time: datetime, end_time: datetime
    ) -> None:
        """Validate a new event.

        Args:
            start_time (datetime): The start time of the event.
            end_time (datetime): The end time of the event.

        Raises:
            InvalidEventTimeError: If the event has an invalid start time or end time.
            CitiesDoNotMatchError: If the city of the event and the city of the itinerary
                do not match.
        """
        # Assert that the start time and end time are within the start date and end date
        if city != self.city:
            raise CitiesDoNotMatchError(city, self.city)

        if start_time > end_time:
            raise InvalidStartAndEndTimeError(start_time, end_time)

        if start_time.date() < self.start_date or end_time.date() > self.end_date:
            raise InvalidEventTimeError(
                start_time, end_time, self.start_date, self.end_date
            )

        # For each event currently existing in the itinerary, assert the the new event does
        # not have interfering start and end times
        for event in self.events:
            # Check if the event starts during an existing event
            if event.start_time <= start_time <= event.end_time:
                raise EventTimeOverlapError(
                    event.start_time, event.end_time, event.title
                )

            # Check if the event ends during an existing event
            if event.start_time <= end_time <= event.end_time:
                raise EventTimeOverlapError(
                    event.start_time, event.end_time, event.title
                )

            # Check if the event contains an existing event
            if start_time <= event.start_time and end_time >= event.end_time:
                raise EventTimeOverlapError(start_time, end_time, event.title)


ITINERARY_CONTEXT_TEMPLATE = """
City: {city}
Start Date: {start_date}
End Date: {end_date}
------------------------

Events:
------------------------
{events}
"""
