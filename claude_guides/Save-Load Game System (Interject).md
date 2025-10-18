Perfect! Let's implement the improved save/load system with auto-registration AND custom serialization support.

<artifact identifier="improved-save-load-implementation" type="text/markdown" title="Improved Save/Load Implementation Guide"> # Improved Save/Load with Auto-Registration - Implementation Guide

**Goal:** Make object serialization robust and automatic.

**Time Estimate:** 20-30 minutes

---

## Part 1: Update Engine (15 minutes)

### Step 1.1: Auto-Register Classes from Imports

**File:** `bardic/runtime/engine.py`

**Find the `_execute_imports()` method and replace it:**

```python
def _execute_imports(self) -> None:
    """
    Execute import statements from the story.
    
    Imports are executed in a temporary namespace and then added to the state,
    making them available to all passages.
    
    NEW: Classes are automatically registered in context for serialization!
    """
    import_statements = self.story.get("imports", [])

    if not import_statements:
        return

    # Join all import statements
    import_code = "\n".join(import_statements)

    if not import_code.strip():
        return

    try:
        # Add current directory to path for imports
        if "." not in sys.path:
            sys.path.insert(0, ".")
        
        # Execute imports with safe builtins
        safe_builtins = self._get_safe_builtins()
        import_namespace = {}

        exec(import_code, {"__builtins__": safe_builtins}, import_namespace)

        # Add imported modules/objects to state AND auto-register classes
        for key, value in import_namespace.items():
            if not key.startswith("_"):
                # Always add to state (for use in stories)
                self.state[key] = value
                
                # NEW: Auto-register classes for serialization!
                if isinstance(value, type):
                    # It's a class - add to context for save/load
                    self.context[key] = value
                    print(f"Auto-registered class for serialization: {key}")
                    
    except ImportError as e:
        raise RuntimeError(
            "Failed to import modules:\n"
            f"{import_code}\n\n"
            f"Error: {e}\n\n"
            "Make sure the modules are installed and accessible"
        )
    except Exception as e:
        raise RuntimeError(f"Error executing imports:\n{import_code}\n\nError: {e}")
```

**What this does:**

- Automatically adds ALL imported classes to `self.context`
- No manual registration needed in `get_game_context()`
- Classes are available for both story use AND serialization

### Step 1.2: Improve `_serialize_value()` with Custom Method Support

**Find the `_serialize_value()` method and replace it:**

```python
def _serialize_value(self, value: Any) -> Any:
    """
    Serialize a single value for JSON storage.
    
    Priority order:
    1. Check for custom to_save_dict() method (explicit serialization)
    2. Try direct JSON serialization (primitives)
    3. Use __dict__ serialization (objects)
    4. Fallback to string representation
    """
    # Priority 1: Custom serialization method
    if hasattr(value, 'to_save_dict') and callable(getattr(value, 'to_save_dict')):
        return {
            "_type": type(value).__name__,
            "_module": type(value).__module__,
            "_data": value.to_save_dict(),
            "_custom": True  # Flag that this used custom serialization
        }
    
    # Priority 2: Direct JSON serialization (primitives)
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        pass
    
    # Priority 3: Object with __dict__
    if hasattr(value, '__dict__'):
        return {
            "_type": type(value).__name__,
            "_module": type(value).__module__,
            "_data": {k: v for k, v in value.__dict__.items() if not k.startswith('_')},
            "_custom": False  # Flag that this used __dict__ serialization
        }
    
    # Priority 4: Fallback to string
    print(f"Warning: Serializing {type(value).__name__} as string representation")
    return {
        "_type": "string_repr",
        "_value": str(value)
    }
```

**What changed:**

- Checks for `to_save_dict()` method FIRST
- Adds `_custom` flag to track serialization method
- Falls back gracefully if no custom method

### Step 1.3: Improve `_deserialize_value()` with Custom Method Support

**Find the `_deserialize_value()` method and replace it:**

