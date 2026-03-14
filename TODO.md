# Bardic TODO

Last updated: 2026-03-12 (v0.9.0)

---

## Recently Completed (for reference)

<details>
<summary>Click to expand completed items</summary>

### Engine & Architecture
- [x] **Modular engine architecture** (v0.9.0) — 2,153-line god class → 8 focused modules (engine, renderer, executor, state, directives, browser, types, hooks)
- [x] **Browser engine fork eliminated** (v0.9.0) — deleted 3,906 lines of forked code, one engine with `environment` parameter
- [x] **`environment` parameter** (v0.9.0) — `BardEngine(story_data, environment="browser")` for browser deployment
- [x] **BrowserStorageAdapter** (v0.9.0) — localStorage save/load in `bardic.runtime.browser`
- [x] **Undo/redo restore uses in-place mutation** (v0.9.0) — fixes stale references in subsystems
- [x] **149 new subsystem tests** (v0.9.0) — 529 total tests

### Linter
- [x] **`bardic lint` command** (v0.8.0) — structural analysis, class-aware attribute checking, plugin system
- [x] **Level 2 class-aware checking** (v0.8.0) — AST parsing of imported Python classes
- [x] **Lint plugin system** (v0.8.0) — `linter/` directory with auto-discovery
- [x] **Word count + play time estimate** (v0.9.0)

### Features
- [x] **@join directive** (v0.6.0) — inline choice blocks with merge points
- [x] **Hooks system** (v0.6.0) — @hook/@unhook, turn_end event, undo/redo aware
- [x] **Undo/redo** (v0.6.0) — GameSnapshot, configurable depth (default 50)
- [x] **@prev target** (v0.7.0) — navigate back to previous passage
- [x] **Visit counting** (v0.7.1) — `_visits` dict, survives save/load
- [x] **Turn counter** (v0.7.1) — `_turns` int, incremented by `choose()`
- [x] **Unknown directive detection** (v0.7.1) — "Did you mean?" suggestions
- [x] **Quest stdlib module** (v0.7.1) — QuestJournal, Quest dataclass, serialization
- [x] **Stdlib test suite** (v0.7.1) — 114 tests across 5 modules
- [x] **`_state` and `_local` special variables** (v0.5.0)
- [x] **`hasattr`, `getattr`, `map`, `filter` in builtins** (v0.9.0)

### Tooling & Docs
- [x] **CI/CD** (v0.4.0) — GitHub Actions for tests + publish
- [x] **pytest migration** — all tests use pytest
- [x] **VSCode extension** — syntax highlighting, graph visualization, live preview, state injection
- [x] **Spec.md cleanup** (Mar 2026) — 4,248→2,620 lines
- [x] **Tutorial accuracy audit** (Mar 2026) — all 9 issues fixed
- [x] **Validate directive names** (v0.7.1)

### Bug Fixes (v0.7.1)
- [x] Relationship.name never assigned
- [x] Coffee shop example wrong property
- [x] Circular include detection broken
- [x] Loop exception tuple mismatch
- [x] One-time choice ID instability
- [x] Callables corrupted on save/load

</details>

---

## 🐛 Bugs & Parser Issues

- [ ] **Error on @include with no filename** — should raise SyntaxError
- [ ] **Cross-file error reporting** — errors in @included files should report correct source filename and line
- [ ] **Line numbers lost in dedented blocks** — `@if`/`@for` block contents show line 0 in errors
- [ ] **Format specifier parsing is naive** — breaks on dict literals `{{'a': 1}['a']}`, slice notation `{items[1:3]}`. Should use AST analysis instead of string searching
- [ ] **Bracket matching in choice validation** — strings containing `[`/`]` can confuse the parser
- [ ] **No recursion depth limit** — deeply nested `@if`/`@for` hits Python limit with unhelpful traceback

## 🎨 Frontend Template Revamp

The big push: make all templates actually nice out of the box.

### Browser Bundle (`bardic bundle`)

**Layer 1: Asset Pipeline** ✅ (v0.10.0)
- [x] Bundler copies `assets/` directory (images, fonts, audio)
- [x] Bundler copies `custom.css` if present (auto-injected into HTML)
- [x] Bundler copies `custom.js` if present (directive renderers, hooks)
- [x] `--assets-dir` CLI flag for non-standard layouts

**Layer 2: Image & Asset Support** ✅ (v0.10.0)
- [x] Markdown image syntax in content: `![alt](path)` → `<img>` tag
- [x] CSS support for pixel art (`image-rendering: pixelated` via variable)
- [x] Per-passage backgrounds (convention-based via `custom.js`)

**Layer 3: Passage Transitions** ✅ (v0.10.0)
- [x] Fade in/out between passages (subtle, fast, CSS-based)
- [x] Configurable duration via CSS variables

