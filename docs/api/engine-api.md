# BardEngine API Reference

This document describes the contract and usage patterns for the Bardic runtime engine.

## Core Principle: Separation of Execution and Rendering

The BardEngine follows a strict separation between:
- **Execution** (side effects: variable changes, commands) - happens **once** per passage entry
- **Rendering** (pure: reading state, displaying content) - can be called **safely** multiple times
- **Navigation** (state changes: moving between passages)

## Public API

### Constructor: `BardEngine(story_data)`

**Purpose**: Initialize engine and navigate to the initial passage

**Behavior**:
- Validates story data
- Navigates to `initial_passage` (executes commands, caches output)
- After construction, engine is ready to use with `current()`

**Example**:
```python
with open('story.json') as f:
    story_data = json.load(f)

engine = BardEngine(story_data)
# Engine is now at initial passage, commands executed, output cached
output = engine.current()  # Read the cached output
```

---

### `goto(passage_id: str) -> PassageOutput`

**Purpose**: Navigate to a passage and execute its commands

**When to use**: Direct navigation (story jumps, debugging, testing)

**What it does**:
1. Changes `current_passage_id` to the target
2. **Executes passage commands** (variable assignments, etc.) - **ONCE**
3. Renders content and filters choices based on new state
4. Caches the `PassageOutput`
5. Returns the `PassageOutput`

**Example**:
```python
# Jump directly to a passage
output = engine.goto('Chapter2.Start')

# Commands in Chapter2.Start are executed once
# State is updated, output is cached
```

**Important**: This is the ONLY method that executes passage commands.

---

### `current() -> PassageOutput`

**Purpose**: Get the current passage output (read-only)

**When to use**:
- Display current passage content
- Check current state
- Read available choices
- Any time you need current info without changing state

**What it does**:
- Returns cached `PassageOutput`
- **NO execution, NO side effects**
- Safe to call multiple times

**Example**:
```python
# Read current passage (safe, no side effects)
output = engine.current()
print(output.content)
print(f"Choices: {[c['text'] for c in output.choices]}")

# Call again - same result, no re-execution
output2 = engine.current()  # Returns cached output
```

**Guarantee**: Will never execute commands or modify state.

---

### `choose(choice_index: int) -> PassageOutput`

**Purpose**: Make a choice and navigate to the target passage

**When to use**: Player selecting a choice from the displayed options

**What it does**:
1. Gets **filtered choices** from cached output
2. Validates the choice index against filtered choices
3. Gets target passage from the selected choice
4. Calls `goto(target)` to navigate (executes target passage)
5. Returns the new `PassageOutput`

**Example**:
```python
# Display choices to user
output = engine.current()
for i, choice in enumerate(output.choices):
    print(f"{i}. {choice['text']}")

# User picks choice 0
choice_idx = 0
output = engine.choose(choice_idx)  # Navigates to target passage
```

**Important**: Choice indices match the **filtered** choices that the user sees, not the raw passage data.

---

## State Access

### `engine.state: Dict[str, Any]`

The global story state (variables). Modified by passage commands during `goto()`.

**Example**:
```python
# Read state
health = engine.state.get('health', 100)

# Manually modify state (use sparingly)
engine.state['debug_mode'] = True
```

### `engine.current_passage_id: str`

The ID of the current passage.

---

## PassageOutput (Return Type)

All navigation methods return a `PassageOutput` dataclass:

```python
@dataclass
class PassageOutput:
    content: str              # Rendered text content
    choices: List[Dict]       # Available choices (filtered by conditions)
    passage_id: str           # Current passage ID
```

**Choices format**:
```python
{
    "text": "Choice display text",
    "target": "TargetPassageID",
    "condition": "health > 0"  # or None
}
```

Only choices where `condition` evaluates to `True` are included.

---

## Common Usage Patterns

### Starting a Story

```python
# Initialize - navigates to initial passage automatically
engine = BardEngine(story_data)

# Display initial passage
output = engine.current()
print(output.content)
show_choices(output.choices)
```

### Player Makes a Choice

```python
# Get current state
output = engine.current()

# Show choices
for i, choice in enumerate(output.choices):
    print(f"{i}. {choice['text']}")

# Player picks choice
choice_idx = int(input("Choose: "))

# Navigate (executes target passage)
output = engine.choose(choice_idx)

# Display new passage
print(output.content)
```

### Direct Navigation (Testing/Debugging)

```python
# Jump to a specific passage
output = engine.goto('Debug.TestScene')

# Check state
print(engine.state)

# Jump to another
output = engine.goto('Chapter3.Boss')
```

### Checking Conditions

```python
# Current state is safe to read multiple times
output = engine.current()

if len(output.choices) == 0:
    print("Story ended")
elif engine.state.get('health', 0) <= 0:
    print("Game over")
```

---

## Execution Guarantees

### ✓ Commands Execute Exactly Once Per Passage Entry

When you call `goto(passage_id)`:
- Commands execute **once**
- State is updated **once**
- Output is cached

Subsequent calls to `current()` return the cached output without re-execution.

### ✓ Rendering is Pure

The rendering process (`_render_passage`) has **zero side effects**:
- Reads state (doesn't modify it)
- Evaluates expressions (doesn't change variables)
- Filters choices based on conditions (doesn't alter passage data)

### ✓ Choice Indices Always Match Filtered Output

When you call `choose(index)`, the index refers to the **filtered choices** that the user sees, not the raw passage data.

**Example**:
```
Passage has: [A (hidden), B (visible), C (visible)]
User sees: [B (index 0), C (index 1)]
choose(0) → navigates to B ✓
choose(1) → navigates to C ✓
```

### ✓ Cache Consistency

The cached output (`_current_output`) always reflects:
- The current passage ID
- The state after commands executed
- The correctly filtered choices

---

## Internal Methods (Private)

These are implementation details. Do not call directly.

### `_execute_passage(passage_id: str) -> None`

Executes passage commands (side effects only). Called by `goto()`.

### `_render_passage(passage_id: str) -> PassageOutput`

Renders content and filters choices (pure, no side effects). Called by `goto()`.

### `_execute_commands(commands: List[dict]) -> None`

Executes individual commands (variable assignments).

### `_is_choice_available(choice: dict) -> bool`

Evaluates choice condition to determine if it should be shown.

### `_render_content(tokens: List[dict]) -> str`

Renders content tokens with variable interpolation.

---

## Migration from Old API

If you have code using the old `render_passage()` method:

**Old (unsafe)**:
```python
output = engine.render_passage('SomePassage')  # Re-executes commands!
```

**New (safe)**:
```python
# For navigation:
output = engine.goto('SomePassage')  # Executes once, caches

# For reading:
output = engine.current()  # No execution, reads cache
```

---

## Future Extensions

This architecture supports future language features without breaking the execution model:

- **`<<py>>` blocks** → Execute in `_execute_passage()`
- **Conditional content** → Evaluate in `_render_passage()` (pure)
- **Visit tracking** → Track in `goto()`
- **Saves/loads** → Restore `state` + `current_passage_id`, then re-render
