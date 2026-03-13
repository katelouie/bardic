# CLAUDE.md

This file provides guidance to Claude Code when working with the Bardic codebase.

## Project Overview

Bardic is a Python-first interactive fiction engine for modern web applications. It compiles `.bard` story files into JSON for runtime execution, with deployment targets including browser bundles (Pyodide), Python desktop (CLI), and web app frameworks (FastAPI + React, NiceGUI, Reflex).

**Current version:** 0.9.0 — 529 tests, modular engine architecture, browser fork eliminated.

## Python Environment

```bash
pyenv activate bardic     # Always activate before running Python commands
```

Required Python version: 3.10+

## Common Commands

```bash
# Install in development mode
pip install -e .

# Compile a .bard story to JSON
bardic compile story.bard
bardic compile story.bard -o output.json

# Play in terminal
bardic play story.json

# Lint a story (structural analysis, attribute checking)
bardic lint story.bard
bardic lint story.bard --verbose --json-output

# Generate story graph (GraphViz)
bardic graph story.json

# Bundle for browser (Pyodide + HTML)
bardic bundle story.bard
bardic bundle story.bard --theme dark --output dist/

# Initialize a new project from template
bardic init nicegui    # or: web, reflex

# Start dev server (FastAPI + React)
bardic serve story.json

# Run tests
pyenv activate bardic && pytest
pytest tests/test_renderer.py -v          # specific test file
pytest -k "test_undo"                     # by name pattern
```

## Architecture

### Three-Layer Design

```
.bard file → Parser → dict → Compiler → JSON → Engine → PassageOutput
```

1. **Parser** (`bardic/compiler/parser.py` + `bardic/compiler/parsing/`)
   - Parses `.bard` source into intermediate representation
   - Modular: core.py, blocks.py, content.py, directives.py, validation.py, preprocessing.py
   - Handles: passages, choices, variables, @if/@for/@join blocks, @include, @hook, @render directives, @py: blocks, inline conditionals

2. **Compiler** (`bardic/compiler/compiler.py`)
   - Thin wrapper: `compile_file()` and `compile_string()`
   - Resolves @include directives, outputs JSON

3. **Runtime Engine** (`bardic/runtime/` — 8 modules)

### Runtime Module Structure

```
bardic/runtime/
├── engine.py       ~770 lines   Facade: goto(), choose(), current(), trigger_event()
├── renderer.py     ~600 lines   Content token rendering, loops, conditionals, choice filtering
├── executor.py     ~430 lines   Command execution, Python blocks, imports, safe builtins
├── state.py        ~400 lines   Undo/redo stacks, save/load serialization, GameSnapshot
├── directives.py   ~240 lines   @render directive processing, argument binding, React output
├── browser.py      ~130 lines   localStorage save/load adapter (BrowserStorageAdapter)
├── types.py        ~95 lines    PassageOutput, GameSnapshot dataclasses
└── hooks.py        ~75 lines    HookManager for event hook registration
```

**Key design patterns:**
- **Compose by reference** — subsystems share state dicts by reference, mutations visible everywhere
- **Callable providers** — renderer/directives get eval_context/builtins as lambdas, decoupled from engine
- **Environment parameter** — `BardEngine(story_data, environment="browser")` configures for browser vs desktop
- **Thin delegation** — engine keeps one-liner methods that forward to subsystems
- **Mutate in place** — undo/redo/load use `clear() + update()` to preserve shared references

### Engine Public API

```python
engine = BardEngine(story_data)                    # Desktop mode
engine = BardEngine(story_data, environment="browser")  # Browser mode

output = engine.goto("PassageName")   # Navigate + execute + render + cache
output = engine.current()             # Return cached output (safe, idempotent)
output = engine.choose(index)         # Select choice by index + navigate

engine.undo()                         # Restore previous state
engine.redo()                         # Restore undone state
engine.can_undo() / engine.can_redo() # Check availability

engine.save_game(filepath)            # Desktop save
engine.load_game(filepath)            # Desktop load

# Browser mode only (auto-attached):
engine.save_to_browser(slot_name)
engine.load_from_browser(slot_name)
engine.list_browser_saves()
```

**PassageOutput** fields: `content`, `choices`, `passage_id`, `render_directives`, `input_directives`

### Stdlib Modules

```
bardic/stdlib/
├── dice.py          Dice rolling (d6, 2d8+3, advantage/disadvantage)
├── inventory.py     Item management (add, remove, quantity tracking)
├── economy.py       Currency system (earn, spend, transfer)
├── relationship.py  NPC relationships (trust, affinity, thresholds)
└── quest.py         Quest journal (objectives, stages, completion)
```