**Layer 4: Sidebar & Panels** ✅ (v0.10.0)
- [x] Collapsible sidebar with toggle button
- [x] `Bardic.sidebar()` hook for game authors
- [x] Sidebar updates after each passage render

**Layer 5: Render Directive Support** ✅ (v0.10.0)
- [x] Extract `render_directives` from engine output in `renderPassage()`
- [x] `Bardic.directive()` registry (built-in + custom via `custom.js`)
- [x] Built-in renderers: image, html, text_block, sidebar, modal
- [x] Fallback display for unhandled directives (dev mode)

**Layer 6: Modal System** ✅ (v0.10.0)
- [x] Reusable modal overlay (for book views, inventory, card detail, settings)
- [x] Close on overlay click or Escape
- [ ] Settings menu (text size, fullscreen)

**Layer 7: Author Customization Hooks** ✅ (v0.10.0)
- [x] `Bardic.on('passageRender', fn)` callback
- [x] `Bardic.on('beforeChoice', fn)` callback
- [x] `Bardic.on('start', fn)` callback
- [x] `Bardic.backgrounds(mapping)` per-passage backgrounds

### NiceGUI Template (`bardic init nicegui`)
- [ ] Add undo/redo buttons
- [ ] Improve layout and styling
- [ ] Add save/load UI

### Reflex Template (`bardic init reflex`) — needs major overhaul
- [ ] Switch from raw JSON reading to `BardEngine` (currently bypasses the engine entirely)
- [ ] Use `rx.markdown()` instead of `rx.text()` for content (enables images, bold, italic, links)
- [ ] Add undo/redo buttons
- [ ] Add save/load UI
- [ ] Add conditional choice support (currently no choice filtering)
- [ ] Add variable assignment / `@py:` block support (currently no execution)
- [ ] Improve layout and styling (currently minimal card layout)

### React/Web Template (`bardic init web`)
- [ ] Add undo/redo buttons
- [ ] Improve layout and styling
- [ ] Add save/load UI

### CLI Player (`bardic play`)
- [ ] Add undo/redo keyboard shortcuts

## ✨ Language Features

### High Priority — Closing Gaps with Ink/Twine

- [ ] **Text variation / sequences** — Ink's killer feature for revisitable passages
  - `{stopping: "First visit" | "Second visit" | "Regular visit"}`
  - Modes: stopping, cycle, shuffle, once
  - Requires per-passage sequence position tracking in state

- [ ] **Fallback choices** — auto-navigate when all visible choices exhausted
  - `+ -> Target` syntax (choice with no text = fallback)
  - Prevents dead ends from one-time choice exhaustion

- [ ] **Inline image syntax** — `![alt](path)` in passage content
  - Parser emits `{"type": "image", "alt": "...", "src": "..."}`
  - Terminal shows `[Image: alt]`, web shows `<img>`

- [ ] **Passage tag styling** — expose tags in PassageOutput for frontend CSS
  - `:: DarkForest ^dark ^scary` → `tags: ["dark", "scary"]` in output
  - Frontend applies `.tag-dark .tag-scary` CSS classes
  - Zero engine changes needed

### Medium Priority

- [ ] **Tunnels (call/return)** — `-> passage ->` goes there and comes back
  - Requires a call stack in the engine
  - `->->` returns to caller
  - Architecturally like function calls

- [ ] **Audio directives** — `@audio play background music=path loop=true`
  - Render directive that frontend handles
  - Play, stop, volume control

- [ ] **Macro/widget system** — reusable story patterns
  - `@macro say(character, text)` ... `@endmacro`
  - `@say("Barkeep", "What'll it be?")`
  - Reduces repetition in dialogue-heavy games

- [ ] **Repeatable menus** — reusable choice blocks across passages

### Nice to Have

- [ ] **Reactive state bindings** — `bindings:` in metadata, auto-included in PassageOutput
  - Frontend auto-updates UI elements without custom code per variable

- [ ] **`@fetch` directive** — server-side data injection
  - Calls a Python function registered in context, stores result in state
  - Transforms bardic from IF engine to narrative application framework

- [ ] **`@generate` directive** — AI-augmented content
  - Prompt template with story state variables → LLM → cached result
  - `--no-ai` flag for offline play with placeholder text

## 🔧 Linter Enhancements (`bardic lint`)

- [ ] **Passage-level context in diagnostics** — report *where* issues occur, not just *what*
- [ ] **`--fix` mode** — auto-fix unambiguous issues (typos with close matches)
- [ ] **Write-but-never-read detection** — complement to W005, finds dead state

## 🛠️ CLI & Tooling

