"""The agent module defines the LLM agent that handles communicating with 
the user.

It is implemented through a REST interface. We will expose the 
'chat' resource to the client, with provided POST, PUT, and DELETE
methods.
- POST: Creates a new chat session
- PUT: Updates a chat session with a new message, returns completion
- DELETE: Deletes a chat session

We will need to define a few principal types to use across the module:
- UserMessage: A message sent by the user
- AgentMessage: A message sent by the agent (optionally should include list of Events)
- ErrorMessage: A message sent from the server when an error occurs
"""
from .agent import Agent
from .types import AgentMessage, ErrorMessage
