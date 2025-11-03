# Bardic

[![PyPI version](https://badge.fury.io/py/bardic.svg)](https://badge.fury.io/py/bardic)
[![Python Version](https://img.shields.io/pypi/pyversions/bardic.svg)](https://pypi.org/project/bardic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Bardic is a Python-first interactive fiction engine that lets you import your own classes and use real Python in your stories. It's built for modern Python web applications. It's also for people who want to make narrative games without learning web dev.**

Write your branching narrative in a clean, simple syntax (inspired by Ink), and when you need complex logic, just use Python. Bardic is designed to be the "story layer" for games that need rich data models, complex state, and custom UIs. Bardic is frontend-agnostic and works with NiceGUI, Reflex, React+FastAPI, or any other frontend layer you want to build with. It compiles stories to JSON and is portable and versatile.

## Why Bardic? A New Choice for Writers and Developers

You have great tools like Twine, Ink, and Ren'Py. So, why did I create Bardic?

Bardic is built for stories that get *complex*.

- **Twine** is fantastic for building "Choose Your Own Adventure" style branching stories.
- **Ink** is a brilliant, elegant language for managing branching state (like `GOTO`s and `GATHER`s).
- **Bardic** is for when your "state" isn't just a number or a string, but a complex Python object. It's for when you want to write:
  - "I want this character to have an inventory, which is a **list of `Item` objects**."
  - "I need to **import my `Player` class** and call `player.take_damage(10)`."
  - "I want to simulate a full tarot deck, with 78 **`Card` objects**, each with its own properties and methods."

Have you ever been writing and thought, "I wish I could just `import` my custom class and use it"? **That's what Bardic does.**

It bridges the gap between simple, text-based branching logic and the full power of a programming language, letting you use both in the same file.

## A Quick Example

Bardic syntax is designed to be simple and stay out of your way. Here's a small story that shows off the core features:

```bard
# Import your own Python classes, just like in a .py file
from my_game.character import Player

:: Start
# Create a new Player object
~ hero = Player("Hero")

Welcome to your adventure, {hero.name}!
You have {hero.health} health.

+ [Look around] -> Forest
+ [Check your bag] -> Inventory

:: Forest
The forest is dark and spooky.
~ hero.sprint() # Call a method on your object
You feel a bit tired.

+ [Go back] -> Start

:: Inventory
# Use Python blocks for complex logic
@py:
  if not hero.inventory:
    bag_contents = "Your bag is empty."
  else:
    # Use list comprehensions, f-strings...
    item_names = [item.name for item in hero.inventory]
    bag_contents = f"You have: {', '.join(item_names)}"
@endpy

{bag_contents}

+ [Go back] -> Start
```

## Core Features

- **Write Python, Natively:** Use `~` for simple variable assignments or drop into full `@py:` blocks for complex logic.
- **Use Your Own Objects:** `import` your custom Python classes (like `Player`, `Card`, or `Client`) and use them directly in your story.
- **Complex State, Solved:** Bardic's engine can save and load your *entire game state*, including all your custom Python objects, right out of the box.
- **You Write the Story, Not the UI:** Bardic doesn't care if you use React, NiceGUI, or a terminal. It produces structured data for any UI.
  - Use the **NiceGUI** template for a pure-Python, single-file game.
  - Use the **Web** template (FastAPI + React) for a production-ready, highly custom web game.
- **Clean, Writer-First Syntax:** Focus on your story with a minimal, line-based syntax for passages (`::`), choices (`+`), and text.
- **Visualize Your Story:** Automatically generate a flowchart of your entire story to find highlighted dead ends or orphaned passages with the `bardic graph` command.
- **Instant Start-Up:** Get a working game in 60 seconds with `bardic init`. It comes with a browser-based frontend pre-configured and ready to run with a single command. (NiceGUI, Reflex, or React -- take your pick.)
- **VS Code Integration:** You can install the [Bardic VS Code extension](https://github.com/katelouie/bardic-vscode) to get full syntax highlighting, code snippets and code folding in your IDE.

## Quick Start (in 4 Steps)

Get a new game running in under 60 seconds.

**1. Install Bardic:**

```bash
pip install bardic

# Or with NiceGUI template support
pip install bardic[nicegui]

# Or with other optional dependencies, if you want them
pip install bardic[nicegui,reflex,web,dev]
```

**2. Create a New Project:**
This creates a new folder with a full example game, ready to run in a pre-made frontend in your browser.

```bash
bardic init my-game
cd my-game
```

**3. Install Dependencies:**
The default template uses NiceGUI. If you didn't install with `[nicegui]`, install the project dependencies:

```bash
pip install -r requirements.txt
```

**4. Compile & Run!**

```bash
# 1. Compile your story from .bard to .json
bardic compile example.bard -o compiled_stories/example.json

# 2. Run the game player
python player.py
```

Your game is now running at `http://localhost:8080`!

### Installation Options

Bardic supports multiple UI frameworks. Choose the one you prefer:

| Framework | Install Command | Best For |
|-----------|----------------|----------|
| NiceGUI | `pip install bardic[nicegui]` | Pure Python, single-file games |
| FastAPI + React | `pip install bardic[web]` | Production web apps |
| Reflex | `pip install bardic[reflex]` | Python → React compilation |

Or install the core engine and add dependencies manually:

```bash
bardic init my-game
cd my-game
pip install -r requirements.txt
```

## The Bardic Toolkit (CLI)

Bardic comes with a command-line interface to help you build your game.

- `bardic init my-game`: Creates a new project from a template.
- `bardic compile story.bard`: Compiles your `.bard` file into a `.json` file that the engine can read.
- `bardic play story.json`: Plays your game directly in your terminal.
- `bardic graph story.json`: Generates a visual flowchart of your story (as a `.png` or `.svg`).

## Example Game: *Arcanum*

Need to see a large-scale project? The [Arcanum](https://github.com/katelouie/arcanum-game) cozy tarot reading game is built with Bardic. It's an example of using Bardic with custom Python classes, complex state, and a NiceGUI frontend.

## Where to Go Next?

- **New to Bardic?** I've put together a short [tutorial course](docs/tutorials/README.md) that walks you through all of the syntax and features of Bardic, from beginner to advanced.
- **Want to see all the syntax?** Check out the [Language Specification](https://github.com/katelouie/bardic/blob/main/docs/spec.md) for the full list of features, from loops to render directives.
- **Want to build the engine?** See our [`CONTRIBUTING.md`](CONTRIBUTING.md) for details on the architecture and development setup.
- **Want VS Code integration?** Download the [Bardic VS Code extension](https://github.com/katelouie/bardic-vscode) with full syntax highlighting, snippets and code folding.
