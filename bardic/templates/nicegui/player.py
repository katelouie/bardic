#!/usr/bin/env python3
"""
Minimal Bardic NiceGUI Player Template

A simple interactive fiction player with:
- Story selection from compiled_stories/ directory
- Save/load functionality
- Clean, customizable UI

This is a template - customize it for your needs!
"""

from pathlib import Path
import json
from datetime import datetime
from nicegui import ui
from bardic.runtime.engine import BardEngine

# ============================================================================
# CONFIGURATION - Customize these for your game
# ============================================================================

APP_TITLE = "My Bardic Game"  # TODO: Change this to your game name
STORIES_DIR = Path("compiled_stories")  # TODO: Adjust path if needed
SAVES_DIR = Path("saves")  # TODO: Adjust path if needed

# ============================================================================
# Save/Load Manager
# ============================================================================

class SaveManager:
    """Simple file-based save/load system."""

    def __init__(self, saves_dir: Path):
        self.saves_dir = saves_dir
        self.saves_dir.mkdir(exist_ok=True)

    def save_game(self, name: str, engine_state: dict, story_id: str) -> str:
        """Save game state to a JSON file."""
        timestamp = datetime.now()
        save_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{name.replace(' ', '_')}"
        save_file = self.saves_dir / f"{save_id}.json"

        save_data = {
            "save_id": save_id,
            "name": name,
            "story_id": story_id,
            "timestamp": timestamp.isoformat(),
            "state": engine_state
        }

        with open(save_file, 'w') as f:
            json.dump(save_data, f, indent=2)

        return save_id

    def load_game(self, save_id: str) -> dict:
        """Load game state from a save file."""
        save_file = self.saves_dir / f"{save_id}.json"
        with open(save_file, 'r') as f:
            return json.load(f)

    def list_saves(self) -> list:
        """List all available saves with metadata."""
        saves = []
        for save_file in sorted(self.saves_dir.glob("*.json"), reverse=True):
            with open(save_file, 'r') as f:
                data = json.load(f)
                saves.append({
                    "save_id": data["save_id"],
                    "name": data["name"],
                    "story_id": data.get("story_id", "unknown"),
                    "timestamp": data["timestamp"]
                })
        return saves

    def delete_save(self, save_id: str):
        """Delete a save file."""
        save_file = self.saves_dir / f"{save_id}.json"
        if save_file.exists():
            save_file.unlink()

# ============================================================================
# Application State
# ============================================================================

save_manager = SaveManager(SAVES_DIR)
current_screen = "story_select"  # story_select, playing
engine = None
current_story_id = None
main_container = ui.column()

# ============================================================================
# Navigation Functions
# ============================================================================

def navigate_to(screen: str):
    """Navigate to a different screen."""
    global current_screen
    current_screen = screen
    update_ui()

def update_ui():
    """Rebuild the UI based on current screen."""
    main_container.clear()
    with main_container:
        if current_screen == "story_select":
            show_story_select()
        elif current_screen == "playing":
            show_player()

# ============================================================================
# Story Selection Screen
# ============================================================================

def show_story_select():
    """Show story selection screen."""
    # Header
    with ui.row().classes('w-full justify-between items-center mb-8'):
        ui.label(APP_TITLE).classes('text-3xl font-bold')

    # Story list
    ui.label('Select a Story').classes('text-xl mb-4')

    story_files = list(STORIES_DIR.glob("*.json"))
    if not story_files:
        ui.label('No compiled stories found!').classes('text-gray-500')
        ui.label(f'Add .json files to {STORIES_DIR}/').classes('text-sm text-gray-400')
        return

    # TODO: Customize the story card appearance
    for story_file in sorted(story_files):
        story_id = story_file.stem
        with ui.card().classes('w-full cursor-pointer hover:shadow-lg').on('click', lambda s=story_id: start_story(s)):
            ui.label(story_id.replace('_', ' ').title()).classes('text-lg font-bold')
            ui.label(f'{story_file.name}').classes('text-sm text-gray-500')

    # Load save section
    saves = save_manager.list_saves()
    if saves:
        ui.separator().classes('my-8')
        ui.label('Load Saved Game').classes('text-xl mb-4')

        for save in saves:
            timestamp = datetime.fromisoformat(save["timestamp"])
            with ui.card().classes('w-full cursor-pointer hover:shadow-lg').on('click', lambda s=save["save_id"]: load_save(s)):
                ui.label(save["name"]).classes('text-lg font-bold')
                ui.label(f'{save["story_id"]} - {timestamp.strftime("%Y-%m-%d %H:%M")}').classes('text-sm text-gray-500')

