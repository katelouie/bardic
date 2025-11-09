# Test Fixtures

This directory contains Python modules that test `.bard` stories can import.

## Purpose

Bardic stories can import custom Python classes and modules. To test this functionality, we need example modules that test stories can use. These modules are **fixtures** - test data that makes our tests work.

## Structure

```
tests/fixtures/
├── __init__.py
└── game_logic/
    ├── __init__.py
    └── test_tarot_objects.py  # Card, Client, Reader classes + draw_cards()
```

## How It Works

1. **Path Setup**: `tests/conftest.py` adds `tests/fixtures/` to `sys.path`
2. **Imports Work**: Test stories can do `from game_logic.test_tarot_objects import Card`
3. **Tests Pass**: Stories compile and run using these fixture modules

## Available Modules

### `game_logic.test_tarot_objects`

Classes and functions for testing object-oriented Bardic stories:

- **`Card`** - A tarot card with name, suit, position, reversal
  - `Card(name, number, reversed)`
  - `.in_position(position)` - Set card position
  - `.is_major_arcana()` - Check if major arcana
  - `.get_display_name()` - Name with reversal status
  - `.get_position_meaning()` - Interpretation text

- **`Client`** - A client receiving a reading
  - `Client(name, age)`
  - `.modify_trust(amount)` - Change trust level
  - `.add_card_seen(card)` - Track cards shown
  - `.get_trust_description()` - Text based on trust

- **`Reader`** - A tarot reader with experience
  - `Reader(name)`
  - `.add_experience(amount)` - Gain experience
  - `.get_level()` - Current level (100 exp/level)

- **`draw_cards(count)`** - Draw random cards from deck

## Test Stories Using Fixtures

- `stories/test/test_loop_objects.bard` - Loop through cards
- `stories/test/test_full_reading.bard` - Complete reading with Reader/Client
- `stories/test/test_conditional_objects.bard` - Conditionals with objects
- `stories/test/test_render_directives.bard` - @render with Card objects
- `stories/test/test_render_demo.bard` - Render directive demo

## Adding New Fixtures

To add new test modules:

1. Create the module in `tests/fixtures/your_module/`
2. Add `__init__.py` files
3. Update test stories to import from your module
4. No code changes needed - conftest.py auto-adds to path

## Why Not in Main Source?

These are **test-only** classes. They're simplified examples for testing Bardic's Python integration. Real games should define their own classes in their own project directories.
