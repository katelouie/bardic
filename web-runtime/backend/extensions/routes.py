"""
Custom API endpoints for your game.

Add game-specific routes here (LLM calls, database access, etc.)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/game", tags=["game"])


@router.post("/interpret-cards")
async def interpret_cards(cards: list) -> dict:
    """
    Custom endpoint for card interpretation.

    Example: Use LLM to generate interpretation
    """
    # TODO: Add your custom logic
    # Could call OpenAI, Claude, etc. here
    return {"interpretation": "Custom interpretation based on cards", "cards": cards}


@router.post("/save-session")
async def save_session(session_data: dict) -> dict:
    """Save a game session to database/file."""
    # TODO: Add your save logic
    return {"status": "saved", "session_id": session_data.get("id")}


@router.get("/load-session/{session_id}")
async def load_session(session_id: str) -> dict:
    """Load a saved game session."""
    # TODO: Add your load loagic
    return {"status": "loaded", "session_id": seesion_id, "data": {}}


def register_custom_routes(app):
    """
    Register all custom routes with the FastAPI app.

    Called from main.py
    """
    app.include_router(router)
