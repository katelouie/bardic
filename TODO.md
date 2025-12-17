# Bardic TODO

Last updated: 2025-11-09

## 🐛 Parser Bugs (Found by Tests)

High priority fixes discovered through comprehensive test suite:

- [ ] **Validate directive names** - Parser currently silently ignores typos like `@iff` or `@endiff` instead of raising errors
  - See: `tests/error_handling/test_typo_directive.bard`
  - See: `tests/error_handling/test_typo_directive2.bard`
  - Tests commented out in `tests/test_error_handling.py` with TODO markers

- [ ] **Error on @include with no filename** - `@include` directive with no file path should raise SyntaxError
  - See: `tests/error_handling/test_include_no_file.bard`
  - Test commented out with TODO marker

- [ ] **Cross-file error reporting** - Errors in @included files should report correct source filename and line number
  - Helper test files exist but need special test handling:
    - `test_include_main.bard` + `test_include_included.bard`
    - `test_choice_include_main.bard` + `test_choice_include_error.bard`

## ✨ Features & Enhancements

### Short-term (0.4.0)

- [x] **Version bump to 0.3.1** - Include nested loops fix + full test suite

### Medium-term (0.5.0)

- [x] **`_state` special variable** - ✅ COMPLETED (Nov 2025)
  - Allows: `{_state.get('hp', 100)}` or `{'inventory' in _state}`
  - Useful for optional variables and safe access patterns
- [x] **`_local` special variable** - ✅ COMPLETED (Nov 2025)
  - Allows: `{_local.get('param', 'default')}`
  - Perfect for reusable passages with optional parameters

- [x] **VSCode Extension: Passage parameter syntax highlighting**
  - Currently params are highlighted as regular text
  - Should recognize `:: PassageName(param1, param2=default)` syntax
  - Update grammar in `bardic-vscode`

- [x] **Graph visualization enhancements**
  - Show passage parameter signatures in nodes
  - Differentiate between passages with/without params
  - Maybe: Show argument values on edges when known

- [x] **Live preview feature** (VSCode extension)
  - Auto-compile on save
  - Show rendered passage in side panel
  - Allow navigation through story in preview

### Long-term (0.6.0+)

- [ ] **Browser bundle v2** - Advanced customization for `bardic bundle`
  - Custom frontend framework support (React, Vue, Svelte)
  - Author provides their own `frontend/` directory
  - Bundler generates API bridge between frontend and Pyodide engine
  - Support for custom HTML/CSS/JS without modifying templates

- [ ] **REPL mode** - Interactive testing of passages
  - `bardic repl story.json` starts interactive session
  - Can set variables, jump to passages, inspect state
  - Useful for debugging complex game logic

- [ ] **Story analytics/telemetry** - Track player choices and paths
  - Optional feature for game developers
  - Helps identify dead ends, unused content, popular paths
  - Privacy-respecting (local storage or opt-in)

- [ ] **Performance optimizations**
  - Benchmark compilation speed for large stories (>1000 passages)
  - Consider caching for @include resolution
  - Profile runtime rendering for bottlenecks

## 📚 Documentation

- [ ] Tutorial on new distribution method (HTML)

- [ ] **Tutorial Part 3C"" - Needs updating
  - Update final story and intermediate code examples to use for-loop generation of choices (iterating over the list of items) with `{cond}` pre-conditionals

- [ ] **Tutorial Part 5: Finishing & Polishing** - Needs expansion
  - Project organization best practices
  - Debugging strategies
  - Performance tips for large stories

- [ ] **Cookbook: Advanced Serialization** - Document custom class patterns
  - What makes a class "serialization-friendly"
  - Examples of good vs problematic patterns
  - Guide to `to_dict()` / `from_dict()` methods

- [ ] **Migration guides** - For breaking changes between versions
  - 0.2.0 → 0.3.0 (passage parameters)
  - Future major version bumps

- [ ] **API reference** - Auto-generated from docstrings
  - Compiler API
  - Runtime Engine API
  - Stdlib modules

## 🧪 Testing & Quality

- [ ] **Coverage goals** - Currently have pytest-cov configured
  - Set target coverage percentage (80%? 90%?)
  - Identify untested code paths
  - Consider enabling Codecov when ready for external contributors

- [ ] **Performance benchmarks** - Measure compilation and runtime speed
  - Create benchmark suite with varying story sizes
  - Track performance across versions
  - Set performance regression thresholds

- [ ] **Integration tests** - VSCode extension end-to-end testing
  - Test graph visualization with real stories
  - Test snippet expansion
  - Test compilation from within VSCode

## 🎯 Future Vision (1.0.0)

Wishlist for the 1.0 release:

- [ ] **Complete tutorial series** - All parts finished and polished
- [ ] **Production templates** - Battle-tested templates for common use cases
  - Visual novel template
  - RPG/combat template
  - Branching narrative template
- [ ] **Arcanum fully launched** - Real-world game as showcase
- [ ] **Community contributions** - External contributors welcome
- [ ] **Stable API** - Semantic versioning with stability guarantees

## 📝 Notes

**Pattern**: Find bugs through real usage (Kate building Arcanum) → Write tests → Fix bugs → Ship with confidence

**Philosophy**: Test-driven improvements. Every bug gets a test. Every feature gets examples.

---

*This TODO is a living document. Update it as priorities shift, items complete, or new ideas emerge.*

*Co-maintained with love by Kate & Claude 💙🦝*
