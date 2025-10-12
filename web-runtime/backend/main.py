"""
Generic Bardic web runtime - FastAPI backend.

This is a minimal server that can run ANY Bardic story.
"""

import random
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path
from typing import Any
from extensions import get_game_context, register_custom_routes

# Import your Bardic engine!
# We need to add the parent directory to the path to find it
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from bardic import BardEngine

# Create the FastAPI app
app = FastAPI(title="Bardic Web Runtime")

# Add the custom routes from the extensions module
register_custom_routes(app)

# Add CORS middleware (this lets your React app talk to your API)
# Don't worry too much about this - it's just standard web security stuff
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite's default dev server
        "http://127.0.0.1:5173",  # Also allow 127.0.0.1
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Story active story sessions in memory
# In a real app you'd use a database but for now this is fine.
sessions: dict[str, BardEngine] = {}

# Directory where compiled stories are stored
# Add directories to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent
GAME_LOGIC_DIR = PROJECT_ROOT / "game_logic"
STORIES_DIR = PROJECT_ROOT / "compiled_stories"

STORIES_DIR.mkdir(exist_ok=True)

for dir_path in [PROJECT_ROOT, GAME_LOGIC_DIR]:
    dir_str = str(dir_path)
    if dir_str not in sys.path:
        sys.path.insert(0, dir_str)


def get_default_context() -> dict[str, Any]:
    """
    Get context functions for stories.

    Conbines default utilities with game-specific functions.
    """
    # Get game-specific context from extensions
    return get_game_context()


# This is an "endpoint" - a URL that does something
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Bardic Web Runtime",
        "version": "0.1.0",
        "endpoints": {
            "health": "/api/health",
            "list_stories": "/api/stories",
            "start_story": "POST /api/story/start",
            "make_choice": "POST /api/story/choose",
        },
    }


@app.get("/api/health")
async def health():
    """Check if the server is working."""
    return {"status": "ok"}


@app.get("/api/stories")
async def list_stories():
    """List all available compiled stories."""
    stories = []

    # Look for .json files in the story directory
    for story_file in STORIES_DIR.glob("*.json"):
        stories.append(
            {
                "id": story_file.stem,  # filename without json
                "name": story_file.stem.replace("_", " ").title(),
                "path": str(story_file),
            }
        )

    return {"stories": stories}


# Pydantic models define what data the endpoint expects
# Think of these as "shapes" for your data
class StartStoryRequest(BaseModel):
    story_id: str
    session_id: str


@app.post("/api/story/start")
async def start_story(request: StartStoryRequest):
    """
    Start a new story session.

    This loads the story and returns the first passage.
    """
    # Load the story file
    story_path = STORIES_DIR / f"{request.story_id}.json"

    if not story_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Story {request.story_id} not found"
        )

    try:
        # Load the JSON
        with open(story_path) as f:
            story_data = json.load(f)

        # Create a Bardic Engine for this story
        # For now just default custom context (see above)
        context = get_default_context()
        engine = BardEngine(story_data, context=context)

        # Store the engine in our sessions dict
        sessions[request.session_id] = engine

        # Get the first passage
        output = engine.current()

        # DEBUG: Print what we're sending
        print(f"\n=== START STORY DEBUG ===")
        print(f"Passage ID: {output.passage_id}")
        print(f"Content length: {len(output.content)}")
        print(f"Content:\n{repr(output.content)}\n")
        print(f"=== END DEBUG ===\n")

        # Return it to the frontend
        return {
            "content": output.content,
            "choices": [
                {"index": i, "text": choice["text"]}
                for i, choice in enumerate(output.choices)
            ],
            "passage_id": output.passage_id,
            "is_end": engine.is_end(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading story: {str(e)}")


class MakeChoiceRequest(BaseModel):
    session_id: str
    choice_index: int


@app.post("/api/story/choose")
async def make_choice(request: MakeChoiceRequest):
    """
    Make a choice and advance the story.
    """
    # Get the engine for this session
    engine = sessions.get(request.session_id)

    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Make the choice
        output = engine.choose(request.choice_index)

        # DEBUG: Print what we're sending
        print(f"\n=== CHOOSE DEBUG ===")
        print(f"Passage ID: {output.passage_id}")
        print(f"Content length: {len(output.content)}")
        print(f"Content:\n{repr(output.content)}\n")
        print(f"=== END DEBUG ===\n")

        # Return the new passage
        return {
            "content": output.content,
            "choices": [
                {"index": i, "text": choice["text"]}
                for i, choice in enumerate(output.choices)
            ],
            "passage_id": output.passage_id,
            "is_end": engine.is_end(),
        }
    except (IndexError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid choice: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
