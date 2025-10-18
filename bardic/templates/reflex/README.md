# Bardic Reflex Template

A Reflex-based interactive fiction player for Bardic stories. Pure Python - no JavaScript!

## Features

- 🐍 **Pure Python** - No JavaScript required
- ⚡ **Reactive** - Reflex's state management
- 🎨 **Customizable** - Tailwind CSS styling
- 🚀 **Fast Setup** - Get running in minutes

## Status

This template provides a basic story player. **Save/load and story picker features are planned for future releases.**

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Compile Your Story

```bash
bardic compile example.bard -o compiled_stories/example.json
```

### 3. Run the Player

```bash
reflex run
```

Open `http://localhost:3000` in your browser!

## Project Structure

```
your-game/
├── reflex_player/
│   ├── __init__.py
│   └── reflex_player.py     # Main Reflex app
├── assets/                  # Static assets (images, etc.)
├── compiled_stories/        # Compiled .json stories (create this directory)
├── rxconfig.py             # Reflex configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## How It Works

**Reflex Architecture:**
- Reflex apps use reactive state management
- State changes automatically trigger UI updates
- All UI is defined in Python (no HTML/JSX)

**Story Integration:**
- BardEngine loaded on app start
- Current passage stored in Reflex state
- Choices trigger state updates

## Writing Stories

Place your `.bard` files anywhere, then compile to `compiled_stories/`:

```bash
# Create the directory first
mkdir -p compiled_stories

# Compile your story
bardic compile my_story.bard -o compiled_stories/my_story.json
```

Update `reflex_player/reflex_player.py` to load your story:
```python
# Find this line and change the story file:
story_data = json.load(open("compiled_stories/your_story.json"))
```

## Customization

### Styling

Reflex uses Tailwind CSS classes. Edit `reflex_player/reflex_player.py`:

```python
# Example: Change button styling
rx.button(
    choice["text"],
    on_click=lambda: State.make_choice(i),
    class_name="px-4 py-2 bg-blue-500 hover:bg-blue-700"  # Customize here
)
```

### State Management

Add custom state variables to the `State` class:

```python
class State(rx.State):
    # Existing state
    current_passage: dict = {}

    # Add your own
    player_score: int = 0
    inventory: list = []
```

## Reflex Commands

```bash
reflex run          # Start development server
reflex export       # Export for deployment
reflex init         # Reinitialize (if needed)
```

## Future Enhancements

The following features are planned:
- 💾 Save/load functionality
- 📚 Story picker (select from multiple stories)
- 🎨 Enhanced UI components
- 📊 Progress tracking

## Known Limitations

- Currently loads a single hardcoded story file
- No save/load yet
- Basic UI (room for enhancement!)

These will be addressed in future updates. Contributions welcome!

## Development

### File Locations

- Main app code: `reflex_player/reflex_player.py`
- Reflex config: `rxconfig.py`
- Generated files: `.web/` (auto-created, don't edit)

### Hot Reload

Reflex automatically reloads when you edit Python files. Just save and refresh your browser!

## Need Help?

- [Bardic Documentation](https://github.com/katelouie/bardic)
- [Reflex Documentation](https://reflex.dev/docs/)
- [Reflex Discord](https://discord.gg/T5WSbC2YtQ)

## Example Game

Check out [Arcanum](https://github.com/katelouie/arcanum-game) for a complete example built with Bardic (using NiceGUI)!
