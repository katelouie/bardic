# Custom Python Classes in Bardic

This guide shows you how to create and use custom Python classes in your Bardic stories, with automatic save/load support.

## Why Use Custom Classes?

Custom classes let you create rich, reusable game objects with their own data and behavior:

- **Tarot reading app**: `Card`, `Spread`, `Reading` classes
- **RPG game**: `Character`, `Item`, `Quest` classes
- **Inventory system**: `Item`, `Container`, `Recipe` classes
- **Any complex game logic**: Encapsulate data and behavior together

## Quick Start: Simple Classes

The easiest way to use custom classes is to create simple data classes. They work automatically with Bardic's save/load system - **no special setup required**.

### 1. Create a Python File

Create a `.py` file in your project directory:

```python
# game_logic/tarot.py

class Card:
    """A tarot card."""

    def __init__(self, name, number, is_reversed=False):
        self.name = name
        self.number = number
        self.is_reversed = is_reversed

    def flip(self):
        """Reverse the card."""
        self.is_reversed = not self.is_reversed

    def meaning(self):
        """Get the card's meaning."""
        if self.is_reversed:
            return f"{self.name} (Reversed): Blocked energy, delays"
        return f"{self.name}: New beginnings, potential"
```

### 2. Import in Your .bard Story

```bard
from game_logic.tarot import Card

:: Start
~ card = Card("The Fool", 0)
~ card.flip()

You draw: {card.name}
Number: {card.number}
Reversed: {card.is_reversed}
Meaning: {card.meaning()}

+ [Continue] -> Next
```

### 3. It Just Works! ✨

That's it! Your `Card` objects will automatically:
- ✅ Be usable in your story
- ✅ Serialize correctly when saving
- ✅ Deserialize correctly when loading
- ✅ Maintain their methods and data

**No custom serialization code needed for simple classes.**

---

## How It Works: Auto-Serialization

Bardic automatically saves and loads simple classes by:

1. **On Save**: Converting object attributes to a dictionary
   ```python
   card = Card("The Fool", 0, True)
   # Saves as: {"_type": "Card", "_data": {"name": "The Fool", "number": 0, "is_reversed": True}}
   ```

2. **On Load**: Reconstructing the object from the dictionary
   ```python
   # Loads back as: Card instance with all attributes restored
   ```

**Requirements for auto-serialization:**
- Class must have a `__dict__` (most classes do by default)
- Attributes should be JSON-serializable types (strings, numbers, lists, other custom classes)
- No special `__slots__` or complex metaclasses

---

## Working with Collections

Custom classes work inside lists, dicts, and nested structures:

```python
# game_logic/tarot.py

class Spread:
    """A collection of cards in a reading."""

    def __init__(self, name, cards=None):
        self.name = name
        self.cards = cards or []  # List of Card objects

    def add_card(self, card):
        self.cards.append(card)

    def card_count(self):
        return len(self.cards)
```

```bard
from game_logic.tarot import Card, Spread

:: Start
~ spread = Spread("Three Card Reading")
~ spread.add_card(Card("The Fool", 0))
~ spread.add_card(Card("The Magician", 1))
~ spread.add_card(Card("The High Priestess", 2))

Your {spread.name}:
Cards drawn: {spread.card_count()}

<<for card in spread.cards>>
  - {card.name} (#{card.number})
<<endfor>>
```

**This works automatically!** Bardic's serialization recursively handles:
- Lists of objects
- Objects with list attributes
- Objects containing other objects
- Dictionaries with object values

---

## Advanced: Custom Serialization

For classes with validation, computed properties, or complex initialization, you can implement custom serialization methods.

### When You Need Custom Serialization

**Simple class (auto-serialization works)**:
```python
class Card:
    def __init__(self, name, number):
        self.name = name
        self.number = number
```

**Complex class (needs custom serialization)**:
```python
class Card:
    def __init__(self, name, number):
        if number < 0 or number > 21:
            raise ValueError("Invalid card number")  # Validation!
        self.name = name
        self.number = number
        self._cached_meaning = None  # Private attribute

    @property
    def meaning(self):  # Computed property!
        if self._cached_meaning is None:
            self._cached_meaning = self._calculate_meaning()
        return self._cached_meaning
```

### Implementing Custom Serialization

Add two methods to your class:

