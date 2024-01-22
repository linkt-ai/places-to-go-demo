"""This file defines a client for the Clerk REST API.

This client has methods for creating, getting, deleting, and listing the users in the
application.
"""
import json
from typing import Any, Dict, List, Optional

import requests

from requests import Response

from .config import settings
from .models import User


class ClerkClientError(Exception):
    """The ClerkClientError class defines an exception for the ClerkClient."""

    def __init__(self, response: Response) -> None:
        """Initialize the ClerkClientError."""
        payload = response.json()
        self.errors = [error.get("message", None) for error in payload["errors"]]

    def __str__(self) -> str:
        """Get the string representation of the error."""
        return self.message

    @property
    def message(self) -> str:
        """Get the error message."""
        return ", ".join(self.errors)


class ClerkUserDoesNotExist(Exception):
    """The ClerkUserDoesNotExist class defines an exception for when a user does not exist."""

    def __init__(self, user_id: str) -> None:
        """Initialize the ClerkUserDoesNotExist."""
        self.user_id = user_id

    def __str__(self) -> str:
        """Get the string representation of the error."""
        return self.message

    @property
    def message(self) -> str:
        """Get the error message."""
        return f"User with id {self.user_id} does not exist."


class ClerkClient:
    """The ClerkClient class defines a client for the Clerk REST API."""

    def __init__(self):
        self._secret_key = settings.CLERK_SECRET_KEY
        self._base = "https://api.clerk.com/v1"

    @property
    def headers(self):
        """The default headers for the ClerkClient.

        This property handles setting the Authorization header with the secret key.
        """
        headers = {}

        if self._secret_key:
            headers["Authorization"] = f"Bearer {self._secret_key}"
        headers["Content-Type"] = "application/json"
        return headers

    def _execute(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        search_params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Execute a request to the Clerk API."""
        params = (
            "?" + "&".join([f"{k}={v}" for k, v in search_params.items()])
            if search_params
            else ""
        )
        url = f"{self._base}/{endpoint}"
        if params:
            url += params

        match method:
            case "GET":
                return requests.get(url, headers=self.headers, timeout=5)
            case "POST":
                return requests.post(
                    url, data=json.dumps(payload), headers=self.headers, timeout=5
                )
            case "DELETE":
                return requests.delete(
                    url, headers=self.headers, data=payload, timeout=5
                )
            case _:
                raise ValueError(f"Unsupported method: {method}")

    def create_user(
        self, email: str, first_name: str, last_name: str, password: str
    ) -> User:
        """Create a user in Clerk."""

        payload = {
            "email_address": [email],
            "first_name": first_name,
            "last_name": last_name,
            "password": password,
        }

        response = self._execute("POST", "users", payload=payload)

        # Catch error responses from clerk
        if response.status_code in [400, 422]:
            raise ClerkClientError(response)

        if response.status_code == 200:
            data = response.json()

            # Transform the data here:
            user = User(**data)
            return user

        raise ValueError("Unexpected response from Clerk API.")

    def list_users(self) -> List[User]:
        """List all users in Clerk."""
        search_params = {"limit": 100}
        response = self._execute("GET", "users", search_params=search_params)

        # Catch error responses from clerk
        if response.status_code in [400, 422]:
            raise ClerkClientError(response)

        if response.status_code == 200:
            data = response.json()
            return [User(**user) for user in data]

        raise ValueError("Unexpected response from Clerk API.")

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a specific clerk user."""

        search_params = {"user_id": user_id}

        response = self._execute("GET", "users", search_params=search_params)

        # Catch error responses from clerk
        if response.status_code in [400, 422]:
            raise ClerkClientError(response)

        if response.status_code == 200:
            data = response.json()
            if len(data) == 0:
                return None

            return User(**data[0])

        raise ValueError("Unexpected response from Clerk API.")

    def delete_user(self, user_id: str) -> None:
        """Delete a user from clerk."""

        response = self._execute("DELETE", f"users/{user_id}")

        # Catch error responses from clerk
        if response.status_code in [400, 422]:
            raise ClerkClientError(response)

        if response.status_code == 200:
            return

        if response.status_code == 404:
            raise ClerkUserDoesNotExist(user_id)

        raise ValueError("Unexpected response from Clerk API.")
