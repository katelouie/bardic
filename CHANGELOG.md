# Changelog

All notable changes to Bardic will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **CLI test suite** — 51 tests for CLI commands using Click's `CliRunner`:
  - `bardic compile` — 12 tests (basic compilation, custom output paths, metadata preservation, `@include` resolution, parent directory creation, error handling)
  - `bardic lint` — 13 tests (clean stories, W001/E002 diagnostics, compile-time vs lint-time error boundary, `--json-output`, `--errors-only`, `--verbose` flags, `@include` following, word count)
  - `bardic init` — 10 tests (all 4 templates: nicegui/web/browser/reflex, custom `--path`, error cases, file creation verification)
  - `bardic graph` — 8 CLI tests (PNG/SVG/PDF output, custom paths, passage/connection count reporting) + 8 `extract_connections()` unit tests (choice targets, jump targets, conditional branches, for-loops, text truncation, empty stories)
  - Total test count: 584 (up from 545)

### Changed

### Fixed

## [0.10.0] - 2026-03-13

### Added

- **Browser template upgrade** — 7-layer upgrade to the `bardic bundle` browser template:
  - **Asset pipeline** — bundler auto-detects and copies `assets/`, `custom.css`, `custom.js` from the story directory. New `--assets-dir` flag for custom asset locations.
  - **Image support** — `![alt](path)` in passage content renders as `<img>`. CSS variable `--image-rendering` (set to `pixelated` in custom.css for pixel art games). `.pixel` class for per-image override.
  - **Passage transitions** — fade out/in animations between passages (200ms). Initial load renders without transition.
  - **Sidebar panel** — collapsible sidebar (280px) with hamburger toggle. Two activation paths: `@render sidebar(content)` directive or `Bardic.sidebar()` hook in custom.js. Mobile: fixed overlay on screens under 600px.
  - **Render directive system** — `renderPassage()` now extracts `render_directives` and `input_directives` from engine output. Built-in renderers for `image`, `html`, `text_block`, `sidebar`, and `modal`. Custom `_serialize` function handles stdlib objects crossing the Pyodide bridge. Fallback renderer shows directive name + JSON data for unregistered directives (dev aid).
  - **Modal system** — reusable overlay for book views, inventory, card details. `Bardic.openModal(html)` / `Bardic.closeModal()`. Escape key and backdrop click to dismiss. ARIA attributes for accessibility.
  - **`Bardic` JavaScript API** — clean namespace object replacing scattered `window.*` globals. Registration methods: `Bardic.directive()`, `Bardic.sidebar()`, `Bardic.backgrounds()`, `Bardic.on()`. Lifecycle hooks: `start`, `passageRender`, `beforeChoice`. Typo detection warns on unknown event names with suggestions.
  - **Fixed header and sidebar** — header stays pinned at the top when scrolling, sidebar is fixed full-height below it. Sidebar respects player toggle (doesn't re-open on navigation after manually closing).

- **`bardic init --template browser`** — new project template for browser bundle games. Includes starter `example.bard`, `custom.css`, `custom.js` (with working Bardic API examples), `assets/`, `game_logic/`, and `linter/` directories.

- **Browser customization docs** — `docs/browser-customization.md` with full `Bardic` JS API reference, CSS variable table, and complete pixel-art RPG example. Linked from main README.

### Changed

### Fixed

- **stdlib `__all__` missing Quest exports** — `Quest` and `QuestJournal` were not exported from `bardic.stdlib`, despite being added in v0.7.1 with full tests and documentation.
- **f-string bug in executor.py error message** — `NameError` handler in `execute_python_block` displayed a literal `{list(exec_context.keys())}` instead of actual variable names.
- **Dead `_loop_context` allocation in renderer** — removed unused dict creation that ran on every loop iteration.
- **`HookManager.restore()` now mutates in place** — uses `clear() + update()` instead of reference replacement, consistent with all other restore paths in the codebase.
- **Typo fix** — "nagivation" → "navigation" in engine.py docstring.

## [0.9.2] - 2026-03-12

### Added

- **Pre-commit hooks** — ruff lint/format, trailing whitespace, end-of-file fixer, YAML/JSON validation, large file check. Install with `pre-commit install`.
- **Ruff configuration** in `pyproject.toml` — target Python 3.10, line length 100, per-file ignores for re-exports and templates.
- **Python 3.13 support** — added to CI test matrix and PyPI classifiers.
- **Inline image syntax** in browser templates — `![alt text](path)` now renders as `<img>` in browser bundle. Terminal player shows `[Image: alt text]`.

### Changed

- **CI test matrix expanded** from Python 3.12 only to 3.10, 3.11, 3.12, 3.13 with `fail-fast: false`.
- **CI lint job added** — ruff check + format verification runs before tests.
- **GitHub Actions updated** to checkout@v4 and setup-python@v5.
- **Codebase formatted** with ruff — consistent style across all source files.

### Fixed

- **`@py:` block functions invisible to comprehensions on Python <3.12** — functions defined inside `@py:` blocks (via `exec()`) couldn't be seen by dict/list/set comprehensions on Python 3.10-3.11 due to comprehension scoping rules. Fixed by using a single namespace for `exec()` instead of separate globals/locals. This was a silent compatibility issue that would cause `NameError` at runtime.
- **Passage parameters, `_state`, and `_local` now accessible in `@py:` blocks** (fixes [#5](https://github.com/katelouie/bardic/issues/5)) — `@py:` blocks were building their execution context separately from `~` statements, so passage parameters and the `_state`/`_local` special variables were only available in `~` lines. All three are now consistently available in both `~` statements and `@py:` blocks. Passage parameters are properly scoped and don't leak into global state.

## [0.9.1] - 2026-03-12

### Changed

- Updated PyPI classifiers to exclude Python versions 3.8 and 3.9.

## [0.9.0] - 2026-03-12

### Added

- **Word count and play time estimate in `bardic lint`** — the summary line now shows approximate word count (`~252,434 words`) and estimated play time (`~26.2 hr play time`). Play time is calculated from reading speed (~200 wpm) plus decision time (~10s per choice). Both values are also included in `--json-output` as `words` and `play_time_minutes`.

- **`environment` parameter for `BardEngine`** — `BardEngine(story_data, environment="browser")` configures the engine for browser deployment. Browser mode excludes `__import__` from safe builtins (modules must be pre-bundled) and attaches localStorage save/load methods automatically. Default is `"desktop"` (no behavior change for existing code).

- **`BrowserStorageAdapter`** — new `bardic.runtime.browser` module providing localStorage-based save/load for browser-bundled games. Wraps the engine's `StateManager` with `save()`, `load()`, `list_saves()`, and `delete_save()` methods. Automatically attached to the engine when `environment="browser"`.

- **Modular engine architecture** — the monolithic `engine.py` (2,153 lines) has been decomposed into 8 focused modules:
  - `engine.py` (771 lines) — facade: navigation (`goto`, `choose`, `current`), composition, event triggering
  - `renderer.py` (604 lines) — content token rendering, expression evaluation, loops, conditionals, choice filtering
  - `executor.py` (427 lines) — command execution, variable assignment, Python blocks, imports, builtins
  - `state.py` (401 lines) — undo/redo stacks, save/load serialization, `GameSnapshot`
  - `directives.py` (241 lines) — `@render` directive processing, argument binding, React output
  - `browser.py` (127 lines) — localStorage save/load adapter for browser deployment
  - `types.py` (95 lines) — `PassageOutput`, `GameSnapshot` dataclasses
  - `hooks.py` (75 lines) — `HookManager` for event hook registration

  All modules are independently testable. The public API (`BardEngine`) is unchanged — this is a purely internal refactoring.

- **149 new tests** across 6 test files (`test_hooks_manager.py`, `test_state_manager.py`, `test_directives.py`, `test_executor.py`, `test_renderer.py`, `test_browser.py`). Total test count: 529.

- **`hasattr`, `getattr`, `map`, `filter`** added to safe builtins for story code, unifying desktop and browser builtin sets.

### Changed

- **`bardic bundle` now ships real engine modules** — bundles include `bardic/runtime/*.py` (8 modules) instead of the old monolithic `engine_browser.py`. The Pyodide init loads modules into the virtual filesystem and uses standard Python imports. All engine features (hooks, `@join`, `@prev`, undo/redo) now work automatically in browser builds.

- **Undo/redo/load restore uses in-place mutation** — `GameSnapshot.restore_to()` and `StateManager.load_state()` now use `clear()` + `update()` on shared containers (`state`, `used_choices`, `_join_section_index`) instead of replacing them. This preserves references held by subsystems (executor, renderer) and fixes a latent bug where subsystem state could go stale after undo/redo.

### Removed

- **`engine_browser.py` — the browser engine fork is eliminated.** The 1,953-line forked copy of the engine (which was missing hooks, `@join`, and `@prev` support) has been deleted. One engine now serves both desktop and browser via the `environment` parameter. Every bug fix and feature addition applies to both environments automatically.

## [0.8.0] - 2026-03-11

### Added

- **`bardic lint` command** — structural and quality analysis for `.bard` story files. Compiles the story first (following all `@include` directives), then analyzes the passage graph to catch issues that regex-based checkers can't.
  - **E001**: Missing passages — broken jump targets that would crash at runtime
  - **E002**: Duplicate passage names
  - **W001**: Orphaned passages — defined but never jumped to (unreachable)
  - **W002**: Dead-end passages — no choices, jumps, or hooks (unintentional dead ends)
  - **W003**: Empty passages — no content, choices, or code
  - **W004**: Sticky self-loops — `+` choices that jump to their own passage (infinite loop)
  - **W005**: Attribute consistency — reads without writes, with typo detection via `difflib`. Suggests close matches (e.g., `"Did you mean 'session.artifacts_received'?"`)
  - **I001**: Dead-ends with ending-like names (informational, shown with `--verbose`)
  - **I002**: Passages with many visible choices — uses MAX across `@if` branches (not SUM), since players only see one branch
  - Smart choice counting accounts for mutually exclusive conditional branches
  - CLI options: `--verbose` (show info-level diagnostics), `--errors-only`, `--json-output` (for CI)
  - Human-readable output with colored severity icons, or structured JSON for tooling

- **Level 2 class-aware attribute checking** — `bardic lint` follows your story's `from game_logic.X import Y` statements, locates the Python source files on disk, and parses class definitions with AST. Class fields, `@property` decorators, private-to-public field mappings (`_trust` → `trust`), and inheritance chains are all resolved. Story variable names are mapped to classes via instantiation patterns (`blackthorn = BlackthornManor(...)`) and fuzzy matching (`session` → `Session`). Eliminates false positives for class-defined attributes that aren't explicitly assigned in `.bard` code.

- **Lint plugin system** — extensible, project-specific lint checks via a `linter/` directory.
  - Drop `.py` files in `linter/` at your project root — any `check_*` function is auto-discovered and run after built-in checks
  - Plugin signature: `def check_something(story_data, report, project_root)`
  - Files starting with `_` are ignored (use for shared helpers)
  - Plugin failures are caught gracefully and reported as P000 warnings
  - `--no-plugins` flag to skip project plugins
  - Plugin count shown in output header
  - Public helper API for plugin authors:
    - `extract_python_code(story_data)` — extracts all Python from compiled story (imports, `@py:` blocks, expressions, conditions, etc.)
    - `parse_attribute_access(code)` — AST-based extraction of attribute writes, reads, and method calls
    - `LintReport`, `Severity`, `Diagnostic` — all importable for building custom diagnostics
  - Documentation: `docs/lint-plugins.md`

- **`linter/` directory in project templates** — `bardic init` now creates a `linter/` directory with an example plugin (`check_example.py`) in all templates (nicegui, web, reflex). The example demonstrates the plugin API and suggests real use cases.

### Changed

- `bardic init` output now includes a tip about `bardic lint` and the `linter/` directory
- `bardic lint --help` documents the plugin system and all diagnostic codes including P000

### Fixed

- **Indented `@py:` blocks not analyzed** — Python code inside `@py:` blocks within `@if` branches retains its indentation in compiled output. `ast.parse` rejects leading whitespace, so these code blocks were silently skipped during attribute analysis. Now uses `textwrap.dedent()` before parsing, catching all writes regardless of nesting depth.
- **Top-level imports not extracted** — compiled story JSON stores `from X import Y` statements in a separate `imports` array, not inside passage execute blocks. The Python code extractor now includes these, enabling class-aware checking and more complete attribute tracking.

## [0.7.1] - 2026-03-11

### Added

- **Unknown directive detection** — lines starting with `@` that don't match any known directive now raise a `SyntaxError` instead of being silently treated as content text. Common typos like `@elseif`, `@iff`, `@python` get "Did you mean?" suggestions; completely unknown directives list all valid options. 5 new error handling tests.
- **Passage visit counting (`_visits`)** — built-in `_visits` dict tracks how many times each passage has been entered. Use `{_visits.get("Tavern", 0)}` in expressions or `{_visits["Start"] >= 2}` in conditions for "you've been here before" content. Automatically included in undo/redo snapshots and save/load.
- **Turn counter (`_turns`)** — built-in `_turns` integer counts player choices (incremented by `choose()`, not `goto()`). Use for pacing (`{_turns}` turns elapsed), urgency mechanics, scoring, or conditional content that unlocks after N choices. 17 new tests for both features.
- **Quest tracking module (`bardic.stdlib.quest`)** — new stdlib module with `QuestJournal` and `Quest` classes. Track objectives with custom stages, completion/failure, and narrative journal entries. Filtered views (`active_quests`, `completed_quests`), full save/load serialization. 32 new tests.
- **Stdlib test suite** — 114 tests covering all 5 stdlib modules (dice, inventory, economy, relationship, quest). Previously zero stdlib test coverage.

### Changed

- **Python version requirement updated to 3.10+** — codebase uses `X | Y` union syntax (3.10+) and lowercase generic types (3.9+); updated `pyproject.toml`, CLAUDE.md, and all tutorials to reflect the real minimum

### Fixed

- **Callables corrupted on save/load** — functions and other callables (e.g., `create_session`, `get_artifact`, `random`) in engine state were falling through to `__dict__`-based serialization, getting saved as dicts. On load, they couldn't be restored as callables, causing `TypeError: 'dict' object is not callable` when the story tried to call them. Now skipped during serialization alongside classes/types.
- **Tutorial 03_5 wrong import paths** — 6 occurrences of `bardic.modules.*` replaced with `bardic.stdlib.*`
- **Tutorial 04 fake engine API** — `GameUI` class rewritten to use actual `BardCompiler`/`BardEngine` API (`compile_string`, `goto`, `submit_inputs`, `choose`) instead of nonexistent methods (`load_story`, `start`, `set_input`, `continue_story`)
- **Tutorial 00b fake engine API** — test example rewritten to use `BardCompiler.compile_string()` + `BardEngine(story_data)` instead of nonexistent `BardEngine()` no-arg constructor and `load_story_file()`
- **Cookbook legacy syntax** — replaced `<<if>>`/`<<for>>` with `@if:`/`@for:` in `custom-classes.md` for consistency with tutorials
- **Stdlib docstring import paths** — `inventory.py` and `economy.py` docstrings referenced `bardic.modules.*` instead of `bardic.stdlib.*`
- **Tutorial 04 non-functional `@start`** — removed standalone `@start` directive that was parsed as content text, not a directive
- **Relationship.name never assigned** — `__init__` had a type annotation (`self.name: str`) instead of an assignment (`self.name = name`), causing `AttributeError` when accessing any relationship's name
- **One-time choice IDs unstable** — filtering used raw content arrays while tracking used rendered strings, so one-time choices (`*`) would reappear on revisit
- **Circular include detection broken** — `resolve_includes` passed `seen.copy()` to recursive calls, giving each branch its own independent set and failing to detect A→B→A cycles
- **Loop exception handler returned 2-tuple** — `_render_loop` error path returned `(error_msg, None)` instead of the expected `(error_msg, None, [])`, causing unpacking errors
- **Coffee shop example wrong property** — used `alex.is_ready_for_deep_work` instead of `alex.is_ready_for_deep_conversation`

## [0.7.0] - 2026-01-12

### Added

- **@prev Target** - Navigate back to the previous passage
  - Use `-> @prev` in jumps or `+ [Go back] -> @prev` in choices
  - Tracks the immediately previous passage (not decision points like undo)
  - Perfect for menus, inventory screens, side conversations, shop interfaces
  - Works with automatic jumps: in chain `A -> B -> C`, @prev from C goes to B
  - Persists through save/load (`previous_passage_id` in save data)
  - Included in `GameSnapshot` for correct undo/redo behavior
  - Clear error message if used at story start (no previous passage exists)
  - `@prev` added to reserved targets alongside `@join`
  - pytest tests: `tests/test_prev_target.py` (11 tests)

## [0.6.1] - 2025-12-31

### Fixed

- Updated CLI output symbols to not throw errors on windows machines for vscode extension compiling messages.

## [0.6.0] - 2025-12-27

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
