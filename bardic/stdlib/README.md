# Standard Library Modules for Bardic Games

Reusable game logic modules for common patterns in interactive fiction.

## Available Modules

| Module | What it does |
|--------|-------------|
| **`dice`** | Dice rolls (`3d6+5`), skill checks, advantage/disadvantage |
| **`inventory`** | Weight-limited item management with add/remove/filter |
| **`economy`** | Wallets, shops, buying/selling with automatic refunds |
| **`relationship`** | NPC trust/comfort/openness with threshold events |
| **`quest`** | Quest tracking with custom stages, journal entries, completion |

## Quick Start

```python
# In your .bard story
from bardic.stdlib.dice import roll, skill_check
from bardic.stdlib.inventory import Inventory
from bardic.stdlib.economy import Wallet, Shop
from bardic.stdlib.relationship import Relationship
from bardic.stdlib.quest import QuestJournal
```

These modules are included with Bardic. No extra installation needed.

## Full Documentation

See the **[Standard Library Reference](../../docs/stdlib.md)** for complete API docs, usage examples in `.bard` syntax, and patterns for combining modules.
