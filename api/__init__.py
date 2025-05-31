"""
alligator.ai API package.

FastAPI-based REST API for the legal research platform.
"""

from .main import app

__version__ = "1.0.0"
__all__ = ["app"]