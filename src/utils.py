"""Utility functions for the project."""
import json
import time
import random

PROXY_PORT = 8888

with open("scrape/config/user_agents.json", "r", encoding="utf-8") as f:
    USER_AGENTS = json.load(f)


def time_elapsed(start):
    """Returns the time elapsed since the given start time."""
    return round(time.perf_counter() - start, 2)


def format_proxy(ip: str) -> str:
    """Formats the given IP address as a proxy."""
    return f"{ip}:{PROXY_PORT}"


def get_user_agent() -> str:
    """Returns a random user agent."""
    return random.choice(USER_AGENTS)
