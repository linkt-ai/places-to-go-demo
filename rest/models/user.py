"""This file defines the data model for the User resource."""
from typing import Optional

from .base import BaseModel


class User(BaseModel):
    """The User class defines the data model for a user."""

    id: str
    email: str
    name: str

    def __init__(
        self,
        id: Optional[str] = None,  # pylint: disable=redefined-builtin
        email_addresses: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        # Add kwargs as a catch-all for any other attributes
        **kwargs,  # pylint: disable=unused-argument
    ) -> None:
        if first_name is None or last_name is None:
            name = None
        else:
            name = f"{first_name} {last_name}"

        if email_addresses is None or len(email_addresses) == 0:
            email = None
        else:
            email = email_addresses[0].get("email_address", None)

        data = {"id": id, "email": email, "name": name}
        super().__init__(**data)
