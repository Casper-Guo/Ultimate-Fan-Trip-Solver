"""
Google Maps API endpoints.

Why rewrite this instead of using the existing Google official Python client library?
1. That library is not actively maintained and has no type annotations.
2. We do not require the additional functionalities provided by having an actual client.
We only need to make a small volume of requests and do not need to keep a connection alive.
"""

from .base import GoogleMapsAPI

__all__ = ["GoogleMapsAPI"]
