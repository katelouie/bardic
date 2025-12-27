# Changelog

All notable changes to Bardic will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Include a `game_logic/` directory inside all generated projects from `bardic init`.
- `bardic play` now accepts and auto-compiles `.bard` files (into memory).

- **Undo/Redo System** - Players can now rewind and replay choices
  - `engine.undo()` / `engine.redo()` methods for programmatic control
  - `engine.can_undo()` / `engine.can_redo()` for UI button state
  - `GameSnapshot` dataclass captures complete game state (passage, variables, used choices, hooks)
  - Stack-based architecture with configurable depth (default: 50)
  - Redo stack clears on new choices (timeline branching)
  - Snapshots taken before navigation for correct restore point
  - Browser template includes ← → navigation buttons in header

- **Hooks System** - Background systems that run every turn
  - `@hook event_name PassageName` - Register a passage to run on an event
  - `@unhook event_name PassageName` - Unregister a hooked passage
  - `engine.register_hook()` / `engine.unregister_hook()` for programmatic control
  - `engine.trigger_event()` executes all passages hooked to an event
  - Built-in `turn_end` event fires after every `choose()` call
  - FIFO execution order (first registered, first run)
  - Idempotent registration (duplicate hooks ignored)
  - Hooks can self-remove inside `@if` blocks
  - Hook state included in undo/redo snapshots

- **@join Directive** - Inline choice blocks that merge back together (like Ink gathers)
  - `+ [Choice] -> @join` with indented block content below the choice
  - `@join` marker where all choices merge back together
  - Block content renders only when that choice is selected
  - Variables set in blocks persist after the merge
  - Multiple sequential `@join` markers per passage (sections)
  - Works with conditional choices (`+ {cond} [Text] -> @join`)
  - Works with one-time choices (`* [Text] -> @join`)
  - Compatible with hooks (`@hook`/`@unhook` in blocks)
  - Full undo/redo support (section index in snapshots)
  - pytest tests: `tests/test_join.py`

### Changed

### Fixed

## [0.5.0] - 2025-12-12

### Added

- **Browser Distribution (`bardic bundle`)** - Package games for itch.io and web deployment
  - New `bardic bundle` CLI command creates self-contained browser packages
  - `--zip` / `-z` flag creates ready-to-upload ZIP files
  - `--theme` option with three built-in themes: `dark`, `light`, `retro`
  - `--name` option to customize game title
  - `--output` / `-o` to specify output directory

- **Local Pyodide Runtime** - No CDN dependency, faster loading
  - Bundles Pyodide 0.29.0 core (~12 MB) for offline Python execution
  - Pre-installed packages for interactive fiction authors:
    - `numpy` - Math, random distributions, procedural generation
    - `pillow` - Image processing
    - `networkx` - Graph-based world maps, relationship webs
    - `pyyaml` - YAML data files
    - `regex` - Advanced pattern matching
    - `jinja2` - Text templating
    - `nltk` - Natural language processing
    - `sympy` - Symbolic math
    - `pygments` - Syntax highlighting
    - `rich` - Rich text formatting
    - `micropip` - Install additional pure-Python packages at runtime
    - `python_dateutil`, `attrs`, `more_itertools`, `sortedcontainers`
  - Total bundle size: ~17 MB (compressed ZIP)

- **Browser Engine (`engine_browser.py`)** - Pyodide-compatible runtime
  - localStorage-based save/load system
  - `save_to_browser(slot_name)` - Save game state
  - `load_from_browser(slot_name)` - Load saved game
  - `list_browser_saves()` - List available save slots
  - `delete_browser_save(slot_name)` - Delete a save
  - Works with both direct Pyodide and PyScript

- **Browser Player UI**
  - Progress bar during Pyodide initialization
  - Save/Load/Restart buttons
  - Simple markdown rendering (bold, italic, paragraphs)
  - CSS custom properties for easy theming
  - Mobile-responsive layout
  - Notification system for user feedback

- **Sample Game: "The Midnight Cafe"**
  - Atmospheric interactive fiction demo
  - Demonstrates Relationship system from stdlib
  - Multiple endings based on relationship stats
  - Located at `stories/samples/midnight_cafe.bard`

### Changed

### Fixed

## [0.4.0] - 2025-12-09

### Added

- **`_state` special variable** - Direct access to global state dictionary for safe variable inspection
  - Use `_state.get('var', default)` for safe access with defaults
  - Check existence with `'var' in _state`
  - Inspect available variables with `_state.keys()`
- **`_local` special variable** - Direct access to local scope (passage parameters)
  - Always available (empty dict if no parameters)
  - Use `_local.get('param', default)` for optional parameters
  - Perfect for reusable passages with conditional logic
