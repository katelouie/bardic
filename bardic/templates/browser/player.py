"""
Browser-based Bardic player using PyScript.

This script handles:
- Loading the game from game.json
- Rendering passages to the DOM
- Handling player choices
- Save/load via localStorage
"""

import json
import re
from pyscript import document, window
from pyscript.ffi import create_proxy

from engine_browser import BardEngine

# Global engine instance
engine = None
# Game name for display (set during init)
game_name = "Bardic Game"


def init_game():
    """Initialize the game engine and render the first passage."""
    global engine, game_name

    try:
        # Load game data from virtual filesystem
        with open("./game.json", "r") as f:
            story_data = json.load(f)

        # Get game name from metadata
        metadata = story_data.get("metadata", {})
        game_name = metadata.get("title", "Bardic Game")

        # Update page title
        title_el = document.getElementById("game-title")
        if title_el:
            title_el.textContent = game_name

        # Initialize the engine
        engine = BardEngine(story_data)

        # Hide loading, show game
        loading_el = document.getElementById("loading")
        game_el = document.getElementById("game")

        if loading_el:
            loading_el.style.display = "none"
        if game_el:
            game_el.style.display = "block"

        # Render the initial passage
        render_passage()

        # Check for autosave
        saves = engine.list_browser_saves()
        if "autosave" in saves:
            show_notification("Autosave found. Click Load to restore.")

    except Exception as e:
        show_error(f"Failed to load game: {e}")
        raise


def render_passage():
    """Render the current passage to the DOM."""
    if not engine:
        return

    output = engine.current()

    # Update story content
    content_div = document.getElementById("story-content")
    if content_div:
        content_div.innerHTML = render_markdown(output.content)

    # Update choices
    choices_div = document.getElementById("choices")
    if choices_div:
        choices_div.innerHTML = ""

        if output.choices:
            for i, choice in enumerate(output.choices):
                btn = document.createElement("button")
                btn.className = "choice-btn"
                btn.textContent = choice["text"]

                # Create click handler with closure to capture index
                def make_handler(idx):
                    def handler(event):
                        make_choice(idx)
                    return create_proxy(handler)

                btn.onclick = make_handler(i)
                choices_div.appendChild(btn)
        else:
            # End of story
            end_div = document.createElement("div")
            end_div.className = "end-screen"
            end_div.innerHTML = "<h2>The End</h2><p>Thank you for playing!</p>"

            restart_btn = document.createElement("button")
            restart_btn.className = "restart-btn"
            restart_btn.textContent = "Play Again"
            restart_btn.onclick = create_proxy(lambda e: restart_game())
            end_div.appendChild(restart_btn)

            choices_div.appendChild(end_div)

    # Autosave after each passage
    try:
        engine.save_to_browser("autosave")
    except Exception:
        pass  # Silently fail autosave


def make_choice(index: int):
    """Handle player choice."""
    if not engine:
        return

    try:
        engine.choose(index)
        render_passage()

        # Scroll to top of content
        content_div = document.getElementById("story-content")
        if content_div:
            content_div.scrollTop = 0

    except Exception as e:
        show_error(f"Error making choice: {e}")


def save_game():
    """Save game to a named slot."""
    if not engine:
        return

    # Prompt for save name
    slot_name = window.prompt("Enter save name:", "quicksave")
    if slot_name:
        try:
            engine.save_to_browser(slot_name)
            show_notification(f"Game saved to '{slot_name}'")
        except Exception as e:
            show_error(f"Failed to save: {e}")


def load_game():
    """Show load dialog with available saves."""
    if not engine:
        return

    saves = engine.list_browser_saves()

    if not saves:
        show_notification("No saves found")
        return

    # Create a simple selection
    saves_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(saves))
    choice = window.prompt(f"Available saves:\n{saves_str}\n\nEnter save name to load:", saves[0])

    if choice:
        try:
            if engine.load_from_browser(choice):
                render_passage()
                show_notification(f"Loaded '{choice}'")
            else:
                show_error(f"Save '{choice}' not found")
        except Exception as e:
            show_error(f"Failed to load: {e}")


def restart_game():
    """Restart the game from the beginning."""
    global engine

    try:
        # Reload the story data and create a fresh engine
        with open("./game.json", "r") as f:
            story_data = json.load(f)

        engine = BardEngine(story_data)
        render_passage()
        show_notification("Game restarted")

    except Exception as e:
        show_error(f"Failed to restart: {e}")


def render_markdown(text: str) -> str:
    """
    Convert simple markdown to HTML.

    Supports:
    - **bold**
    - *italic*
    - Paragraphs (double newlines)
    - Line breaks (single newlines)
    """
    if not text:
        return ""

    # Escape HTML entities first
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")

    # Bold: **text**
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # Italic: *text*
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

    # Paragraphs: split on double newlines
    paragraphs = text.split('\n\n')

    # Convert single newlines to <br> within paragraphs
    paragraphs = [p.replace('\n', '<br>') for p in paragraphs]

    # Wrap each paragraph
    html_paragraphs = [f'<p>{p}</p>' for p in paragraphs if p.strip()]

    return '\n'.join(html_paragraphs)


def show_notification(message: str):
    """Show a brief notification message."""
    notif = document.createElement("div")
    notif.className = "notification"
    notif.textContent = message
    document.body.appendChild(notif)

    # Remove after 3 seconds
    def remove_notification():
        if notif.parentNode:
            notif.parentNode.removeChild(notif)

    window.setTimeout(create_proxy(remove_notification), 3000)


def show_error(message: str):
    """Show an error message."""
    notif = document.createElement("div")
    notif.className = "notification error"
    notif.textContent = message
    document.body.appendChild(notif)

    # Remove after 5 seconds
    def remove_notification():
        if notif.parentNode:
            notif.parentNode.removeChild(notif)

    window.setTimeout(create_proxy(remove_notification), 5000)


# Expose functions to JavaScript for onclick handlers in HTML
window.save_game = create_proxy(save_game)
window.load_game = create_proxy(load_game)
window.restart_game = create_proxy(restart_game)

# Initialize the game when the script loads
init_game()
