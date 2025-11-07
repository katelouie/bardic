# Standard Library Modules for Bardic Games

Reusable game logic modules for common patterns in interactive fiction.

## Available Modules

- `relationship.py` - Trust, comfort, openness tracking for NPCs
- `dice.py` - Dice rolls, skill checks, weighted choices
- `inventory.py` - Item management with weight/categories (coming)
- `economy.py` - Currency, shops, bartering (coming)

## Usage

```python
# In your .bard story
from bardic.stdlib.relationship import Relationship
from bardic.stdlib.dice import roll, skill_check

# Then use in @py: blocks or ~ lines
```

## Installation

These modules are included with Bardic. No extra installation needed.