```python
def _deserialize_value(self, value: Any) -> Any:
    """
    Deserialize a single value from JSON storage.
    
    Priority order:
    1. Check for custom from_save_dict() classmethod (explicit deserialization)
    2. Use __new__ + __dict__ update (automatic deserialization)
    3. Return as dict if class not available
    """
    # Not a special serialized object - return as-is
    if not isinstance(value, dict) or "_type" not in value:
        return value
    
    obj_type = value["_type"]
    obj_data = value.get("_data", {})
    
    # Special case: string representation
    if obj_type == "string_repr":
        return value.get("_value", "")
    
    # Try to get class from context
    if obj_type not in self.context:
        # Class not available - keep as dict
        print(f"Warning: Class '{obj_type}' not in context, keeping as dict")
        return obj_data
    
    cls = self.context[obj_type]
    
    # Priority 1: Custom deserialization method
    if hasattr(cls, 'from_save_dict') and callable(getattr(cls, 'from_save_dict')):
        try:
            return cls.from_save_dict(obj_data)
        except Exception as e:
            print(f"Warning: Custom deserialization failed for {obj_type}: {e}")
            # Fall through to automatic method
    
    # Priority 2: Automatic deserialization using __new__
    try:
        obj = cls.__new__(cls)
        if hasattr(obj, '__dict__'):
            obj.__dict__.update(obj_data)
        return obj
    except Exception as e:
        print(f"Warning: Failed to deserialize {obj_type}: {e}")
        return obj_data
```

**What changed:**

- Checks for `from_save_dict()` classmethod FIRST
- Falls back to `__new__` if no custom method
- Better error handling and logging

### Step 1.4: Update `_serialize_state()` to Use Improved Methods

**The current `_serialize_state()` calls `_serialize_value()`, but let's make it clearer:**

```python
def _serialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
    """
    Serialize state dictionary for JSON storage.
    
    Handles:
    - Objects with to_save_dict() (custom serialization)
    - Objects with __dict__ (automatic serialization)
    - Lists and collections (recursive)
    - Primitives (direct)
    """
    serialized = {}
    
    for key, value in state.items():
        if isinstance(value, (list, tuple)):
            # Recursively serialize collections
            serialized[key] = [self._serialize_value(v) for v in value]
        else:
            # Serialize single value
            serialized[key] = self._serialize_value(value)
    
    return serialized
```

**What changed:**

- Explicitly handles lists/tuples
- Clearer logic flow

### Step 1.5: Update `_deserialize_state()` Similarly

```python
def _deserialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
    """
    Deserialize state from JSON storage.
    
    Attempts to reconstruct objects using:
    1. Custom from_save_dict() if available
    2. Automatic __new__ + __dict__ update
    3. Fallback to dict if class not found
    """
    deserialized = {}
    
    for key, value in state.items():
        if isinstance(value, list):
            # Recursively deserialize lists
            deserialized[key] = [self._deserialize_value(v) for v in value]
        else:
            # Deserialize single value
            deserialized[key] = self._deserialize_value(value)
    
    return deserialized
```

**✅ Checkpoint 1: Engine now auto-registers classes and supports custom serialization!**

---

## Part 2: Add Custom Serialization to Card Class (5 minutes)

**File:** `game_logic/test_tarot_objects.py` (or wherever your Card class is)

**Add these methods to your Card class:**

```python
class Card:
    """A tarot card."""
    
    def __init__(self, name: str, number: int, is_reversed: bool = False):
        self.name = name
        self.number = number
        self.is_reversed = is_reversed
    
    # NEW: Custom serialization support
    def to_save_dict(self) -> dict:
        """
        Serialize card to a dictionary for saving.
        
        This method is called automatically by the engine when saving.
        You can customize what gets saved here.
        """
        return {
            "name": self.name,
            "number": self.number,
            "is_reversed": self.is_reversed
        }
    
    @classmethod
    def from_save_dict(cls, data: dict) -> "Card":
        """
        Restore a card from saved data.
        
        This method is called automatically by the engine when loading.
        It goes through __init__, so validation runs!
        """
        return cls(
            name=data["name"],
            number=data["number"],
            is_reversed=data.get("is_reversed", False)
        )
    
    # Rest of your Card methods...
    def get_display_name(self) -> str:
        prefix = "↓ " if self.is_reversed else ""
        return f"{prefix}{self.name}"
```

**Benefits:**

- ✅ Goes through `__init__` (validation runs!)
- ✅ Can customize what gets saved
- ✅ Can handle version upgrades (e.g., `data.get("new_field", default)`)
- ✅ Explicit and clear