```python
class Card:
    def __init__(self, name, number, is_reversed=False):
        if number < 0 or number > 21:
            raise ValueError(f"Card number must be 0-21, got {number}")
        self.name = name
        self.number = number
        self.is_reversed = is_reversed

    def to_save_dict(self):
        """Serialize for saving.

        Return a JSON-serializable dictionary with only the data
        needed to reconstruct this object.
        """
        return {
            "name": self.name,
            "number": self.number,
            "is_reversed": self.is_reversed
        }

    @classmethod
    def from_save_dict(cls, data):
        """Deserialize from saved data.

        Takes the dictionary from to_save_dict() and reconstructs
        the object. This goes through __init__, so validation runs!
        """
        return cls(
            name=data["name"],
            number=data["number"],
            is_reversed=data.get("is_reversed", False)  # Default for old saves
        )
```

### Benefits of Custom Serialization

1. **Validation runs on load**: Goes through `__init__`, so your validation logic works
2. **Control over what gets saved**: Don't save cached/computed values
3. **Version migration**: Handle old save formats gracefully
4. **Explicit is better than implicit**: You know exactly what's being saved

**Example with version migration**:
```python
@classmethod
def from_save_dict(cls, data):
    """Handle both old and new save formats."""
    # Old format: just had "name"
    if "number" not in data:
        # Migrate old saves: infer number from name
        number = CARD_NAMES.index(data["name"])
        return cls(name=data["name"], number=number)

    # New format: has name and number
    return cls(
        name=data["name"],
        number=data["number"],
        is_reversed=data.get("is_reversed", False)
    )
```

---

## Complete Example: RPG Character System

Here's a complete example showing both simple and custom serialization:

```python
# game_logic/rpg.py

class Item:
    """Simple item class - uses auto-serialization."""

    def __init__(self, name, value, weight):
        self.name = name
        self.value = value
        self.weight = weight

class Character:
    """Complex character class - uses custom serialization."""

    MAX_HEALTH = 100

    def __init__(self, name, health=MAX_HEALTH):
        if health < 0 or health > self.MAX_HEALTH:
            raise ValueError(f"Health must be 0-{self.MAX_HEALTH}")

        self.name = name
        self.health = health
        self.inventory = []  # List of Item objects
        self._level = 1  # Private attribute - don't save

    def take_damage(self, amount):
        """Reduce health."""
        self.health = max(0, self.health - amount)

    def add_item(self, item):
        """Add item to inventory."""
        self.inventory.append(item)

    @property
    def is_alive(self):
        """Computed property - don't save, calculate on demand."""
        return self.health > 0

    def to_save_dict(self):
        """Save only essential data."""
        return {
            "name": self.name,
            "health": self.health,
            "inventory": [item for item in self.inventory]  # Will auto-serialize
        }

    @classmethod
    def from_save_dict(cls, data):
        """Reconstruct character from saved data."""
        character = cls(
            name=data["name"],
            health=data.get("health", cls.MAX_HEALTH)  # Default for old saves
        )
        # Inventory auto-deserializes (list of Item objects)
        character.inventory = data.get("inventory", [])
        return character
```

Using it in a story:

```bard
from game_logic.rpg import Character, Item

:: Start
~ hero = Character("Aria")
~ hero.add_item(Item("Sword", 100, 5))
~ hero.add_item(Item("Potion", 50, 1))

Character: {hero.name}
Health: {hero.health}/{Character.MAX_HEALTH}
Inventory: {len(hero.inventory)} items

+ [Fight dragon] -> Combat
+ [Check inventory] -> Inventory

:: Combat
~ hero.take_damage(30)

The dragon breathes fire! You take 30 damage.
Health: {hero.health}/{Character.MAX_HEALTH}

<<if hero.is_alive>>
  You survived!
  + [Continue] -> Victory
<<else>>
  You died!
  + [Restart] -> Start
<<endif>>

:: Inventory
Your inventory:
<<for item in hero.inventory>>
  - {item.name} (worth {item.value} gold, weighs {item.weight} kg)
<<endfor>>

+ [Back] -> Start
```

---

## Import System

### Basic Import

```bard
from game_logic.tarot import Card
```

This imports `Card` and makes it available throughout your story.

### Multiple Imports

```bard
from game_logic.tarot import Card, Spread, Reading
from game_logic.rpg import Character, Item
```

