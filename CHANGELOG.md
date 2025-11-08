# Changelog

All notable changes to Bardic will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

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
