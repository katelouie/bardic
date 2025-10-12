"""
Extension system for custom game logic.

Add your custom functions and API endpoints here.
"""

from .context import get_game_context
from .routes import register_custom_routes

__all__ = ["get_game_context", "register_custom_routes"]
