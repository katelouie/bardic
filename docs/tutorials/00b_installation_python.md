# Step 0B: Installation for Python Users

**This guide is for developers** who already have Python installed and are comfortable with virtual environments, pip, and the command line.

If you're new to Python, we recommend [Step 0A: Installation for Beginners](00A_installation_pixi.md) instead—it's much simpler!

---

## Prerequisites

- Python 3.8 or higher
- pip
- Basic command line knowledge

Check your Python version:

```bash
python --version
# or
python3 --version
```

---

## Quick Start (TL;DR)

```bash
pip install bardic
bardic init my-game
cd my-game
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
bardic play example.bard
```

---

## Detailed Installation

### 1. Install Bardic

You can install Bardic globally or in a virtual environment:

#### Global Installation (Easiest)

```bash
pip install bardic
```

This installs the `bardic` command globally on your system.

#### Virtual Environment Installation (Recommended for Developers)

```bash
# Create a dedicated environment
python -m venv ~/.bardic-env

# Activate it
source ~/.bardic-env/bin/activate  # Mac/Linux
# or
~\.bardic-env\Scripts\activate  # Windows

# Install Bardic
pip install bardic
```

### 2. Verify Installation

```bash
bardic --version
```

You should see something like `bardic 0.x.x`.

---

## Creating a New Project

### Initialize a Project

```bash
bardic init my-game
cd my-game
```

This creates a new directory with:

```sh
my-game/
├── example.bard          # Sample story
├── requirements.txt      # Python dependencies
└── player.py            # Optional: CLI player
```

### Set Up Project Virtual Environment

Create an isolated environment for this project:

```bash
python -m venv .venv
```

Activate it:

```bash
# Mac/Linux
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Your First Story

Create a file called `hello.bard`:

```bard
:: Start
Welcome to Bardic!

+ [Continue] -> Next

:: Next
You're all set up!

+ [Play again] -> Start
```

### Compile and Play

```bash
# Compile to JSON
bardic compile hello.bard -o hello.json

# Play in terminal
bardic play hello.json
```

Or compile and play in one step:

```bash
bardic play hello.bard
```

---

## Project Structure (Recommended)

For larger projects:

```sh
my-game/
├── .venv/                    # Virtual environment
├── stories/                  # Your .bard files
│   ├── main.bard
│   ├── chapter1.bard
│   └── chapter2.bard
├── compiled_stories/         # Compiled .json files
│   └── main.json
├── game_logic/              # Your Python classes
│   ├── __init__.py
│   ├── character.py
│   └── items.py
├── player.py                # CLI player (optional)
├── web_ui.py               # Web UI (optional)
├── requirements.txt
└── README.md
```

---

## Dependencies for Different Features

### Base Installation

```bash
pip install bardic
```

### For NiceGUI Web UI (Part 4 of Tutorial)

```bash
pip install bardic nicegui
```

### For React + FastAPI Web UI

```bash
pip install bardic fastapi uvicorn
```

### Development Tools

```bash
pip install bardic pytest black mypy
```

---

## IDE Setup

### VS Code

1. Install the [Bardic extension](https://github.com/katelouie/bardic-vscode)
2. Open your project folder
3. VS Code will detect `.venv` automatically
4. Select the Python interpreter from `.venv`

**Recommended extensions:**

- Bardic (syntax highlighting)
- Python (official)
- Pylance (type checking)

### PyCharm

1. Open project folder
2. File → Settings → Project → Python Interpreter
3. Add Interpreter → Existing Environment
4. Select `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)

---

## Command Reference

```bash
# Create new project
bardic init <project-name>

# Compile story
bardic compile <story.bard> [-o output.json]

# Play story
bardic play <story.bard|story.json>

# Generate story graph visualization
bardic graph <story.json> [--output graph.html]

# Get help
bardic --help
bardic compile --help
bardic play --help
```

---

## Common Workflows

### Development Workflow

```bash
# Edit your .bard file in your editor
nano story.bard

# Play it directly (auto-compiles)
bardic play story.bard

# If errors, fix and replay
bardic play story.bard
```

### Production Build

```bash
# Compile with output location
bardic compile main.bard -o build/game.json

# Verify compilation
bardic play build/game.json

# Generate documentation
bardic graph build/game.json --output docs/story-map.html
```

---

## Python Integration

### Import Your Classes

Create `game_logic/items.py`:

```python
class Item:
    def __init__(self, name, value):
        self.name = name
        self.value = value
```

Use in your story:

```bard
from game_logic.items import Item

:: Start
~ sword = Item("Iron Sword", 100)
You found: {sword.name} (worth {sword.value} gold)
```

**Note:** Bardic uses the same Python import system as regular Python. Your `PYTHONPATH` and module structure work the same way.

---

## Troubleshooting

### "bardic: command not found"

Your pip bin directory isn't in PATH. Either:

1. Use `python -m bardic` instead of `bardic`
2. Add pip's bin directory to PATH
3. Use a virtual environment and activate it

### "ModuleNotFoundError: No module named 'bardic'"

You're running Python directly instead of using the `bardic` CLI. The CLI handles imports correctly.

Use:

```bash
bardic play story.bard
```

Not:

```bash
python story.bard  # This won't work!
```

### Import Errors in Stories

Make sure you're running from the project root:

```bash
# Good
cd my-game
bardic play stories/main.bard

# Bad (wrong directory)
cd my-game/stories
bardic play main.bard  # Can't find game_logic modules!
```

### Different Python Versions

If you have multiple Python versions:

```bash
# Use specific version
python3.11 -m venv .venv
source .venv/bin/activate
pip install bardic
```

---

## Package Management Alternatives

### Using Poetry

```bash
poetry new my-game
cd my-game
poetry add bardic
poetry run bardic play example.bard
```

### Using Pipenv

```bash
pipenv install bardic
pipenv run bardic play example.bard
```

### Using uv (Fastest)

```bash
uv pip install bardic
uv run bardic play example.bard
```

---

## Deployment

### Single File Distribution

Compile your story and distribute just the JSON:

```bash
bardic compile game.bard -o game.json
# Distribute game.json + player.py
```

### As a Python Package

Structure as a proper package:

```sh
my-game/
├── setup.py
├── my_game/
│   ├── __init__.py
│   ├── stories/
│   └── game_logic/
└── README.md
```

```python
# setup.py
from setuptools import setup

setup(
    name="my-game",
    version="1.0.0",
    install_requires=["bardic>=0.1.0"],
    entry_points={
        "console_scripts": [
            "my-game=my_game.cli:main",
        ],
    },
)
```

### Web Application

See [Part 4: Custom UI](04_custom_ui.md) for deploying with NiceGUI or FastAPI.

---

## Testing

### Test Your Story Logic

```python
# tests/test_game.py
from bardic import BardEngine

def test_inventory():
    engine = BardEngine()
    engine.load_story_file("story.bard")

    output = engine.start()
    assert "Welcome" in output.content

    # Make choice
    output = engine.choose(0)
    assert output.passage_id == "Expected_Passage"
```

Run tests:

```bash
pytest tests/
```

---

## Next Steps

Now that you're set up:

1. **[Part 1: Your First Branching Story](01_first_story.md)** - Learn the basics
2. **[Language Spec](../spec.md)** - Complete syntax reference
3. **[Example Projects](https://github.com/bardic-lang/examples)** - See Bardic in action

---

**Ready to start building?**

**[→ Continue to Part 1: Your First Branching Story](01_first_story.md)**