**✅ Checkpoint 2: Card class has custom serialization!**

---

## Part 3: Test It! (10 minutes)

### Test 1: Auto-Registration Works

**Create:** `test_auto_register.bard`

```bard
from game_logic.test_tarot_objects import Card

:: Start
~ card = Card("The Fool", 0, False)

Card created: {card.name}
Type: {type(card).__name__}

+ [Continue] -> Next

:: Next
Card still works: {card.name}
Display: {card.get_display_name()}
```

**Test in Python:**

```python
from bardic import BardEngine
import json
import sys

# Add path
sys.path.insert(0, '.')

# Compile
from bardic.compiler import BardCompiler
compiler = BardCompiler()

with open('test_auto_register.bard') as f:
    story = compiler.compile_string(f.read())

# Create engine (NO manual context needed!)
engine = BardEngine(story)

print("=== Initial State ===")
print(f"Card in state: {engine.state.get('Card')}")
print(f"Card in context: {engine.context.get('Card')}")
print()

# Navigate
output = engine.current()
print("Initial passage:")
print(output.content)

# Check that card is a Card instance
print(f"\ncard type: {type(engine.state['card'])}")
print(f"card.__class__.__name__: {engine.state['card'].__class__.__name__}")

# Save
print("\n=== Saving ===")
save_data = engine.save_state()
print(f"Saved card structure:")
print(json.dumps(save_data['state']['card'], indent=2))

# Check for custom flag
if save_data['state']['card'].get('_custom'):
    print("✅ Used custom to_save_dict() method!")
else:
    print("⚠️ Used automatic __dict__ serialization")

# Load
print("\n=== Loading ===")
engine2 = BardEngine(story)
engine2.load_state(save_data)

print(f"Restored card type: {type(engine2.state['card'])}")
print(f"Is Card instance: {isinstance(engine2.state['card'], engine2.context['Card'])}")
print(f"Card name: {engine2.state['card'].name}")
print(f"Has method: {hasattr(engine2.state['card'], 'get_display_name')}")

# Try calling method
try:
    display = engine2.state['card'].get_display_name()
    print(f"✅ Method call works: {display}")
except Exception as e:
    print(f"❌ Method call failed: {e}")

# Navigate
engine2.choose(0)
print("\n=== After Navigation ===")
print(engine2.current().content)
```

**Expected Output:**

```
=== Initial State ===
Card in state: <class 'game_logic.test_tarot_objects.Card'>
Card in context: <class 'game_logic.test_tarot_objects.Card'>
Auto-registered class for serialization: Card

Initial passage:
Card created: The Fool
Type: Card

card type: <class 'game_logic.test_tarot_objects.Card'>
card.__class__.__name__: Card

=== Saving ===
Saved card structure:
{
  "_type": "Card",
  "_module": "game_logic.test_tarot_objects",
  "_data": {
    "name": "The Fool",
    "number": 0,
    "is_reversed": false
  },
  "_custom": true
}
✅ Used custom to_save_dict() method!

=== Loading ===
Auto-registered class for serialization: Card
Restored card type: <class 'game_logic.test_tarot_objects.Card'>
Is Card instance: True
Card name: The Fool
Has method: True
✅ Method call works: The Fool

=== After Navigation ===
Card still works: The Fool
Display: The Fool
```

### Test 2: Full Save/Load in Web Runtime

**Create:** `stories/test/test_save_card.bard`

```bard
from game_logic.test_tarot_objects import Card

:: Start
~ deck = [
    Card("The Fool", 0, False),
    Card("The Magician", 1, False),
    Card("The High Priestess", 2, True)
]

**Your Tarot Deck**

You have {len(deck)} cards:

<<for card in deck>>
- {card.get_display_name()}
<<endfor>>

+ [Draw a card] -> Draw

:: Draw
~ drawn = deck[0]
~ deck = deck[1:]

**You draw:** {drawn.get_display_name()}

Reversed: {drawn.is_reversed}
Remaining cards: {len(deck)}

+ [Continue] -> Start
```

**Test it:**