## Bard Language Syntax

```bard
:: PassageName                          # Passage header
:: Shop(item, price=10)                 # Parameterized passage

Content with {variable} interpolation.
{price:.2f} for format specifiers.
{condition ? "true text" | "false text"} # Inline conditional

~ variable = value                      # Variable assignment
~ health = health - 10                  # Expression assignment

+ [Choice text] -> TargetPassage        # Basic choice (reusable)
* [One-time choice] -> Target           # One-time choice (disappears after use)
+ {gold >= 10} [Buy sword] -> Shop      # Conditional choice
+ [Inline block] -> @join               # Join choice (inline branching)
    Block content here.
@join                                   # Merge point for join choices

-> TargetPassage                        # Jump (instant navigation)
-> @prev                                # Jump to previous passage

@if condition                           # Conditional block
@elif other_condition
@else
@endif

@for item in items                      # Loop
@endfor

@py:                                    # Python code block
from bardic.stdlib.inventory import Inventory
inv = Inventory()
@endpy

@hook turn_end                          # Event hook
~ turns_played = turns_played + 1
@endhook

@render component_name(arg1, arg2=val)  # Render directive (frontend component)
@input input_name(prompt="Enter name")  # Input directive

@include "other_file.bard"              # File inclusion

^tag                                    # Passage tag
// Comment                              # Line comment
```

### Built-in Variables

- `_state` — dict of all game state (for safe access: `_state.get('hp', 100)`)
- `_local` — dict of passage parameters (for defaults: `_local.get('param', 'default')`)
- `_visits` — dict of passage visit counts (`_visits.get("Shop", 0)`)
- `_turns` — int of player choices made (incremented by `choose()`)

## CLI Commands

| Command | Purpose |
|---------|---------|
| `bardic compile` | Compile .bard → JSON |
| `bardic play` | Play story in terminal |
| `bardic lint` | Structural + attribute analysis |
| `bardic graph` | Generate story graph (GraphViz) |
| `bardic bundle` | Browser bundle (Pyodide + HTML) |
| `bardic init` | Initialize project from template |
| `bardic serve` | Dev server (FastAPI + React) |

## File Organization

```
bardic/
├── compiler/
│   ├── parser.py              # Entry point
│   ├── compiler.py            # File I/O wrapper
│   └── parsing/               # Parser modules (core, blocks, content, directives, validation, preprocessing)
├── runtime/                   # 8 modules (see above)
├── stdlib/                    # 5 modules (dice, inventory, economy, relationship, quest)
├── cli/
│   ├── main.py                # Click CLI (compile, play, init, serve)
│   ├── bundler.py             # Browser bundle creation
│   ├── lint.py                # Lint command + diagnostics
│   └── graph.py               # Graph generation
├── templates/
│   ├── browser/               # Pyodide browser template (index.html, style.css, player.py)
│   ├── nicegui/               # NiceGUI template
│   ├── reflex/                # Reflex template
│   └── web/                   # React + FastAPI template
└── linter/                    # Lint plugin API (extract_python_code, parse_attribute_access)

tests/                         # 29 test files, 529 tests
├── test_engine.py
├── test_renderer.py
├── test_executor.py
├── test_state_manager.py
├── test_directives.py
├── test_hooks_manager.py
├── test_browser.py
├── test_parser.py
├── test_join.py
├── test_undo_redo.py
├── test_visits_turns.py
├── test_stdlib_*.py           # 5 stdlib test files (114 tests)
├── error_handling/            # Error case test .bard files
└── fixtures/                  # Test fixtures

docs/                          # Tutorials, API docs, spec, cookbook
stories/samples/               # Example stories (coffee_shop, etc.)
```

## Testing

All tests use **pytest**. Run from project root with `pyenv activate bardic && pytest`.

Key test files map to runtime modules: `test_renderer.py`, `test_executor.py`, `test_state_manager.py`, `test_directives.py`, `test_hooks_manager.py`, `test_browser.py`.

## Browser Bundle Architecture

`bardic bundle` creates a self-contained browser-playable distribution:
- Copies all 8 runtime modules to `bardic/runtime/` in the bundle
- Copies stdlib modules to `bardic/stdlib/`
- Loads Pyodide, writes modules to virtual filesystem, uses standard Python imports
- `BardEngine(game_data, environment="browser")` — excludes `__import__`, attaches localStorage methods
- Three CSS themes: dark, light, retro
