# How to Contribute to Bardic

Thank you for your interest in helping with Bardic! As an early-stage project, your contributions—from bug reports to new features—are invaluable.

## How You Can Help

The best way to contribute right now is by using Bardic and letting us know how it goes.

- **Reporting Bugs:** If you find a bug, please [open an issue](https://github.com/katelouie/bardic/issues) and include steps to reproduce it, your OS, and your Python version.
- **Suggesting Features:** Have an idea for the language or the engine? [Open an issue](https://github.com/katelouie/bardic/issues) to start a discussion. We'd love to hear your "why" and "how."
- **Submitting Code:** If you'd like to fix a bug or add a feature, please follow the process below.

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Set up your development environment (see below).
3. Make your changes!
4. Make sure to add or update tests for your changes.
5. Run the tests (**forthcoming**) to ensure everything passes.
6. Submit a pull request with a clear description of your changes.

## Development Setup

### Installing from Source

To set up your local environment for development:

```bash
git clone [https://github.com/katelouie/bardic.git](https://github.com/katelouie/bardic.git)
cd bardic
pip install -e .
```

This will install the project in "editable" mode, so your changes to the source code will be immediately available.

### Running Tests

**Forthcoming.**

## Understanding the Codebase

Here is a high-level overview of the project's design and architecture, as described in the original documentation.

```sh
bardic/
├── bardic/
│   ├── compiler/    # Parser and compiler
│   ├── runtime/     # BardEngine execution
│   ├── cli/         # Command-line interface
│   └── templates/   # Project templates
├── tests/           # Test files
├── docs/            # Documentation
└── stories/         # Example stories
```

### Architecture

Bardic uses a three-layer architecture:

- **Compiler** - Parses `.bard` files to JSON.
- **Runtime** - The `BardEngine` executes compiled stories.
- **UI Layer** - Your choice of interface (NiceGUI, React, etc.).

Stories are compiled to platform-independent JSON that can be run anywhere.

### Security Model

Bardic stories execute in a controlled Python environment:

- Whitelisted builtins only (no `open`, `exec`, `eval`, etc.).
- Controlled namespace (no `globals`/`locals` access).
- Imports are allowed (stories can import Python modules).

Stories are trusted code. Only run `.bard` files you've written or reviewed, just as you'd only run `.py` files you trust.
