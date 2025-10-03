# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bardic is a Python-first interactive fiction engine for modern web applications. It compiles `.bard` story files into JSON for runtime execution, designed for narratives that integrate with Python backends (FastAPI) and React frontends.

**Current Status:** Early MVP development (Week 1 complete)

## Python Environment

**CRITICAL:** Always activate the pyenv environment before running Python commands:

```bash
pyenv activate bardic
```

Required Python version: 3.12+

## Common Commands

### Development Workflow

```bash
# Install in development mode
pip install -e .

# Compile a .bard story to JSON
bardic compile story.bard
bardic compile story.bard -o output.json

# Play a compiled story in the terminal
bardic play story.json
bardic play story.json --no-color

# Run parser tests (basic test script, not pytest)
pyenv activate bardic && python tests/test_parser.py

# Run engine tests
pyenv activate bardic && python test_engine.py
```

### CLI Structure

The `bardic` CLI has two main commands:
- `compile` - Parses .bard files and outputs JSON
- `play` - Runs compiled JSON stories interactively in the terminal

## Architecture

### Three-Layer Design

1. **Parser** (`bardic/compiler/parser.py`)
   - Parses `.bard` source files into intermediate representation
   - Handles passage headers (`:: PassageName`), content, choices (`+ [text] -> target`), and variable assignments (`~ var = value`)
   - Returns dict with `version`, `initial_passage`, and `passages`

2. **Compiler** (`bardic/compiler/compiler.py`)
   - Thin wrapper around parser that handles file I/O
   - Converts `.bard` → JSON
   - Methods: `compile_file()` and `compile_string()`

3. **Runtime Engine** (`bardic/runtime/engine.py`)
   - `BardEngine` class executes compiled stories
   - **Separates execution from rendering** for safety
   - Manages state (`engine.state` dict for variables)
   - Caches output to prevent re-execution
   - Navigation API:
     - `goto(passage_id)` - Navigate + execute + cache (use for navigation)
     - `current()` - Read cached output (use for display, safe, no side effects)
     - `choose(index)` - Use filtered choices + navigate (use for player choices)
   - See `docs/engine-api.md` for detailed API contract

### Data Flow

```
.bard file → Parser → dict → Compiler → JSON → Engine → PassageOutput
```

### Key Data Structures

**PassageOutput** (dataclass in engine.py):
- `content: str` - Rendered text
- `choices: List[Dict]` - Available choices with `text` and `target`
- `passage_id: str` - Current passage ID

**Compiled Passage Format**:
```json
{
  "id": "PassageName",
  "content": [{"type": "text", "value": "..."}, {"type": "expression", "code": "var"}],
  "choices": [{"text": "Choice text", "target": "TargetPassage"}],
  "execute": [{"type": "set_var", "var": "name", "expression": "value"}]
}
```

## Bard Language Syntax (Current Implementation)

### Passages
```bard
:: PassageName
Content goes here.
```

### Choices
```bard
+ [Choice text] -> TargetPassage                    # Basic choice
+ {condition} [Conditional choice] -> TargetPassage # Only shows if condition is true
```

### Variables
```bard
~ variable = value           # Assignment
{variable}                   # Display in content
~ health = health - 10       # Expressions
```

### Content Interpolation
Content is tokenized into:
- `{"type": "text", "value": "..."}` - Plain text
- `{"type": "expression", "code": "..."}` - Variables/expressions in `{}`

Variables are evaluated at render time using restricted `eval()` with `engine.state` as context.

## Important Implementation Details

### Engine Architecture: Separation of Execution and Rendering

**Key Principle**: Commands execute **exactly once** per passage entry.

**Private Methods**:
- `_execute_passage(passage_id)` - Executes commands (side effects only)
- `_render_passage(passage_id)` - Renders content and filters choices (pure, no side effects)

**Public API**:
- `goto(passage_id)` - Executes + renders + caches
- `current()` - Returns cached output (safe, idempotent)
- `choose(index)` - Uses filtered choices from cache

**Cache**: `_current_output` stores the last PassageOutput, preventing re-execution when `current()` is called multiple times.

See `docs/engine-api.md` for complete API documentation.

### Variable System (parser.py:51-64, engine.py:221-253)

- Assignments (`~ var = value`) are stored in `passage["execute"]` as `set_var` commands
- Executed **once** when `goto()` navigates to a passage
- Uses restricted eval with `{"__builtins__": {}}` for safety
- Falls back to literal parsing for simple values (strings, numbers, bools)
- State persists globally in `engine.state`

### Conditional Choices (parser.py:98-117, engine.py:122-138)

- Choices can have optional `condition` field: `+ {health > 0} [Victory!] -> Win`
- Parsed as: `{"text": "Victory!", "target": "Win", "condition": "health > 0"}`
- Filtered during rendering based on current state
- `choose(index)` uses **filtered** choices, so indices always match what user sees

### Content Rendering (engine.py:270-287)

- Content is a list of tokens (text + expressions)
- Expressions are evaluated with current state
- Errors in expressions show as `{ERROR: code - message}` for debugging

### Parser Line Processing (parser.py:28-87)

Line types processed in order:
1. Passage headers (`:: Name`)
2. Variable assignments (`~ var = value`)
3. Choices (`+ [text] -> target` or `+ {condition} [text] -> target`)
4. Content with interpolation (tokenized via `parse_content_line()`)
5. Empty lines (become `\n` tokens)

## File Organization

```
bardic/
├── compiler/
│   ├── parser.py      # .bard → dict
│   └── compiler.py    # File I/O wrapper
├── runtime/
│   └── engine.py      # BardEngine execution
└── cli/
    └── main.py        # Click-based CLI (compile, play)

tests/
└── test_parser.py     # Basic parser test

*.bard                 # Test story files
*.json                 # Compiled stories
```

## Development Roadmap

Reference `spec.md` for full language specification and planned features.

**Completed (Week 1):**
- Basic passages and choices
- Variable assignments and interpolation
- Compiler and runtime engine
- CLI for compile and play

**Next (Week 2):**
- File includes (`@include`)
- Conditional choices
- Enhanced expressions

**Future:**
- Python code blocks (`<<py>>`)
- Conditionals (`<<if>>`)
- Loops (`<<for>>`)
- Render directives for React (`@`)
- Markdown support

## Testing

Currently using simple test scripts (not pytest framework):
- `tests/test_parser.py` - Parser output inspection
- `test_engine.py` - Engine functionality
- Various `.bard` test files for manual testing

Run with: `pyenv activate bardic && python test_file.py`
