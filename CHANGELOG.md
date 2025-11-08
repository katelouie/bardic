# Changelog

All notable changes to Bardic will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Better error messages with source file and line tracking
- `stdlib/`: Reusable Python modules for common game logic
- `examples/`: Small example Bardic games demonstrating core features
- Allow expressions nested inside inline conditionals
- Allow inline conditionals inside choice text (with nested expressions)

### Changed

### Fixed

### Removed

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