def start_story(story_id: str):
    """Start a new story."""
    global engine, current_story_id
    current_story_id = story_id

    story_file = STORIES_DIR / f"{story_id}.json"
    with open(story_file, 'r') as f:
        story_data = json.load(f)

    engine = BardEngine(story_data)
    navigate_to("playing")

def load_save(save_id: str):
    """Load a saved game."""
    global engine, current_story_id

    save_data = save_manager.load_game(save_id)
    current_story_id = save_data.get("story_id", "unknown")

    story_file = STORIES_DIR / f"{current_story_id}.json"
    with open(story_file, 'r') as f:
        story_data = json.load(f)

    engine = BardEngine(story_data)
    engine.load_state(save_data["state"])
    navigate_to("playing")

# ============================================================================
# Player Screen
# ============================================================================

def show_player():
    """Show the story player."""
    # Header with save and return buttons
    with ui.row().classes('w-full justify-between items-center mb-4'):
        ui.label(APP_TITLE).classes('text-2xl font-bold')
        with ui.row().classes('gap-2'):
            ui.button('Save', on_click=lambda: show_save_dialog()).classes('bg-blue-500')
            ui.button('Return to Menu', on_click=lambda: navigate_to("story_select")).classes('bg-gray-500')

    # Story content
    output = engine.current()

    # Passage text - TODO: Customize text styling
    if output.content.strip():
        ui.markdown(output.content).classes('mb-6 text-lg leading-relaxed')

    # Choices or end message
    if output.choices:
        # TODO: Customize choice button styling
        for i, choice in enumerate(output.choices):
            ui.button(
                choice['text'],
                on_click=lambda idx=i: make_choice(idx)
            ).classes('w-full mb-2 text-left bg-purple-600 hover:bg-purple-700')
    else:
        ui.label('THE END').classes('text-2xl font-bold text-center my-8')

def make_choice(choice_index: int):
    """Handle player choice."""
    engine.choose(choice_index)
    update_ui()

# ============================================================================
# Save/Load Dialogs
# ============================================================================

def show_save_dialog():
    """Show save game dialog."""
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Save Game').classes('text-xl font-bold mb-4')

        save_name_input = ui.input(
            label='Save Name',
            placeholder='My Save'
        ).classes('w-full mb-4')

        with ui.row().classes('w-full justify-end gap-2'):
            ui.button('Cancel', on_click=dialog.close).classes('bg-gray-500')
            ui.button('Save', on_click=lambda: save_game(save_name_input.value, dialog)).classes('bg-blue-500')

    dialog.open()

def save_game(name: str, dialog):
    """Save the current game state."""
    if not name.strip():
        name = "Quicksave"

    save_manager.save_game(
        name=name,
        engine_state=engine.save_state(),
        story_id=current_story_id
    )
    dialog.close()
    ui.notify(f'Game saved as "{name}"', type='positive')

# ============================================================================
# Main Application Setup
# ============================================================================

# TODO: Customize the page title and styling
ui.query('body').classes('bg-gray-900 text-white')

with ui.column().classes('w-full max-w-4xl mx-auto p-8'):
    main_container

update_ui()

# TODO: Customize port and other ui.run() options
ui.run(title=APP_TITLE, port=8080, reload=False)
