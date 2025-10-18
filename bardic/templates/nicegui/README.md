# Bardic NiceGUI Player Template

A minimal interactive fiction player built with [NiceGUI](https://nicegui.io/) and [Bardic](https://github.com/katelouie/bardic).

## Features

- 📖 **Story Selection** - Choose from multiple compiled stories
- 💾 **Save/Load** - Save your progress and load anytime
- 🎨 **Customizable UI** - Easy to modify styling and layout
- 🚀 **Simple Setup** - Get started in minutes

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Compile Stories

Compile your `.bard` story files to JSON:

```bash
bardic compile example.bard -o compiled_stories/example.json
```

### 3. Run the Player

```bash
python player.py
```

Open your browser to `http://localhost:8080` and start playing!

## Project Structure

```
your-game/
├── player.py              # NiceGUI player application
├── example.bard           # Example story (compile this first!)
├── compiled_stories/      # Compiled .json story files go here
├── saves/                 # Save game files (auto-created)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Customization Guide

The `player.py` file has TODO comments marking key customization points:

### Basic Customization

1. **App Title**: Change `APP_TITLE` at the top of the file
2. **Paths**: Adjust `STORIES_DIR` and `SAVES_DIR` if needed
3. **Port**: Change the port in `ui.run(port=8080)`

### UI Styling

Look for TODO comments to customize:
- Story card appearance (line ~125)
- Text styling (line ~210)
- Choice button styling (line ~220)
- Page title and background (line ~270)

### Advanced Customization

- Add custom screens (login, settings, etc.)
- Integrate with backend APIs
- Add custom Bardic directives with `@render`
- Implement achievements, stats tracking, etc.

## Writing Stories

Create `.bard` story files using the [Bardic language syntax](https://github.com/katelouie/bardic).

Basic example:

```bard
@metadata
  title: My Story
  author: Your Name
  story_id: my_story

:: Start
Welcome to my story!

~ player_name = "Adventurer"

+ [Begin the adventure] -> Chapter1
+ [Read the tutorial] -> Tutorial

:: Chapter1
Hello, {player_name}! Your adventure begins...
```

Compile with: `bardic compile my_story.bard -o compiled_stories/my_story.json`

## Example Game

Check out [Arcanum](https://github.com/katelouie/arcanum-game) for a complete example of what you can build with Bardic!

## Need Help?

- [Bardic Documentation](https://github.com/katelouie/bardic)
- [NiceGUI Documentation](https://nicegui.io/documentation)
- [Report Issues](https://github.com/katelouie/bardic/issues)

## License

This template is provided as-is for use with Bardic projects.
