"""
SaveManager - Abstraction layer for save/load functionality.

Currently uses local JSON files in saves/ directory.
Can be swapped for localStorage or database later without changing UI code.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any


class SaveManager:
    """Manages save game files."""

    def __init__(self, saves_dir: str | Path):
        """Initialize SaveManager with a saves directory."""
        self.saves_dir = Path(saves_dir)
        self.saves_dir.mkdir(exist_ok=True)

    def save_game(self, save_name: str, engine_state: dict[str, Any]) -> dict:
        """
        Save game state to a file.

        Args:
            save_name: User-provided name for the save
            engine_state: Complete engine state from engine.save_state()

        Returns:
            Dict with save metadata (save_id, save_path, etc.)
        """
        # Add user-provided save name to the state
        save_data = engine_state.copy()
        save_data["save_name"] = save_name
        save_data["user_timestamp"] = save_data.get("timestamp")

        # Generate unique save ID (timestamp-based)
        save_id = f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        save_path = self.saves_dir / f"{save_id}.json"

        # Write to disk
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2)

        return {
            "success": True,
            "save_id": save_id,
            "save_path": str(save_path),
            "metadata": {
                "save_name": save_name,
                "passage": save_data.get("current_passage_id", "Unknown"),
                "timestamp": save_data.get("timestamp"),
            },
        }

    def load_game(self, save_id: str) -> dict[str, Any]:
        """
        Load a saved game.

        Args:
            save_id: The save file ID (without .json extension)

        Returns:
            The saved engine state

        Raises:
            FileNotFoundError: If save file doesn't exist
        """
        save_path = self.saves_dir / f"{save_id}.json"

        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_id}")

        with open(save_path) as f:
            save_data = json.load(f)

        return save_data

    def list_saves(self) -> list[dict]:
        """
        List all available save files.

        Returns:
            List of save metadata dicts, sorted by timestamp (newest first)
        """
        saves = []

        for save_file in self.saves_dir.glob("save_*.json"):
            try:
                with open(save_file) as f:
                    save_data = json.load(f)

                saves.append(
                    {
                        "save_id": save_file.stem,
                        "save_name": save_data.get("save_name", "Unnamed Save"),
                        "story_name": save_data.get("story_name", "Unknown Story"),
                        "story_id": save_data.get("story_id", "unknown"),
                        "passage": save_data.get("current_passage_id", "Unknown"),
                        "timestamp": save_data.get("timestamp"),
                        "date_display": self._format_timestamp(
                            save_data.get("timestamp")
                        ),
                    }
                )

            except Exception as e:
                print(f"Warning: Could not read save file {save_file}: {e}")
                continue

        # Sort by timestamp (newest first)
        saves.sort(key=lambda s: s.get("timestamp", ""), reverse=True)

        return saves

    def delete_save(self, save_id: str) -> bool:
        """
        Delete a save file.

        Args:
            save_id: The save file ID (without .json extension)

        Returns:
            True if deleted successfully

        Raises:
            FileNotFoundError: If save file doesn't exist
        """
        save_path = self.saves_dir / f"{save_id}.json"

        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_id}")

        save_path.unlink()
        return True

    def _format_timestamp(self, timestamp: str | None) -> str:
        """Format ISO timestamp for display."""
        if not timestamp:
            return "Unknown date"

        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except Exception:
            return timestamp
