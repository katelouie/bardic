# Lint Plugins

`bardic lint` checks your story for structural issues — broken jump targets, orphaned passages, dead ends, and more. But every game has its own mechanics, data files, and conventions that generic checks can't cover.

**Lint plugins** let you add game-specific checks that run alongside the built-in ones. They use the same diagnostic system, the same output format, and the same `--verbose` / `--json-output` flags.

## Quick Start

1. Create a `linter/` directory in your project root
2. Add a Python file with a `check_*` function
3. Run `bardic lint` — your plugin runs automatically

```
my-game/
├── stories/
│   └── main.bard
├── game_logic/
│   └── characters.py
└── linter/
    └── check_items.py      <-- your plugin
```

```python
# linter/check_items.py
from bardic.cli.lint import LintReport

def check_item_names(story_data, report, project_root):
    """Validate that item references match our item database."""
    # Your checking logic here
    report.warning("GW001", "Unknown item 'rusty_sword'",
                   hint="Did you mean 'iron_sword'?")
```

```
$ bardic lint stories/main.bard --verbose

  BARDIC LINT  stories/main.bard
  ─  ─  ─  ─  ─  ─  ─  ─  ─  ─
  42 passages · 3 files · 87 choices · 1 plugin

  ⚠ GW001  Unknown item 'rusty_sword'
           → Did you mean 'iron_sword'?
```

## How It Works

When `bardic lint` runs, it:

1. Compiles your `.bard` file (following all `@include` directives)
2. Runs built-in structural checks (E001–I002)
3. Looks for a `linter/` directory by walking up from the `.bard` file
4. Loads every `.py` file in `linter/` (except files starting with `_`)
5. Calls every `check_*` function it finds in those files
6. Displays all results together — built-in and plugin diagnostics mixed

Use `--no-plugins` to skip plugin checks:

```
bardic lint stories/main.bard --no-plugins
```

## Writing a Plugin

### Function Signature

Every check function receives three arguments:

```python
def check_something(
    story_data: dict,           # The compiled story (passages, choices, code)
    report: LintReport,         # Add your findings here
    project_root: Path,         # The directory containing linter/
):
```

- **`story_data`** — The compiled story as a dict. Contains `passages`, `imports`, `initial_passage`, etc. This is the same data that `bardic compile` produces.
- **`report`** — Call `report.error()`, `report.warning()`, or `report.info()` to add findings.
- **`project_root`** — The directory that contains your `linter/` folder. Use it to find data files (`project_root / "data" / "items.json"`).

### Reporting Diagnostics

```python
# Error — something is definitely broken
report.error("GE001", "Missing required item definition for 'quest_key'")

# Warning — likely a bug, but might be intentional
report.warning("GW001", "Unknown item 'rusty_sword'",
               hint="Did you mean 'iron_sword'?")

# Info — informational, only shown with --verbose
report.info("GI001", "Item database has 47 entries")
```

### Diagnostic Codes

Pick a prefix for your project to avoid collisions with built-in codes:

| Prefix | Meaning |
|--------|---------|
| `E___` | Built-in errors (reserved) |
| `W___` | Built-in warnings (reserved) |
| `I___` | Built-in info (reserved) |
| `P000` | Plugin system errors (reserved) |
| `GE__` / `GW__` | Your game's errors/warnings |
| `AE__` / `AW__` | Arcanum-specific codes |

You can use any string as a code — the linter doesn't enforce a format.

## Helper API

Import these from `bardic.cli.lint` to avoid reinventing the wheel:

### `extract_python_code(story_data) -> list[tuple[str, str]]`

Extracts all Python code from the compiled story — `@py:` blocks, `~ expr` statements, `{expressions}`, `@if` conditions, choice conditions, `@for` iterables, `@render` expressions, and top-level imports.

Returns a list of `(code_string, context_description)` tuples. The context is a human-readable string like `"passage 'Chen.Session1'"`.

```python
from bardic.cli.lint import extract_python_code

snippets = extract_python_code(story_data)
for code, context in snippets:
    if "inventory" in code:
        print(f"Found inventory reference in {context}")
```

### `parse_attribute_access(code) -> tuple[set, set, set]`

Parses a Python code string with AST and extracts attribute access patterns.

Returns `(writes, reads, method_calls)` where each is a set of `(object_name, attribute_name)` tuples.

```python
from bardic.cli.lint import parse_attribute_access

code = 'player.health -= 10\nplayer.add_item("sword")'
writes, reads, methods = parse_attribute_access(code)
# writes: {('player', 'health')}
# reads:  {('player', 'health')}  (augmented assignment is both)
# methods: {('player', 'add_item')}
```

