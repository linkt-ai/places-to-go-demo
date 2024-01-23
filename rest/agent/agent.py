"""The agent module defines the LLM agent that handles communicating with the user."""

import json
from typing import List, Optional, Union

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessage,  # When the agent returns a message
    ChatCompletionMessageToolCall,  # When the agent returns a tool call
    # Models to be instantiated
    ChatCompletionSystemMessageParam,  # The system message model
    ChatCompletionUserMessageParam,  # The user message model
)

from .prompts import SYSTEM_PROMPT
from .tools import tools, Event, execute_tool
from .types import AgentMessage, ErrorMessage

from ..graph import graph_itinerary


class Agent:
    """The Agent class is responsible for executing the agent."""

    messages: List[
        Union[
            ChatCompletionMessage,
            ChatCompletionMessageToolCall,
        ]
    ]

    def __init__(
        self,
        user_id: str,
        model: str = "gpt-3.5-turbo-1106",
        debug: bool = False,
        message_history: Optional[List[ChatCompletionMessage]] = None,
    ):
        """Setup the agent object."""

        # The ID of the user that the agent is interacting with. This will be used for querying
        # the Graph Database.
        self._user_id = user_id

        self._tools = tools
        self.debug = debug

        # Establish the message history if it exists, otherwise create a new message history.
        if message_history:
            print("Using message history")
            self.messages = message_history
        else:
            self.messages = [
                ChatCompletionSystemMessageParam(role="system", content=SYSTEM_PROMPT),
                ChatCompletionUserMessageParam(role="user", content=self.itinerary),
            ]

        self.model = model
        self.client = OpenAI()
        self._finish_reason = None

    @property
    def itinerary(self):
        """Return the itinerary of the user. This must be fetched from the Graph Database."""
        itinerary = graph_itinerary.get_itinerary(self._user_id)
        return itinerary.context

    @property
    def last_events(self) -> Union[List[Event], None]:
        """Return the last events."""
        # iterate backwards through self.messages until we find a message of role "tool",
        # with name "event_creator"
        for message in reversed(self.messages):
            # Extract the role and name from the message. We are looking for messages
            # returned from the LLM, so we filter out all dict instances
            if isinstance(message, dict):
                role = message.get("role", "")
                name = message.get("name", "")
                if role == "tool" and name == "event_creator":
                    data = json.loads(message.get("content", ""))
                    events = [Event(**item) for item in data]
                    return events

        return None

    def __call__(self, query: str) -> Union[AgentMessage, ErrorMessage]:
        """Execute the agent."""
        self.messages.append(ChatCompletionUserMessageParam(role="user", content=query))

        try:
            count = 0
            while count < 5:
                # Execute a single step of the agent.
                self._step()

                # Get the last message from the agent (the result of the last step)
                last_message: ChatCompletionMessage = self.messages[-1]

                # If the last message is a tool_call, execute the tool call.
                if (
                    self._finish_reason == "tool_calls"
                    and len(last_message.tool_calls) > 0
                ):
                    tool_calls: List[
                        ChatCompletionMessageToolCall
                    ] = last_message.tool_calls

                    # If the agent is producing multiple calls per step, that is a problem.
                    assert (
                        len(tool_calls) == 1
                    ), "Only one tool call can be made at a time."

                    # Get the tool call
                    tool_call = tool_calls[0]  # pylint: disable=unsubscriptable-object
                    self._execute_tool(tool_call)

                # Otherwise, if the last message has content, then we may return the results.
                if self._finish_reason == "stop":
                    break

                # Increment the count to track iteratins
                count += 1

            agent_response = AgentMessage(
                content=last_message.content, events=self.last_events
            )
            return agent_response
        except Exception as exp:  # pylint: disable=broad-except
            print(exp)
            error_message = ErrorMessage(
                content=f"An error occurred while executing the agent: {exp}"
            )
            return error_message

    def _step(self) -> None:
        """Execute a single step of the agent."""
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            tools=self._tools,
            tool_choice="auto",
            temperature=0.5,
        )
        msg = completion.choices[0].message
        self._finish_reason = completion.choices[0].finish_reason
        self.messages.append(msg)

    def _execute_tool(self, tool_call_message: ChatCompletionMessageToolCall) -> None:
        """Execute a tool call."""
        tool_call_id = tool_call_message.id
        tool_name = tool_call_message.function.name
        tool_args = json.loads(tool_call_message.function.arguments)
        tool_result = execute_tool(
            tool_call_id, tool_name, debug=self.debug, **tool_args
        )
        self.messages.append(tool_result)
