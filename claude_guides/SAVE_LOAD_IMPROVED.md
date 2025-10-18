# Improved Save/Load with Better Object Serialization

## The Problem

The current implementation uses `__new__` and bypasses `__init__`, which can break objects with:
- Validation in `__init__`
- Computed properties
- `__slots__`
- Custom setters

## Solution 1: Registry Pattern (Recommended)

### Step 1: Add Serialization Protocol

Objects opt-in to custom serialization:

```python
# In game_logic/tarot.py (or wherever Card is defined)

class Card:
    """A tarot card."""
    
    def __init__(self, name: str, is_reversed: bool = False):
        self.name = name
        self.is_reversed = is_reversed
        # Any validation or setup here
    
    def to_save_dict(self) -> dict:
        """Convert to saveable dict."""
        return {
            "name": self.name,
            "is_reversed": self.is_reversed
        }
    
    @classmethod
    def from_save_dict(cls, data: dict) -> "Card":
        """Restore from save dict."""
        return cls(
            name=data["name"],
            is_reversed=data["is_reversed"]
        )
```

### Step 2: Update Engine Serialization

```python
# In bardic/runtime/engine.py

def _serialize_value(self, value: Any) -> Any:
    """Serialize a single value for JSON storage."""
    # Check for custom serialization first
    if hasattr(value, 'to_save_dict'):
        return {
            "_type": type(value).__name__,
            "_module": type(value).__module__,
            "_data": value.to_save_dict()  # Use custom method!
        }
    
    # Try basic JSON serialization
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        # Fallback to __dict__ method
        if hasattr(value, '__dict__'):
            return {
                "_type": type(value).__name__,
                "_module": type(value).__module__,
                "_data": {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
            }
        else:
            return str(value)

def _deserialize_value(self, value: Any) -> Any:
    """Deserialize a single value from JSON storage."""
    if isinstance(value, dict) and "_type" in value:
        obj_type = value["_type"]
        obj_data = value.get("_data", {})
        
        # Try to get class from context
        if obj_type in self.context:
            cls = self.context[obj_type]
            
            # Check for custom deserialization
            if hasattr(cls, 'from_save_dict'):
                return cls.from_save_dict(obj_data)  # Use custom method!
            
            # Fallback to __new__ method
            obj = cls.__new__(cls)
            if hasattr(obj, '__dict__'):
                obj.__dict__.update(obj_data)
            return obj
        else:
            # Class not in context - keep as dict
            return obj_data
    
    return value
```

### Benefits:

✅ Objects control their own serialization
✅ Goes through `__init__` (validation works!)
✅ Works with `__slots__`
✅ Works with properties
✅ Explicit and clear

## Solution 2: Automatic Registration

Make it even easier - auto-detect classes from imports:

```python
# In bardic/runtime/engine.py

def _execute_imports(self) -> None:
    """Execute import statements and auto-register classes."""
    import_statements = self.story.get("imports", [])
    
    if not import_statements:
        return
    
    import_code = "\n".join(import_statements)
    
    if not import_code.strip():
        return
    
    try:
        if "." not in sys.path:
            sys.path.insert(0, ".")
        
        safe_builtins = self._get_safe_builtins()
        import_namespace = {}
        
        exec(import_code, {"__builtins__": safe_builtins}, import_namespace)
        
        # Add imported modules/objects to BOTH state AND context
        for key, value in import_namespace.items():
            if not key.startswith("_"):
                self.state[key] = value
                
                # If it's a class, also add to context for serialization!
                if isinstance(value, type):
                    self.context[key] = value  # ← Auto-register classes!
                    
    except ImportError as e:
        raise RuntimeError(f"Failed to import modules: {e}")
```

Now imports automatically make classes available for deserialization!

## Testing

Create a test to verify object serialization:

```python
# test_save_load.py

from bardic import BardEngine
import json

# Test story with Card object
story_source = """
from game_logic.tarot import Card

:: Start
~ card = Card("The Fool", is_reversed=True)
~ card_name = card.name

You draw: {card.name}
Reversed: {card.is_reversed}

+ [Save and check] -> Next

:: Next
Card is: {type(card).__name__}
Name: {card.name}
"""

# Compile
from bardic.compiler import BardCompiler
compiler = BardCompiler()
story = compiler.compile_string(story_source)

# Create engine
engine = BardEngine(story)

# Navigate
output = engine.current()
print(f"Initial: {output.content}")

# Save
save_data = engine.save_state()
print(f"\nSaved card type: {save_data['state']['card']['_type']}")
print(f"Saved card data: {save_data['state']['card']['_data']}")

# Make a choice
engine.choose(0)

# Load
engine.load_state(save_data)
output = engine.current()

# Check if Card is still a Card object
print(f"\nAfter load: {output.content}")
print(f"card type in state: {type(engine.state['card'])}")
print(f"Is Card instance: {isinstance(engine.state['card'], engine.context['Card'])}")

# Check methods still work
if hasattr(engine.state['card'], 'to_save_dict'):
    print("✅ Card has custom serialization")
else:
    print("❌ Card missing custom serialization")
```

## What You Need to Do

### Option A: Minimal (Current code works mostly)

Just make sure `Card` is in context:

```python
# In web-runtime/backend/extensions/context.py

def get_game_context():
    from game_logic.tarot import Card
    
    return {
        "Card": Card,  # ← This is enough for basic cases
        # ... other stuff
    }
```

**Pros:** No changes to Card class needed
**Cons:** Bypasses `__init__`, might break with complex classes

### Option B: Add Serialization Methods (Recommended)

Add to each custom class:

```python
class Card:
    def to_save_dict(self) -> dict:
        """Serialize for save."""
        return {"name": self.name, "is_reversed": self.is_reversed}
    
    @classmethod
    def from_save_dict(cls, data: dict) -> "Card":
        """Deserialize from save."""
        return cls(data["name"], data["is_reversed"])
```

Update engine with the improved `_serialize_value` and `_deserialize_value` from above.

**Pros:** Explicit, uses `__init__`, works with validation
**Cons:** Requires updating each class

### Option C: Both (Best)

Use Option A as fallback, Option B when available:

The code I showed in Solution 1 already does this!

```python
# Tries custom method first
if hasattr(cls, 'from_save_dict'):
    return cls.from_save_dict(obj_data)

# Falls back to __new__ if no custom method
obj = cls.__new__(cls)
obj.__dict__.update(obj_data)
```

## Quick Test Right Now

Want to test what happens with current code?

```bash
# Create a test
cat > test_card_save.bard << 'EOF'
from game_logic.test_tarot_objects import Card

:: Start
~ card = Card("The Fool", 0, False)

Card name: {card.name}
Card number: {card.number}
Is reversed: {card.is_reversed}

+ [Continue] -> End

:: End
Card still works: {card.name}
EOF

# Compile
bardic compile test_card_save.bard -o test_card_save.json

# Test in Python
python3 << 'PYTHON'
from bardic import BardEngine
import json

with open('test_card_save.json') as f:
    story = json.load(f)

# Must have Card in context!
import sys
sys.path.insert(0, '.')
from game_logic.test_tarot_objects import Card

context = {'Card': Card}
engine = BardEngine(story, context=context)

print("Initial passage:")
print(engine.current().content)

# Save
save = engine.save_state()
print(f"\nSaved card: {save['state']['card']}")

# Load
engine2 = BardEngine(story, context=context)
engine2.load_state(save)

print("\nAfter load:")
print(f"Type: {type(engine2.state['card'])}")
print(f"Is Card: {isinstance(engine2.state['card'], Card)}")
print(f"Has methods: {hasattr(engine2.state['card'], 'name')}")

# Navigate
engine2.choose(0)
print("\nNext passage:")
print(engine2.current().content)
PYTHON
```

This will show you **exactly** what happens with your current Card class!

## Summary

**Short Answer:**
- ✅ YES, Card objects CAN survive save/load
- ⚠️ BUT you must put Card in the context
- ⚠️ AND current implementation bypasses `__init__`

**Best Practice:**
1. Put all classes in context (either manually or auto-register)
2. Add `to_save_dict()` / `from_save_dict()` to important classes
3. Update engine with improved serialization code

**Which approach do you prefer?**
- A) Keep it simple, just ensure context has classes?
- B) Add serialization methods to classes?
- C) Both (safest)?

I can help implement whichever you choose! 🎯