### Auto-Registration

Classes are **automatically registered** for save/load when imported:

```
Auto-registered class for serialization: Card
Auto-registered class for serialization: Spread
Auto-registered class for serialization: Character
```

You'll see these messages when your story loads. This ensures your custom classes work with the save/load system.

---

## Best Practices

### ✅ DO: Keep Classes Simple

```python
class Card:
    def __init__(self, name, rank):
        self.name = name
        self.rank = rank
```

Simple classes work automatically and are easy to maintain.

### ✅ DO: Use Methods for Behavior

```python
class Character:
    def __init__(self, name, health):
        self.name = name
        self.health = health

    def take_damage(self, amount):
        self.health -= amount

    def is_alive(self):
        return self.health > 0
```

Encapsulate game logic in methods that can be called from your story.

### ✅ DO: Document What Gets Saved

```python
class Character:
    def to_save_dict(self):
        """Save only: name, health, inventory.

        Don't save: _cached_stats (recomputed on load)
        """
        return {
            "name": self.name,
            "health": self.health,
            "inventory": self.inventory
        }
```

Make it clear what persists between saves.

### ✅ DO: Provide Defaults for Old Saves

```python
@classmethod
def from_save_dict(cls, data):
    return cls(
        name=data["name"],
        health=data.get("health", 100),  # Default if missing
        mana=data.get("mana", 50)  # New field, default for old saves
    )
```

This lets you add new fields without breaking old save files.

### ⚠️ AVOID: Saving Computed Values

```python
# ❌ Bad: saving computed value
class Character:
    def to_save_dict(self):
        return {
            "name": self.name,
            "health": self.health,
            "max_damage": self.calculate_max_damage()  # Don't save this!
        }

# ✅ Good: compute on demand
class Character:
    def to_save_dict(self):
        return {
            "name": self.name,
            "health": self.health
        }

    def max_damage(self):
        return self.strength * 2  # Compute when needed
```

### ⚠️ AVOID: External Dependencies in Constructors

```python
# ❌ Bad: requires external resource
class Character:
    def __init__(self, name):
        self.name = name
        self.sprite = load_image(f"sprites/{name}.png")  # Won't work on load!

# ✅ Good: lazy loading
class Character:
    def __init__(self, name):
        self.name = name
        self._sprite = None

    def get_sprite(self):
        if self._sprite is None:
            self._sprite = load_image(f"sprites/{self.name}.png")
        return self._sprite
```

---

## Troubleshooting

### "Class 'X' not in context, keeping as dict"

**Problem**: Your class isn't being recognized on load.

**Solution**: Make sure the class is imported in your .bard file:
```bard
from game_logic.mymodule import MyClass
```

Classes must be imported to be auto-registered for save/load.

### "Custom deserialization failed"

**Problem**: Your `from_save_dict()` method has an error.

**Solution**: Check that:
1. You're returning a proper instance: `return cls(...)`
2. All required fields are in the data dict
3. You provide defaults for optional fields: `data.get("field", default_value)`

### Objects load but lose their methods

**Problem**: Objects are loading as plain dictionaries.

**Solution**: This happens when the class isn't imported. Add the import to your .bard file:
```bard
from game_logic.mymodule import MyClass
```

### "Failed to deserialize X"

**Problem**: The automatic deserialization encountered an error.

**Solution**: The class likely needs custom serialization. Implement `to_save_dict()` and `from_save_dict()` methods.

---

## Progressive Disclosure Summary

**Level 1: Just Works**
```python
class Card:
    def __init__(self, name):
        self.name = name
```
→ Auto-serialization handles everything

**Level 2: Add Behavior**
```python
class Card:
    def __init__(self, name):
        self.name = name

    def flip(self):
        self.is_reversed = not self.is_reversed
```
→ Still auto-serialization, now with methods

**Level 3: Custom Serialization**
```python
class Card:
    def __init__(self, name):
        if not name:
            raise ValueError("Name required")
        self.name = name

    def to_save_dict(self):
        return {"name": self.name}

    @classmethod
    def from_save_dict(cls, data):
        return cls(data["name"])
```
→ Full control over save/load

Start simple. Add complexity only when needed.

---

## See Also

- [Engine API Reference](../engine-api.md) - How the runtime engine works
- [Bard Language Spec](../../spec.md) - Full language syntax reference
