"""
Generic Bardic web runtime - FastAPI backend.

This is a minimal server that can run ANY Bardic story.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path
from typing import Any
from extensions import get_game_context, register_custom_routes
from datetime import datetime

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
# Each session stores: {"engine": BardEngine, "story_id": str}
sessions: dict[str, dict] = {}

# Directory where compiled stories are stored
# Add directories to Python path
PROJECT_ROOT = Path(__file__).parent.parent.parent

GAME_LOGIC_DIR = PROJECT_ROOT / "game_logic"

STORIES_DIR = PROJECT_ROOT / "compiled_stories"
STORIES_DIR.mkdir(exist_ok=True)

SAVES_DIR = PROJECT_ROOT / "saves"
SAVES_DIR.mkdir(exist_ok=True)

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
        try:
            # Try to read metadata from story file
            with open(story_file) as f:
                story_data = json.load(f)
                metadata = story_data.get("metadata", {})

            # Use metadata title if available, otherwise use filename
            story_name = metadata.get("title", story_file.stem.replace("_", " ").title())
            story_id = metadata.get("story_id", story_file.stem)

            stories.append(
                {
                    "id": story_id,
                    "name": story_name,
                    "path": str(story_file),
                    "metadata": metadata,  # Include full metadata
                }
            )
        except Exception as e:
            # If we can't read the file, use filename as fallback
            print(f"Warning: Could not read story file {story_file}: {e}")
            stories.append(
                {
                    "id": story_file.stem,
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

        # Store the engine AND story_id in our sessions dict
        sessions[request.session_id] = {
            "engine": engine,
            "story_id": request.story_id
        }

        # Get the first passage
        output = engine.current()

        # DEBUG: Print what we're sending
        print("\n=== START STORY DEBUG ===")
        print(f"Passage ID: {output.passage_id}")
        print(f"Content length: {len(output.content)}")
        print(f"Content:\n{repr(output.content)}\n")
        print(f"Render directives: {output.render_directives}")
        print("=== END DEBUG ===\n")

        # Return it to the frontend
        return {
            "content": output.content,
            "choices": [
                {"index": i, "text": choice["text"]}
                for i, choice in enumerate(output.choices)
            ],
            "passage_id": output.passage_id,
            "is_end": engine.is_end(),
            "render_directives": output.render_directives,
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
    # Get the session for this session_id
    session = sessions.get(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = session["engine"]

    try:
        # Make the choice
        output = engine.choose(request.choice_index)

        # DEBUG: Print what we're sending
        print("\n=== CHOOSE DEBUG ===")
        print(f"Passage ID: {output.passage_id}")
        print(f"Content length: {len(output.content)}")
        print(f"Content:\n{repr(output.content)}\n")
        print(f"Render directives: {output.render_directives}")
        print("=== END DEBUG ===\n")

        # Return the new passage
        return {
            "content": output.content,
            "choices": [
                {"index": i, "text": choice["text"]}
                for i, choice in enumerate(output.choices)
            ],
            "passage_id": output.passage_id,
            "is_end": engine.is_end(),
            "render_directives": output.render_directives,
        }
    except (IndexError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid choice: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


class SaveGameRequest(BaseModel):
    session_id: str
    save_name: str  # User-provided name like "before boss fight"


class LoadGameRequest(BaseModel):
    session_id: str
    save_id: str  # Filename (without .json)
    story_id: str  # Which story to load


class DeleteSaveRequest(BaseModel):
    save_id: str


@app.post("/api/story/save")
async def save_game(request: SaveGameRequest):
    """
    Save the current game state to disk.

    Creates a JSON file in the saves directory with:
    - Complete engine state
    - User-provided save name
    - Timestamp
    - Story metadata
    """
    # Get the session for this session_id
    session = sessions.get(request.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    engine = session["engine"]

    try:
        # Get save data from engine (includes story_id from metadata)
        save_data = engine.save_state()

        # Add user metadata
        save_data["save_name"] = request.save_name
        save_data["user_timestamp"] = save_data["timestamp"]  # For display

        # Note: story_id now comes from engine.save_state() via story metadata

        # Generate unique save ID (timestamp-based)
        save_id = f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        save_path = SAVES_DIR / f"{save_id}.json"

        # Write to disk
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2)

        return {
            "success": True,
            "save_id": save_id,
            "save_path": str(save_path),
            "metadata": {
                "save_name": request.save_name,
                "passage": save_data["current_passage_id"],
                "timestamp": save_data["timestamp"],
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@app.post("/api/story/load")
async def load_game(request: LoadGameRequest):
    """
    Load a saved game from disk and restore the session.

    Creates a new engine instance with the saved state.
    """
    # Load the save file
    save_path = SAVES_DIR / f"{request.save_id}.json"

    if not save_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Save file not found: {request.save_id}"
        )

    try:
        # Read save data
        with open(save_path) as f:
            save_data = json.load(f)

        # Load the story
        story_path = STORIES_DIR / f"{request.story_id}.json"

        if not story_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Story not found: {request.story_id}"
            )

        with open(story_path) as f:
            story_data = json.load(f)

        # Create new engine
        context = get_default_context()
        engine = BardEngine(story_data, context=context)

        # Restore state
        engine.load_state(save_data)

        # Store in sessions with story_id
        sessions[request.session_id] = {
            "engine": engine,
            "story_id": request.story_id
        }

        # Get current passage
        output = engine.current()

        return {
            "success": True,
            "content": output.content,
            "choices": [
                {"index": i, "text": choice["text"]}
                for i, choice in enumerate(output.choices)
            ],
            "passage_id": output.passage_id,
            "is_end": engine.is_end(),
            "render_directives": output.render_directives,
            "metadata": {
                "save_name": save_data.get("save_name", "Unnamed Save"),
                "timestamp": save_data.get("timestamp"),
            },
        }

    except ValueError as e:
        # Invalid save data
        print(f"\n=== LOAD ERROR (ValueError) ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("=== END ERROR ===\n")
        raise HTTPException(status_code=400, detail=f"Invalid save file: {str(e)}")
    except Exception as e:
        print(f"\n=== LOAD ERROR (Exception) ===")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("=== END ERROR ===\n")
        raise HTTPException(status_code=500, detail=f"Failed to load: {str(e)}")


@app.get("/api/saves/list")
async def list_saves():
    """
    List all available save files with their metadata.

    Returns summary information for display in the load menu.
    """
    saves = []

    for save_file in SAVES_DIR.glob("save_*.json"):
        try:
            with open(save_file) as f:
                save_data = json.load(f)

            saves.append(
                {
                    "save_id": save_file.stem,
                    "save_name": save_data.get("save_name", "Unnamed Save"),
                    "story_name": save_data.get("story_name", "Unknown"),
                    "story_id": save_data.get("story_id", "unknown"),  # The actual file ID
                    "passage": save_data.get("current_passage_id", "Unknown"),
                    "timestamp": save_data.get("timestamp"),
                    "date_display": _format_timestamp(save_data.get("timestamp")),
                }
            )

        except Exception as e:
            print(f"Warning: Could not read save file {save_file}: {e}")
            continue

    # Sort by timestamp (newest first)
    saves.sort(key=lambda s: s.get("timestamp", ""), reverse=True)

    return {"saves": saves}


@app.delete("/api/saves/delete/{save_id}")
async def delete_save(save_id: str):
    """Delete a save file."""
    save_path = SAVES_DIR / f"{save_id}.json"

    if not save_path.exists():
        raise HTTPException(status_code=404, detail="Save not found")

    try:
        save_path.unlink()
        return {"success": True, "message": f"Deleted save: {save_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


def _format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display."""
    if not timestamp:
        return "Unknown date"

    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return timestamp
