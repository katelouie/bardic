"""
Browser-specific storage adapter for the Bardic runtime engine.

Provides localStorage-based save/load for browser-bundled games.
This is the ONLY browser-specific code — everything else in the runtime
works identically in desktop and browser environments via the
`environment` parameter.

Usage:
    # Automatically attached when environment="browser"
    engine = BardEngine(story_data, environment="browser")
    engine.save_to_browser("slot1")
    engine.load_from_browser("slot1")
    saves = engine.list_browser_saves()
    engine.delete_browser_save("slot1")

    # Or used standalone with a StateManager
    adapter = BrowserStorageAdapter(engine.state_manager)
    adapter.save("my_save")
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bardic.runtime.state import StateManager


def _get_storage():
    """Get localStorage handle from the browser environment.

    Tries Pyodide's js module first (direct Pyodide), then falls back
    to PyScript's window object.

    Returns:
        localStorage object

    Raises:
        ImportError: If neither Pyodide nor PyScript is available
    """
    try:
        from js import localStorage
        return localStorage
    except ImportError:
        from pyscript import window
        return window.localStorage


class BrowserStorageAdapter:
    """localStorage save/load for browser-bundled games.

    Wraps a StateManager with browser-specific persistence. Each save
    is stored as a JSON string in localStorage under the key
    "bardic_save_{slot_name}".
    """

    def __init__(self, state_manager: "StateManager"):
        self.state_manager = state_manager

    def save(self, slot_name: str = "autosave") -> None:
        """Save game state to browser localStorage.

        Args:
            slot_name: Name of the save slot (default: "autosave")

        Raises:
            ImportError: If localStorage is not available
        """
        try:
            storage = _get_storage()
            save_data = self.state_manager.save_state()
            json_str = json.dumps(save_data)
            storage.setItem(f"bardic_save_{slot_name}", json_str)
        except ImportError:
            print("Warning: localStorage not available (not in browser)")
            raise

    def load(self, slot_name: str = "autosave") -> bool:
        """Load game state from browser localStorage.

        Args:
            slot_name: Name of the save slot (default: "autosave")

        Returns:
            True if save was found and loaded, False otherwise
        """
        try:
            storage = _get_storage()
            json_str = storage.getItem(f"bardic_save_{slot_name}")
            if json_str:
                save_data = json.loads(json_str)
                self.state_manager.load_state(save_data)
                return True
            return False
        except ImportError:
            print("Warning: localStorage not available (not in browser)")
            return False

    def list_saves(self) -> list[str]:
        """List available save slots in browser localStorage.

        Returns:
            List of save slot names (without the "bardic_save_" prefix)
        """
        try:
            storage = _get_storage()
            saves = []
            for i in range(storage.length):
                key = storage.key(i)
                if key and key.startswith("bardic_save_"):
                    saves.append(key[12:])  # Remove "bardic_save_" prefix
            return saves
        except ImportError:
            print("Warning: localStorage not available (not in browser)")
            return []

    def delete_save(self, slot_name: str) -> None:
        """Delete a save slot from browser localStorage.

        Args:
            slot_name: Name of the save slot to delete
        """
        try:
            storage = _get_storage()
            storage.removeItem(f"bardic_save_{slot_name}")
        except ImportError:
            print("Warning: localStorage not available (not in browser)")