- [ ] **REPL mode** — `bardic repl story.json` for interactive testing
  - Set variables, jump to passages, inspect state
- [ ] **`bardic play --debug`** — state inspector, mutation log, goto command
- [ ] **`bardic proofread`** — dump all passage text as continuous prose for editing
- [ ] **Story testing framework** — `bardic.testing.StoryTest` base class
  - `choose("text")`, `assert_passage()`, `assert_state()`, `find_path_to()`
  - Fuzzy path testing (seeded random playthroughs)
  - Integrates with pytest
- [ ] **Story profiler/audit** — dead-end detection, unreachable passages, cycle detection, path counting
- [ ] **`bardic diff old.json new.json`** — semantic story diffing
  - Shows added/removed/modified passages, new branches, changed reachability
- [ ] **Hot-reload for `bardic serve`** — file watcher that recompiles on change
- [ ] **`--verbose` / `--debug` flags** — full stack traces for debugging
- [ ] **Better error messages** — suggestions for common fixes (partially done for directives)

## 🧪 Testing & Quality

- [x] **CLI tests for `compile`** — 12 tests via Click CliRunner (basic, output path, metadata, includes, errors)
- [x] **CLI tests for `lint`** — 13 tests (clean story, W001/E002 diagnostics, JSON output, flags, includes, word count)
- [x] **CLI tests for `init`** — 10 tests (all 4 templates, custom paths, error cases, file creation)
- [x] **CLI tests for `graph`** — 8 CLI tests + 8 `extract_connections()` unit tests (PNG/SVG/PDF, connections, conditionals, loops)
- [ ] **CLI tests for `bundle`** — `create_browser_bundle()`, module detection, theme application
- [ ] **CLI tests for `play`** — interactive input, hard to test with CliRunner
- [ ] **Integration tests** — compile `.bard` → run engine → make choices → verify output
- [ ] **Coverage goals** — set target percentage, identify untested paths
- [ ] **Performance benchmarks** — compilation speed for large stories, runtime rendering profiling

## 📚 Documentation

- [ ] **Docs on new features** — undo/redo, hooks, @join, @prev, visits/turns
- [ ] **Tutorial on browser distribution** — `bardic bundle` workflow
- [ ] **Cookbook: Advanced Serialization** — custom class patterns, `to_dict()`/`from_dict()`
- [ ] **Cookbook: Common Patterns** — visited passages, day/night cycles, inventory management
- [ ] **Stdlib documentation page** — standalone docs (currently only README table + docstrings)
- [ ] **API reference** — auto-generated from docstrings (compiler, engine, stdlib)
- [ ] **Migration guides** — breaking changes between versions

## 🔭 Future Vision

### Embeddable Story Component
- [ ] `<bardic-story>` web component (Custom Element + Shadow DOM)
  - Drop a story into any web page
  - Custom events for state changes, endings, passage transitions
  - Lazy Pyodide loading (show first passage with lightweight JS renderer while Python loads)

### Story Composition / Multi-File Architecture
- [ ] `@export` directive for public passage API
- [ ] Namespace passages: `chapter1.Tavern` vs `chapter2.Tavern`
- [ ] Story packages as pip-installable Python packages

### Multi-Player / Shared World
- [ ] `@shared` / `@publish` directives for shared state channels
- [ ] WebSocket connection for real-time updates via FastAPI backend

### Story Analytics
- [ ] `bardic analytics` — heatmaps, funnels, decision trees, dead content detection
- [ ] Engine emits events (passage_enter, choice_made, session_start)
- [ ] SQLite storage (local) or backend endpoint

### Type-Safe Story Contracts
- [ ] `@requires` / `@ensures` directives for passage contracts
- [ ] Compile-time verification via `bardic check`
- [ ] Story-level type declarations in metadata

### VSCode Extension Enhancements
- [ ] **Error diagnostics (LSP)** — real-time squiggles, hover info, go-to-definition
- [ ] **Passage outline sidebar** — tree view with quick-jump
- [ ] **Enhanced preview** — state diffing, choice condition inspector, navigation breadcrumb

## 🎯 1.0.0 Checklist

- [ ] Complete tutorial series
- [ ] Production-quality templates (browser, NiceGUI, Reflex, React)
- [ ] Arcanum fully launched as showcase
- [ ] Stable API with semver guarantees
- [ ] Community-ready (contributing guide, issue templates)
- [ ] Text variation/sequences implemented
- [ ] Fallback choices implemented
- [ ] Story testing framework

---

**Pattern**: Find bugs through real usage (Arcanum) → Write tests → Fix bugs → Ship with confidence

**Philosophy**: Test-driven improvements. Every bug gets a test. Every feature gets examples.

*This TODO is a living document. Update it as priorities shift, items complete, or new ideas emerge.*