### `LintReport`

The report object with methods for adding diagnostics:

```python
from bardic.cli.lint import LintReport, Severity

report.error(code, message, hint="optional hint")
report.warning(code, message, hint="optional hint")
report.info(code, message, hint="optional hint")
```

### `Diagnostic` and `Severity`

If you need to inspect existing diagnostics:

```python
from bardic.cli.lint import Severity

for d in report.diagnostics:
    if d.severity == Severity.ERROR:
        print(f"Error: {d.message}")
```

## File Organization

```
linter/
├── _helpers.py          # Shared helpers (underscore = not loaded as plugin)
├── check_items.py       # Item validation
├── check_npcs.py        # NPC consistency
└── check_combat.py      # Combat balance
```

Files starting with `_` are ignored by the plugin loader. Use them for shared utilities:

```python
# linter/_helpers.py
def load_game_data(project_root):
    """Shared data loading for all plugins."""
    ...

# linter/check_items.py
from linter._helpers import load_game_data

def check_item_names(story_data, report, project_root):
    data = load_game_data(project_root)
    ...
```

## Working with Story Data

The `story_data` dict has this structure:

```python
{
    "version": "1.0",
    "initial_passage": "Start",
    "imports": [                    # Top-level Python imports
        "from game_logic import Player",
    ],
    "passages": {
        "PassageName": {
            "execute": [            # @py: blocks and ~ statements
                {"type": "python_block", "code": "x = 1\ny = 2"},
                {"type": "python_statement", "code": "z = x + y"},
            ],
            "content": [            # Text, expressions, conditionals, loops
                "Plain text",
                {"type": "expression", "expression": "player.name"},
                {"type": "conditional", "branches": [...]},
            ],
            "choices": [            # Player choices
                {"text": "Go north", "target": "North", "condition": "has_key"},
            ],
            "tags": ["DREAM:GOTHIC"],
        },
    },
}
```

### Common Patterns

**Find all passage names:**
```python
passages = list(story_data.get("passages", {}).keys())
```

**Find all jump targets:**
```python
targets = set()
for pid, pdata in story_data["passages"].items():
    for choice in pdata.get("choices", []):
        if "target" in choice:
            targets.add(choice["target"])
```

**Find specific function calls in story code:**
```python
import ast
import textwrap
from bardic.cli.lint import extract_python_code

for code, ctx in extract_python_code(story_data):
    code = textwrap.dedent(code)
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check function name, arguments, etc.
            ...
```

## Example: Full Plugin

Here's a complete plugin that validates card names in a tarot game:

```python
"""Validate tarot card names against game data."""

import ast
import json
import textwrap
from pathlib import Path

from bardic.cli.lint import LintReport, extract_python_code


def check_card_names(story_data: dict, report: LintReport, project_root: Path):
    """Validate card names in Deck() calls against card database."""
    # Load valid card names from game data
    cards_file = project_root / "assets" / "cards.json"
    if not cards_file.exists():
        return

    with open(cards_file) as f:
        valid_names = {card["name"] for card in json.load(f)}

    # Find card names in Deck(cards=[...]) calls
    for code, ctx in extract_python_code(story_data):
        code = textwrap.dedent(code)
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not (isinstance(node.func, ast.Name) and node.func.id == "Deck"):
                continue

            # Find cards= keyword argument
            for kw in node.keywords:
                if kw.arg == "cards" and isinstance(kw.value, ast.List):
                    for elt in kw.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            if elt.value not in valid_names:
                                import difflib
                                close = difflib.get_close_matches(
                                    elt.value, valid_names, n=1, cutoff=0.7
                                )
                                hint = f"Did you mean '{close[0]}'?" if close else ""
                                report.warning(
                                    "GW001",
                                    f"Unknown card '{elt.value}' (in {ctx})",
                                    hint=hint,
                                )
```

## Built-in Diagnostic Codes Reference

For reference, these codes are used by the built-in checks:

| Code | Severity | Description |
|------|----------|-------------|
| E001 | Error | Missing passage (broken jump target) |
| E002 | Error | Duplicate passage name |
| W001 | Warning | Orphaned passage (unreachable) |
| W002 | Warning | Dead-end passage (no exits) |
| W003 | Warning | Empty passage |
| W004 | Warning | Sticky self-loop (potential infinite loop) |
| W005 | Warning | Attribute read but never written |
| I001 | Info | Dead-end that looks like intentional ending |
| I002 | Info | Passage with many choices |
| P000 | Warning | Plugin failed to execute |
