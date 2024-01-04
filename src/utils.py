"""Utility functions for the project."""
import time

PROXY_PORT = 8888


def time_elapsed(start):
    """Returns the time elapsed since the given start time."""
    return round(time.perf_counter() - start, 2)


def format_proxy(ip: str) -> str:
    """Formats the given IP address as a proxy."""
    return f"{ip}:{PROXY_PORT}"
