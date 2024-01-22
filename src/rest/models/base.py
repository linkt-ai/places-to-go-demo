"""This file defines the custom BaseModel object used by the application.

It has a few simple convenience methods for converting to and from JSON.
"""
import json
import re

from pydantic import BaseModel as BaseModelPydantic


class BaseModel(BaseModelPydantic):
    """The BaseModel class defines the base model for all models in the application."""

    @staticmethod
    def _camel_to_snake(name):
        """Convert a string from camel case to snake case.

        Args:
            name (str): The string to convert.
        """
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def model_dump(self, **kwargs):
        """Dump the model to a dictionary.

        Returns:
            Dict[str, str]: The model as a dictionary.
        """
        json_data = self.model_dump_json(**kwargs)
        data = json.loads(json_data)
        return data
