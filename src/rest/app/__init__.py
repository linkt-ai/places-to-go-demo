"""The app module defines the Fast API application, along with the routes and
endpoints for the application.
"""

from .base import app

# We need to import each file which defines routes to ensure that the routes are
# registered with the application.
from . import board
from . import itinerary
from . import venue
