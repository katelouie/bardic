# Bardic

A Python-first interactive fiction engine for modern web applications.

## Features

- 📝 **Clean Syntax** - Python-like `.bard` files that feel natural to write
- 🐍 **Python Integration** - Full Python code blocks, custom classes, and objects
- 💾 **Save/Load** - Built-in serialization for complex game state
- 🎨 **UI Flexible** - Works with NiceGUI, React, terminal, or any UI framework
- 🚀 **Fast Development** - Compile stories to JSON, run anywhere

## Quick Start

### Installation

```bash
pip install bardic
```

### Create a New Project

```bash
bardic init my-game
cd my-game
pip install -r requirements.txt
```

### Write Your Story

Edit `example.bard`:

```bard
@metadata
  title: My Adventure
  author: Your Name
  story_id: my_adventure

:: Start
Welcome to my interactive story!

~ player_name = "Hero"

+ [Begin adventure] -> Chapter1

:: Chapter1
Hello, {player_name}! Your journey begins...
```

### Compile and Run

```bash
# Compile story to JSON
bardic compile example.bard -o compiled_stories/example.json

# Run the player
python player.py
```

Open `http://localhost:8080` and play your game!

## Example Game

Check out [Arcanum](https://github.com/katelouie/arcanum-game) - a complete tarot reading game built with Bardic. It demonstrates:
- Custom Python classes (Card, Client objects)
- Dynamic UI with passage tags
- Save/load functionality
- Dashboard systems
- NiceGUI integration

## Documentation

### Language Features

- **Passages** - Organize your story into named sections
- **Choices** - Player decisions with conditional visibility
- **Variables** - Store and track game state
- **Python Blocks** - Execute Python code for complex logic
- **Conditionals** - Branch narrative based on state
- **Loops** - Iterate over collections
- **Custom Objects** - Use Python classes in your stories
- **Metadata** - Story information for save/load

See [spec.md](spec.md) for complete language documentation.

### CLI Commands

```bash
# Initialize new project
bardic init my-game

# Compile story
bardic compile story.bard
bardic compile story.bard -o output.json

# Play in terminal
bardic play story.json

# Start web runtime (if available)
bardic serve
```

### Templates

**NiceGUI Template** (default)
- Python-based UI framework
- Save/load functionality
- Story selection
- Clean, customizable interface

Future templates: React, Terminal, Custom

## Development

### Installing from Source

```bash
git clone https://github.com/katelouie/bardic.git
cd bardic
pip install -e .
```

### Running Tests

```bash
pyenv activate bardic
python tests/test_parser.py
```

### Project Structure

```
bardic/
├── bardic/
│   ├── compiler/    # Parser and compiler
│   ├── runtime/     # BardEngine execution
│   ├── cli/         # Command-line interface
│   └── templates/   # Project templates
├── tests/           # Test files
├── docs/           # Documentation
└── stories/        # Example stories
```

## Architecture

Bardic uses a three-layer architecture:

1. **Compiler** - Parses `.bard` files to JSON
2. **Runtime** - BardEngine executes compiled stories
3. **UI Layer** - Your choice of interface (NiceGUI, React, etc.)

Stories compile to platform-independent JSON that runs anywhere.

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Links

- [Documentation](https://github.com/katelouie/bardic/wiki)
- [Example Game: Arcanum](https://github.com/katelouie/arcanum-game)
- [Report Issues](https://github.com/katelouie/bardic/issues)

## Status

Bardic is in early development (MVP stage). Core features are working, but the API may change as the project evolves.