- Added `type()` and `isinstance()` to safe builtins for type inspection
- Added Tutorial Step 3.5: Reusable Passages & The Standard Library
- Comprehensive test suite with 100+ tests
  - 18 tests for `_state` and `_local` special variables
  - 32 error handling tests
  - 9 object-based story tests
  - Test fixtures for custom objects
- CI/CD on GitHub Actions (Python 3.10, 3.11, 3.12)

### Changed

### Fixed

- Bug preventing compiling on inline conditionals in choice text
- `bardic compile` success message now shows total size including all `@include`-d files
- Fix bug on for-loop `@endfor` depth tracking causing nested loops to error on compile
- Parser now properly handles square brackets inside choice conditionals (e.g., `{cards[1].reversed}`)
- Setter bug in relationships.py
- Missing passages in Coffee Shop example story.
- Bug in template bardic files using old syntax that caused them to not run properly.

### Removed

## [0.3.0] - 2025-11-08

### Added

- **Passage Parameters (MAJOR):**
  - Passages can now accept parameters like functions: `:: PassageName(param1, param2=default)`
  - Navigate with arguments: `-> PassageName(value)` or `+ [Choice] -> PassageName(arg1, arg2)`
  - Support for positional and keyword arguments: `-> Target(100)` or `-> Target(hp=100)`
  - Default parameter values: `:: Greet(name="World", greeting="Hi")`
  - Parameters are local variables (don't persist to global state)
  - Compile-time validation ensures required params are provided
  - **Unlocks dynamic content patterns:** shops, NPC conversations, combat encounters, any template passage!
  - Example: `@for item in inventory: + [Buy {item.name}] -> BuyItem(item) @endfor`

- Updated `spec.md` and `README.md` to document new passage parameter feature
- Inventory and Economy modules to `stdlib`
- Wandering Merchant story to `examples`

## [0.2.0] - 2025-11-07

### Added

- **Inline Conditional Enhancements:**
  - Mixed text + expressions in conditional branches: `{health > 50 ? HP: {health} | You're weak}`
  - Inline conditionals in choice text: `+ [{health > 0 ? Fight (HP: {health}) | Too weak}] -> Battle`
  - Nested expressions inside conditionals: fully recursive rendering
  - Choice text supports pure expressions: `+ [You have {gold} coins] -> Shop`

- **Comprehensive Error Validation (100% coverage!):**
  - Expression validation: detects unclosed braces, extra closing braces, mismatched nesting
  - Python syntax validation: AST parsing catches all syntax errors at compile time
  - @py block validation: missing colons, unclosed blocks
  - Control flow validation: @if/@elif/@else/@endif/@for/@endfor syntax
  - Directive validation: @render and @input parameter checking
  - @include edge cases: missing file path, multiple files
  - All errors use beautiful `format_error()` with visual context
  - Source line mapping for @include scenarios (shows correct file/line)
  - 35+ test files covering all error scenarios

### Changed

- Updated `parse_content_line()` to accept line_num, lines, filename, line_map for better error reporting
- Updated `split_expressions_with_depth()` to validate brace matching
- Choice validation now distinguishes between conditionals (before `[`) and expressions (inside `[...]`)
- All parse_content_line() call sites updated across core.py and blocks.py

### Fixed

- Apostrophes in inline conditional text no longer break syntax (VSCode extension)
- Choice text validation no longer treats expressions as conditionals
- Expression validation catches all brace mismatches with helpful error messages

## [0.1.0] - 2025-11-03

### Added

- Initial release 🎉
- **Core Syntax:**
  - Passages (`:: PassageName`)
  - Choices (`+ [text] -> target`)
  - Variables (`~ var = value`)
  - Expressions (`{variable}` with format specs like `{price:.2f}`)
- **Python Integration:**
  - Multi-line Python blocks (`@py:` ... `@endpy`)
  - Inline Python expressions in content
  - Safe builtins and standard library imports
- **Control Flow:**
  - Conditionals (`@if:`, `@elif:`, `@else:`, `@endif`)
  - Loops (`@for:` ... `@endfor`)
  - Immediate jumps (`-> TargetPassage`)
- **Organization:**
  - File includes (`@include path/to/file.bard`)
  - Import statements (standard Python syntax)
- **Comments:**
  - Full-line comments (`#`)
  - Inline comments (`//`)
- **CLI Tools:**
  - `bardic compile` - Compile .bard to JSON
  - `bardic play` - Terminal story player
- **Engine Features:**
  - State management and variable persistence
  - Conditional choice filtering
  - Object attribute access in expressions
  - Format specifiers for number/string formatting

### Documentation

- Complete language specification (spec.md)
- Installation and quickstart guide
- Example stories