```bash
# Compile
bardic compile stories/test/test_save_card.bard -o compiled_stories/test_save_card.json

# Start server
bardic serve

# In browser:
# 1. Select "Test Save Card"
# 2. Draw a card
# 3. Click "💾 Save Game" → Name it "After drawing Fool"
# 4. Draw another card
# 5. Click "📁 Load Game" → Load "After drawing Fool"
# 6. Check: Should be back with 2 cards, first one drawn!
```

**Check the save file:**

```bash
cat saves/save_*.json | jq '.state.deck'
```

Should show:

```json
[
  {
    "_type": "Card",
    "_module": "game_logic.test_tarot_objects",
    "_data": {
      "name": "The Magician",
      "number": 1,
      "is_reversed": false
    },
    "_custom": true
  },
  {
    "_type": "Card",
    "_module": "game_logic.test_tarot_objects",
    "_data": {
      "name": "The High Priestess",
      "number": 2,
      "is_reversed": true
    },
    "_custom": true
  }
]
```

**✅ Checkpoint 3: Cards serialize and restore perfectly!**

---

## Part 4: Add to Other Classes (Optional, 5 minutes)

If you have other custom classes (like `Client`, `Reading`, etc.), add the same methods:

```python
class Client:
    def __init__(self, name: str, trust: int = 50):
        self.name = name
        self.trust = trust
    
    def to_save_dict(self) -> dict:
        return {
            "name": self.name,
            "trust": self.trust
        }
    
    @classmethod
    def from_save_dict(cls, data: dict) -> "Client":
        return cls(
            name=data["name"],
            trust=data.get("trust", 50)
        )
```

**Note:** Classes without these methods still work (via `__dict__`), but custom methods are more robust!

---

## Part 5: Update Context Provider (Cleanup)

Since auto-registration now handles classes, you can simplify your context:

**File:** `web-runtime/backend/extensions/context.py`

**Before:**

```python
def get_game_context():
    from game_logic.tarot import Card
    from game_logic.client import Client
    
    return {
        "Card": Card,  # Manual registration
        "Client": Client,  # Manual registration
        "random_int": lambda min, max: random.randint(min, max),
    }
```

**After:**

```python
def get_game_context():
    # Classes are now auto-registered from imports!
    # Just provide utility functions here
    return {
        "random_int": lambda min_val, max_val: random.randint(min_val, max_val),
        "random_choice": lambda items: random.choice(items),
        "chance": lambda probability: random.random() < probability,
    }
```

**Much cleaner!** Classes automatically register themselves when imported in stories.

---

## Summary

**What We Built:**

1. **Auto-Registration**
    
    - Classes imported in stories automatically register for serialization
    - No manual context management needed
    - Works transparently
2. **Custom Serialization (Optional)**
    
    - Classes can define `to_save_dict()` / `from_save_dict()`
    - Goes through `__init__` (validation works!)
    - Explicit control over what gets saved
3. **Backwards Compatible**
    
    - Classes without custom methods still work (via `__dict__`)
    - Primitives work as before
    - Old saves still load

**Code Changes:**

- ✅ `_execute_imports()` - Auto-registers classes
- ✅ `_serialize_value()` - Checks for `to_save_dict()`
- ✅ `_deserialize_value()` - Checks for `from_save_dict()`
- ✅ `Card` class - Added custom methods

**Benefits:**

- ✅ Objects restore as actual instances, not dicts
- ✅ Methods work after load
- ✅ `__init__` runs (when using custom methods)
- ✅ Automatic for most cases
- ✅ Customizable when needed

**Ready to save/load complex game state!** 🎉 </artifact>

Perfect! Now you have a robust save/load system that:

1. **Automatically registers** all imported classes
2. **Supports custom serialization** for complex objects
3. **Falls back gracefully** if custom methods aren't present
4. **Goes through `__init__`** when custom methods are used

The key insight is the **priority system**:

```
Priority 1: to_save_dict() / from_save_dict()  ← Explicit control
Priority 2: __dict__ serialization            ← Automatic fallback  
Priority 3: String representation             ← Last resort
```

This means:

- ✅ Simple classes work automatically (no extra code needed)
- ✅ Complex classes can add custom methods for robustness
- ✅ Everything is backwards compatible

Want to implement this now? The changes are pretty straightforward - mainly updating those 4 methods in the engine and optionally adding the two methods to your Card class! 🚀