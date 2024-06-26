"""The tools.py file defines the tools that are used by the agent."""
import json
from typing import List, Optional
from uuid import uuid4

from pinecone import ScoredVector
from pydantic import BaseModel
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCallParam

from .types import ActivityType
from ..models import City, Event as BaseEventModel
from ..pinecone import pinecone_index


class VenueInformation(BaseModel):
    """The information about a venue managed by the LLM."""

    id: str
    name: str
    description: str


class VenueResult(VenueInformation):
    """VenueResult object that represents a venue result from the API."""

    relevance_score: float


class Event(BaseEventModel):
    """Event object that represents an event from the API. We override the base model
    to implement additional functionality needed by the Agent.
    """

    title: Optional[str] = None
    venue_id: Optional[str] = None

    @classmethod
    def from_venues(
        cls, venues: List[VenueInformation], start_time: str, end_time: str
    ) -> List["Event"]:
        """Create an event from a venue."""
        # Get the urls and thumbnail urls for the venues from the Graph
        # TODO: Implement this query to the graph

        print(venues)
        # Create an list of Event object to be returned to the client
        return [
            cls(
                id=str(uuid4()),
                title=venue.name,
                venue_id=venue.id,
                start_time=start_time,
                end_time=end_time,
                url="http://business-name.com/",
                thumbnail_url="http://business-name.com/image.jpg",
            )
            for venue in venues
        ]


class VenueQueryTool(BaseModel):
    """A tool that queries the Vectorstore database for relevant venues."""

    category: ActivityType
    city: City
    query: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._openai_client = OpenAI()
        self._index = pinecone_index

    def _embed_query(self, query: str) -> List[float]:
        """Embed a query using the OpenAI API."""
        # Get the embeddings of the query.
        response = self._openai_client.embeddings.create(
            input=query, model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    def _query_vectorstore(self) -> List[ScoredVector]:
        """Query the Vectorstore database."""
        # Get a list of relevant venues from the Vectorstore database.
        query_value = self._embed_query(self.query)
        venue_results = self._index.query(
            vector=query_value,
            top_k=10,
            namespace="venues",
            include_metadata=True,
            filter={
                "city": {"$eq": self.city.value},
                "category": {"$eq": self.category.value},
            },
        )

        assert (
            "matches" in venue_results
        ), "'matches' field not found in response object"
        assert len(venue_results["matches"]) > 0, "No venues found for the given query."

        return venue_results["matches"]

    def __call__(self) -> List[VenueResult]:
        """Execute the VenueQueryTool."""

        # Get a list of relevant venues from the Vectorstore database.
        filtered_venues = self._query_vectorstore()

        # Now that we have base venues, we need to order them based on the relationship values
        # between the venues and the user's posts

        # TODO: Implement the query to the graph to order venues by relevance to mood board

        # Format the results as VenueResult objects
        results = [
            VenueResult(id=venue.id, **venue.metadata, relevance_score=venue.score)
            for venue in filtered_venues
        ]
        return results

    @staticmethod
    def definition():
        """Get the definition of the VenueQueryTool to be provided to the LLM."""
        return {
            "type": "function",
            "function": {
                "name": "venue_query",
                "description": "Detailed sentence describing the activity or location the user \
                    is looking for.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": ActivityType.schema(),
                        "city": City.schema(),
                        "query": {
                            "type": "string",
                            "description": "A one sentence description of the venue the user is \
                                looking for.",
                        },
                    },
                    "required": ["category", "city", "query"],
                },
            },
        }


class EventCreatorTool(BaseModel):
    """A tool that creates events from a list of venues."""

    venues: List[VenueInformation]
    start_time: str
    end_time: str

    def __call__(self) -> List[Event]:
        """Execute the EventCreatorTool."""
        # We simply create an event for each venue.

        events = Event.from_venues(self.venues, self.start_time, self.end_time)

        return events

    @staticmethod
    def definition():
        """Get the definition of the EventCreatorTool to be provided to the LLM."""
        return {
            "type": "function",
            "function": {
                "name": "event_creator",
                "description": "Create events from a list of venues.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "venues": {
                            "type": "array",
                            "items": VenueInformation.model_json_schema(),
                        },
                        "start_time": {"type": "string", "format": "%Y-%m-%dT%H:%M:%S"},
                        "end_time": {"type": "string", "format": "%Y-%m-%dT%H:%M:%S"},
                    },
                    "required": ["venues", "start_time", "end_time"],
                },
            },
        }


def execute_tool(_id: str, name: str, **kwargs) -> ChatCompletionMessageToolCallParam:
    """Execute a tool given a name and a set of arguments."""
    if name == "venue_query":
        tool = VenueQueryTool(**kwargs)
    elif name == "event_creator":
        tool = EventCreatorTool(**kwargs)
    else:
        raise ValueError(f"Invalid tool name: {name}.")
    result = tool()
    data = [item.model_dump() for item in result]
    print(data)
    return ChatCompletionMessageToolCallParam(
        tool_call_id=_id, role="tool", name=name, content=json.dumps(data)
    )


tools = [VenueQueryTool.definition(), EventCreatorTool.definition()]
