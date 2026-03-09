# Bardic Language Specification v1.0

**Status:** Current as of v0.7.0
**Philosophy:** Build for real needs, not hypothetical ones

---

## Overview

Bardic is a Python-first interactive fiction engine designed for narratives that integrate deeply with Python backends and modern web frontends.

**Primary Use Case:** Interactive fiction that needs:

- Complex game logic in Python
- Rich data models (objects, not just primitives)
- Integration with web services/APIs
- Modern React-based UIs
- Server-side state management

**Built For:** A tarot reading game where players influence clients' lives through card interpretations.

## Syntax Reference

Quick reference for all Bardic syntax elements:

| Symbol | Meaning | Example |
|--------|---------|---------|
| `::` | Passage definition | `:: PassageName` |
| `@include` | Include external file | `@include shared/file.bard` |
| `@render` | Render directive | `@render render_spread(cards)` |
| `@input` | Input directive | `@input name="player_name" label="Your Name"` |
| `@py:` / `@endpy` | Python code block | `@py:\ncode\n@endpy` |
| `@if:` / `@elif:` / `@else:` / `@endif` | Conditional | `@if condition:` |
| `@for:` / `@endfor` | Loop | `@for item in list:` |
| `@hook` | Register event hook | `@hook turn_end MyPassage` |
| `@unhook` | Unregister event hook | `@unhook turn_end MyPassage` |
| `@join` | Merge point for inline blocks | `@join` |
| `-> @join` | Choice with inline block | `+ [Text] -> @join` |
| `-> @prev` | Jump to previous passage | `+ [Go back] -> @prev` |
| `~` | Variable assignment | `~ health = 100` |
| `~ var += value` | Augmented assignment | `~ count += 1` |
| `{}` | Expression | `{variable}` or `{function()}` or `{var:.2f}` |
| `+` | Sticky choice | `+ [Text] -> Target` |
| `*` | One-time choice | `* [Text] -> Target` |
| `->` | Immediate jump | `-> Target` |
| `<>` | Glue (suppress newline) | `Text<>` |
| `#` | Full-line comment | `# This whole line is a comment` |
| `//` | Inline comment | `Text here // rest is comment` |
| `[!tag]` | Custom markup (TBA) | `[!whisper]text[/!whisper]` |

**Import statements** use standard Python syntax with no prefix.

---

## Design Principles

1. **Python is First-Class** - Not a scripting afterthought, but core to the language
2. **Simple Core, Extensible** - Basic features work simply; complexity is opt-in
3. **Objects Over Primitives** - Support rich Python objects with methods and attributes
4. **Web-Native** - Designed for FastAPI + React, not desktop apps
5. **Ink-Inspired** - Learn from Ink's elegance, especially whitespace handling
6. **Scratch Our Own Itch** - Features exist because we need them, not "just in case"

---

## File Format

- **Extension:** `.bard`
- **Encoding:** UTF-8
- **Structure:** Line-based, with multi-line blocks for Python code

---

## Core Syntax

### Passages

The fundamental unit of narrative. Every story is a collection of passages.

```bard
:: PassageName Content goes here.
```

**Rules:**

- Passage names are case-sensitive
- Must start with `::` followed by a space
- Name can contain letters, numbers, underscores, dots
- Dots create namespace conventions (e.g., `Client.Aria.Session1`)

### Start Passage

Every story needs an initial passage. Bardic determines the start passage using this priority:

#### 1. Explicit `@start` directive (highest priority)

```bard
@start GameIntro
:: GameIntro
The story begins here.
:: Start
This is NOT the start (explicit override).
```

#### 2. Passage named "Start" (convention, like Twine)

```bard
:: Start
The story begins here by convention.
:: Other
Not the start.
```

#### 3. First passage (fallback with warning)

```bard
:: FirstPassage
Becomes start with a warning printed.
```

**Recommendations:**

- Use `:: Start` for most stories (clear convention)
- Use `@start CustomName` when you need a different entry point
- Always include a passage named "Start" to avoid surprises

---

### Text Content

Regular text is rendered as-is. Markdown is supported.

```bard
:: Example This is regular text.

This is **bold** and _italic_.

- Bullet list
- Another item
```

**Whitespace Rules:**

- Empty line (blank line) = paragraph break (`\n\n`)
- Content line = adds single newline after
- Logic blocks (`@if`, `@for`) follow same rules
- Use glue operator `<>` to suppress newlines (see below)

**Text Formatting:**

Bardic supports standard Markdown formatting (except headers).

**Supported:**

- `**bold**` → **bold**
- `*italic*` → *italic*
- `***bold italic***` → ***bold italic***
- `~~strikethrough~~` → ~~strikethrough~~
- `` `code` `` → `code`
- `[link](url)` → [link](url)
- Lists (bulleted and numbered)
- Blockquotes (`>`)
- Horizontal rules (`---`)
- Code blocks (` ``` `)

**Not Supported:**

- `# Headers` - Conflicts with comment syntax
- Use passage names for structure instead
- Or use custom tags: `[!heading]Text[/!heading]`
- Or HTML: `<h1>Text</h1>`

**Comments:**

`# This is a comment (Python-style)`

Not rendered in output.

**Example:**

```bard
:: DramaticMoment
# Comment: This is the climax
She looks at the cards, her face **pale**.
"Is this... *really* what you see?"
You can sense her ~~fear~~ anxiety.

* [Tell the truth] -> Truth
* [Soften the blow] -> Gentle
```

---

### Glue Operator `<>`

The glue operator suppresses the automatic newline that normally follows a line of content. This allows you to combine content from multiple lines (including conditionals and loops) into a single continuous line.

**Syntax:** End a line with `<>` to prevent adding a newline.

**Basic Usage:**

```bard
The cards whisper<>
@if reader.style == "intuitive":
, and you feel their meaning in your bones.
@elif reader.style == "analytical":
, and you systematically decode each symbol.
@else:
, guiding you forward.
@endif
```

**Output:** `The cards whisper, and you feel their meaning in your bones.`

**Pluralization:**

```bard
You have {count} item<>
@if count != 1:
s<>
@endif
.
```

**Outputs:**

- If `count = 1`: `You have 1 item.`
- If `count = 3`: `You have 3 items.`

**With Loops:**

```bard
The spread contains<>
@for card in [" the Fool", " the Magician", " the Priestess"]:
{card}<>
@endfor
.
```

**Output:** `The spread contains the Fool the Magician the Priestess.`

**Important Notes:**

- Glue only works when `<>` appears at the **end of a line**
- Literal `<>` in the middle of text is preserved: `x <> y` renders as `x <> y`
- Works in passages, conditionals (`@if`), and loops (`@for`)
- The glue operator is inspired by Ink's glue syntax

---

### Choices

Allow player navigation between passages.

```bard
- [Choice text] -> TargetPassage
```

**Rules:**

- Choices start with `+` (sticky) or `*` (one-time)
- Square brackets contain display text
- `->` points to target passage
- Target must be a valid passage name

**Variations:**

```bard
# Sticky choice (always available)

+ [Look around] -> Examine

# One-time choice (only show once)

* [Pick up the key] -> GetKey

# Conditional choice

+ {health > 50} [Fight the dragon] -> Combat

# Choice with parameters (pass data to next passage)

+ [Draw cards] -> DrawCards(count=3, spread='celtic_cross')
```

---

### Inline Python Statements (`~`)

Execute single-line Python statements directly in your story content.

**Syntax:** `~ <any valid Python statement>`

```bard
~ health = 100
~ client.add_trust(15)
~ inventory.append("key")
```

**Rules:**

- Must be a single logical line (though can span physical lines for lists/dicts/parenthesized expressions)
- Has access to all variables in `state` and functions in `context`
- Modifies state directly and immediately
- Executes in order with other passage content
- Gets compiled to `execute` commands that run before rendering

---

#### What You Can Do

**Variable Assignment:**

```bard
~ health = 100
~ name = "Hero"
~ has_key = True
~ inventory = []
~ card = Card()
```

**Augmented Assignment:**

Shorthand operators for updating variables:

```bard
~ count += 1              # Same as: count = count + 1
~ health -= 10            # Same as: health = health - 10
~ total *= 2              # Same as: total = total * 2
~ price /= 1.5            # Same as: price = price / 1.5
~ items //= 2             # Same as: items = items // 2 (floor division)
~ remainder %= 10         # Same as: remainder = remainder % 10
~ area **= 2              # Same as: area = area ** 2 (exponentiation)
```

**Supported operators:** `+=`, `-=`, `*=`, `/=`, `//=`, `%=`, `**=`

**Works with complex expressions:**

```bard
~ total += (base * multiplier) + bonus
~ score -= penalty_amount * difficulty
```

**Method Calls:**

```bard
~ client.add_trust(15)
~ client.discuss_topic("grief")
~ deck.shuffle()
~ reader.add_experience(50)
```

**List/Dict Operations:**

```bard
~ inventory.append("key")
~ cards_seen.extend([card.name for card in drawn_cards])
~ stats["strength"] += 5
~ del inventory[0]
```

**Complex Expressions:**

```bard
~ filtered_cards = [c for c in deck.cards if c.is_major()]
~ total_value = sum(item.value for item in inventory)
~ average = total / len(items) if items else 0
```

**Multiline Expressions:**

The `~` operator supports multiline for lists, dicts, and parenthesized expressions:

```bard
~ total += (
    base_value +
    bonus_multiplier +
    situational_modifier
)

~ my_list = [
    first_item,
    second_item,
    third_item
]

~ client_data = {
    "name": client.name,
    "trust": client.trust,
    "sessions": client.sessions_completed
}
```

**Debug Output:**

```bard
~ print(f"[DEBUG] Trust: {client.trust}, Session: {session_num}")
~ print(f"Cards drawn: {[c.name for c in cards]}")
```

---

#### What You Can't Do

```bard
# ❌ Multiple statements (no semicolons - use separate ~ lines)
~ trust = 50; comfort = 50

# ❌ Control flow structures
~ if health < 50:
    health = 50  # Use @py: blocks for this

# ❌ Loops
~ for item in inventory:
    process(item)  # Use @py: blocks for this

# ❌ Function definitions
~ def my_func():
    return 42  # Use @py: blocks for this

# ❌ Import statements
~ import random  # Use file-level imports instead
```

---

#### `~` vs `@py:` Blocks

> [!TIP]
> 💡 **When to use which:**
>
> **Use `~` for quick one-liners:**
>
> - Variable assignments: `~ gold = 100`
> - Method calls: `~ client.add_trust(10)`
> - Simple operations: `~ inventory.append("key")`
> - Debug output: `~ print(f"Trust: {trust}")`
>
> **Use `@py:` blocks for complex logic:**
>
> - Loops: `for card in cards: ...`
> - Conditionals: `if health < 50: ...`
> - Multi-statement sequences
> - Function definitions
> - Complex algorithms
>
> **Think of `~` as "inline Python" and `@py:` as "Python block".**
>
> ⚠️ **Side effects happen immediately:** When you write `~ client.add_trust(10)`, that trust is added right now, during passage execution. The change persists across passages. If you're modifying objects or collections, remember that `~` statements run in the order they appear.

---

#### Display Variables

Access variables in story text using `{expression}` syntax:

```bard
You have {health} health. Your name is {name}.
The client's trust is {client.trust}.
You've completed {reader.sessions_completed} sessions.
```

**Format Specifiers:**

Use Python's format specification mini-language to control display:

```bard
Average: {average:.1f}        # Float with 1 decimal place
Price: ${price:.2f}           # Float with 2 decimal places
Count: {count:03d}            # Integer with leading zeros (007)
Name: {name:>10}              # Right-aligned, 10 characters wide
Percent: {ratio:.1%}          # Percentage (0.753 → 75.3%)
```

**Common Format Specs:**

- `.Nf` - Float with N decimal places (`:.2f` → `3.14`)
- `0Nd` - Integer with N digits, zero-padded (`03d` → `007`)
- `>N` - Right-align in N spaces (`>10`)
- `<N` - Left-align in N spaces (`<10`)
- `^N` - Center in N spaces (`^10`)
- `.N%` - Percentage with N decimals (`.1%` → `75.3%`)

---

#### Common Patterns

**Update character stats:**

```bard
~ reader.add_experience(50)
~ reader.add_money(25)
~ reader.add_competence(1)
```

**Track story progress:**

```bard
~ cards_seen.append(card.name)
~ topics_discussed.add("grief")
~ client.sessions_completed += 1
```

**Conditional side effects:**

```bard
~ client.unlock_memory("childhood") if client.trust >= 80 else None
~ bonus_gold = 50 if reader.reputation >= 5 else 0
```

**Batch updates (use multiple lines):**

```bard
~ client.add_trust(10)
~ client.add_comfort(5)
~ client.discuss_topic("fear")
```

**Calculate before displaying:**

```bard
~ total_value = sum(item.price for item in inventory)
~ average_trust = sum(c.trust for c in clients) / len(clients)

Your inventory is worth {total_value} gold.
Average client trust: {average_trust:.1f}
```

---

#### Error Handling

When a `~` statement fails, Bardic provides detailed error messages with source file and line number:

```bard
~ undefined_function()
```

**Error output:**

```sh
RuntimeError: Error executing statement in passage 'MyPassage'
  File: story.bard, Line: 42
  Statement: undefined_function()

  NameError: name 'undefined_function' is not defined

  Available variables: ['client', 'reader', 'health', 'cards']
  Available functions: ['draw_cards', 'roll_dice']
```

---

### Python Code Blocks

Execute multi-line Python code in passages.

**Syntax:** `@py: ... @endpy`

```bard
:: Example
@py:
# Multi-line Python code

import random

rolls = []
for i in range(5):
    roll = random.randint(1, 6)
    rolls.append(roll)
total = sum(rolls)
average = total / len(rolls)

if total > 20:
    outcome = "great"
else:
    outcome = "okay"
@endpy

Results: {total} (average: {average:.1f})
Outcome: {outcome}
````

**Rules:**

- Opens with `@py:` (colon required)
- Closes with `@endpy` (no colon)
- Can span multiple lines
- Preserves Python indentation
- Executes in order with other commands
- Has access to:
  - All variables in `self.state`
  - All functions in `context`
  - Safe standard library imports
  - Safe builtins (len, str, int, etc.)
- Modifies state directly
- Produces no output (use variables to display results)

**What's Available:**

```python
# Safe builtins
len, str, int, float, bool, list, dict, tuple, set
range, enumerate, zip, sum, min, max, abs, round
sorted, any, all, print

# Safe imports
import random
import math
import datetime
# ... other standard library modules
````

**Context Functions:** Functions can be provided via engine context:

```python
context = {
    'roll_dice': lambda sides=6: random.randint(1, sides),
    'greet': lambda name: f"Hello, {name}!",
}

engine = BardEngine(story, context=context)
```

Then in stories:

```bard
@py:
result = roll_dice(20)
greeting = greet("Hero")
@endpy
```

**Error Handling:**

- Syntax errors show the problematic line
- Runtime errors show full traceback
- Undefined variables list available variables

---

### Python Expressions

Inline Python evaluation in content.

```bard
You rolled a {roll_dice(20)}.
The card is {card.get_display_name()}.
{greet(player_name)}
```

**Rules:**

- Wrapped in `{}`
- Can be variable names, function calls, or expressions
- Evaluated at render time with full Python syntax
- Result is converted to string for display
- Has access to:
  - All variables in `self.state`
  - All functions in `context`
  - Safe builtins (len, str, int, sum, max, etc.)
  - Imported modules (from `@py:` blocks)

**Safe Builtins Available:**

```python
len, str, int, float, bool, list, dict, tuple, set
range, enumerate, zip, sum, min, max, abs, round
sorted, reversed, any, all, print
__import__  # For import statements
```

**Examples:**

```bard
# Simple expressions
Health: {health}
Total: {x + y}
Percentage: {score / max_score * 100:.1f}%

# Function calls
You rolled: {roll_dice(20)}
Greeting: {greet(player.name)}
Damage: {calculate_damage(attack, defense)}

# Built-in functions
Count: {len(inventory)}
Total: {sum(scores)}
Best: {max(results)}

# String methods
Uppercase: {name.upper()}
First word: {text.split()[0]}

# List comprehensions
Doubled: {[x * 2 for x in numbers]}

# Complex expressions
Average: {sum(values) / len(values):.2f}
Status: {"alive" if health > 0 else "dead"}
```

**Format Specifiers:**

Expressions support optional format specifications using Python's format spec syntax:

```bard
{expression:format_spec}
```

**How it works:**

1. Engine splits at the `:` (rightmost occurrence)
2. Evaluates the expression part
3. Applies the format spec using `format(value, spec)`

**Examples:**

```bard
Score: {total_score:05d}              # Zero-padded: 00123
Accuracy: {hit_rate:.1%}              # Percentage: 87.5%
Damage: {damage:.2f}                  # Float: 42.50
Name: {player_name:^20}               # Centered: "    Alice    "
```

**Limitations:**

- Comparison operators are excluded from format parsing to prevent conflicts:
  - `{a == b}` - Evaluates as comparison (not format spec)
  - `{a <= b}` - Evaluates as comparison
  - `{a != b}` - Evaluates as comparison
  - `{a >= b}` - Evaluates as comparison
  - `{dict::key}` - Double colon preserved (Python dict syntax)

- Format spec must be a valid Python format specification
- Uses rightmost `:` to split expression from format spec
- Invalid format specs will show an error in the output

**Object Attributes and Methods:**

```bard
# Accessing attributes
Card: {card.name}
Health: {player.stats.health}
Position: {card.position}

# Calling methods
Display: {card.get_display_name()}
Status: {player.get_status()}
Trust: {client.get_trust_description()}

# Nested attributes
Health: {character.stats.health}
Weapon: {character.equipped["weapon"]}

# Method chaining
Result: {card.set_reversed(True).in_position("past")}

# List operations with objects
Names: {[card.name for card in cards]}
Major: {[c for c in cards if c.is_major_arcana()]}

# Dictionary operations
Client: {clients["aria"].name}
Best: {max(clients.values(), key=lambda c: c.trust).name}
```

**Full Python Object Support:**

- Access attributes of any Python object
- Call methods with arguments
- Navigate nested attributes
- Use objects in comprehensions
- Method chaining supported
- Dictionary and list operations work naturally

---

### Special Variables

Bardic provides special built-in variables for safe state inspection and debugging.

#### `_state` - Global State Dictionary

Direct reference to the engine's global state dictionary. Useful for defensive coding and existence checks.

```bard
:: Start
~ hp = 100
~ gold = 500

# Safe access with defaults
HP: {_state.get('hp', 0)}
Mana: {_state.get('mana', 100)}  # Uses default if missing

# Existence checks
@if 'inventory' in _state:
    You have an inventory.
@else:
    No inventory found.
@endif

# Inspect available variables
Available vars: {list(_state.keys())}
Total vars: {len(_state)}
```

**Common use cases:**

- Safe variable access: `{_state.get('optional_var', 'default')}`
- Existence checking: `{'var_name' in _state}`
- Debugging: `{sorted(_state.keys())}`
- Conditional rendering: `@if _state.get('has_sword'): ...`

#### `_local` - Local Scope Dictionary

Direct reference to current local scope (passage parameters). Always available, empty dict if no parameters.

```bard
:: ShowItem(item=None)

# Check if parameter was provided
@if _local.get('item'):
    You examine the {item}.
@else:
    You have nothing to examine.
@endif

# Inspect parameters
Params: {list(_local.keys())}
```

**Common use cases:**

- Optional parameters: `{_local.get('param', 'default')}`
- Parameter existence: `{'param' in _local}`
- Reusable passages that work with/without params
- Debugging: `{sorted(_local.keys())}`

#### Scope Isolation

Parameters are local-only and don't leak into global state:

```bard
:: Start
~ hp = 100

+ [Attack] -> Combat(25)

:: Combat(damage)

Global HP: {_state.get('hp')}        # 100
Local damage: {_local.get('damage')}  # 25

# 'damage' is NOT in global state
In global: {'damage' in _state}       # False
In local: {'damage' in _local}        # True
```

#### `_visits` - Passage Visit Counter

Dictionary tracking how many times each passage has been entered. Automatically incremented on every `goto()` call (including the initial passage at engine startup).

```bard
:: Tavern
@if _visits.get("Tavern", 0) == 1:
    You push open the tavern door for the first time.
@elif _visits.get("Tavern", 0) <= 3:
    You return to the familiar tavern.
@else:
    The bartender nods. "The usual?"
@endif

+ [Leave] -> Town
```

**Common use cases:**

- First-visit content: `@if _visits.get("Room", 0) == 1: ...`
- Returning content: `@if _visits.get("Room", 0) >= 2: ...`
- Conditional choices: `+ {_visits.get("Library", 0) >= 3} [Secret passage] -> Hidden`
- Visit display: `You've been here {_visits.get("Tavern", 0)} times.`

**Notes:**

- Passages not yet visited are absent from the dict — always use `.get()` with a default
- The initial passage starts at visit count 1 (the engine navigates to it on startup)
- Jump targets (via `->`) are also counted
- Survives undo/redo and save/load

#### `_turns` - Turn Counter

Integer counting total player choices made. Incremented by `choose()` only — programmatic navigation via `goto()` does not count as a turn.

```bard
:: Dungeon
@if _turns >= 30:
    The dungeon begins to collapse! Time is running out!
@endif

You see a dark corridor ahead.
Turns elapsed: {_turns}

+ [Go deeper] -> DungeonDeep
+ {_turns >= 20} [I've explored enough...] -> Exit
```

**Common use cases:**

- Pacing: Show different text after N turns
- Urgency: `The bomb detonates in {50 - _turns} turns!`
- Scoring: `You escaped in {_turns} turns!`
- Unlocking content: `+ {_turns >= 10} [New option] -> Secret`

**Notes:**

- Starts at 0
- Only incremented by player choices (`choose()`), not `goto()`
- Survives undo/redo and save/load

---

### Conditionals

Branch content based on conditions.

```bard
@if condition:
Content if true.
@elif other_condition:
Content if other is true.
@else:
Default content.
@endif
```

**Examples:**

```bard
@if health > 75:
You feel strong and healthy.
@elif health > 25:
You're wounded but standing.
@else:
You're barely conscious.
@endif
```

**Rules:**

- Conditions are Python expressions
- Colons (`:`) are required after `@if`, `@elif`, and `@else`
- Can access all variables and functions
- Can be nested
- Produces no whitespace itself (only renders chosen branch)
- Must close with `@endif` (no colon)
- Multiple `@elif` branches allowed
- `@else` is optional
- First true condition wins (like Python if/elif/else)

**Complex Conditions:**

```bard
@if gold > 100 and trust > 50:
Wealthy and trusted!
@elif gold > 50 or has_key:
Have resources.
@elif not has_key and gold < 20:
Poor and locked out.
@else:
Getting by.
@endif
```

**With Objects:**

```bard
@if client.trust_level > 75:
Deeply trusted.
@elif any(card.is_major_arcana() for card in cards):
Major arcana drawn!
@else:
Standard reading.
@endif
```

**Nested Conditionals:**

```bard
@if player_class == "warrior":
  @if health > 75:
  Strong warrior!
  @else:
  Wounded warrior.
  @endif
@else:
  Not a warrior.
@endif
```

**Error Handling:**

- Failed conditions skip that branch
- Warnings printed to console
- Story continues with next branch
- Missing `@endif` causes parse error
- Missing colon on `@if`, `@elif`, or `@else` causes helpful syntax error

---

### Inline Conditionals

Choose between two text options inline using ternary-style syntax.

```bard
{condition ? truthy_text | falsy_text}
```

**Basic Examples:**

```bard
You are {health > 50 ? healthy | wounded} right now.
Status: {alive ? breathing | deceased}
The door is {locked ? locked | unlocked}.
```

**With Expressions:**

```bard
Inventory: {inventory ? {", ".join(inventory)} | Empty}
Price: {on_sale ? {price * 0.8:.2f} | {price:.2f}} gold
Items: {items ? You have {len(items)} items | You have nothing}
```

**Empty Branches:**

```bard
{has_key ? You unlock the door. | }
{locked ? | The door is already open.}
```

**Why Use Inline Conditionals:**

Inline conditionals are cleaner than Python's ternary for text-heavy content:

```bard
# Inline conditional (clean, no quote escaping!)
{inventory ? {", ".join(inventory)} | Empty}

# Python ternary (quote hell)
{", ".join(inventory) if inventory else "Empty"}
```

**Rules:**

- Syntax: `{condition ? truthy | falsy}`
- Uses `?` and `|` operators (not `:` to avoid format spec collision)
- Both branches are optional (can be empty)
- Condition is any Python expression
- Branches can contain expressions: `{condition ? {func()} | text}`
- Branches can use format specs: `{condition ? {price:.2f} | free}`
- Works inline within flowing text
- Python ternary still works (backwards compatible)
- Nested conditionals are NOT supported (by design - use multi-line `@if` for complex logic)

**Format Specs in Branches:**

```bard
~ discount = 0.2
~ price = 100

Regular: {price:.2f} gold
On sale: {on_sale ? {price * (1 - discount):.2f} | {price:.2f}} gold
```

**Multiple in One Line:**

```bard
You walk through the {locked ? locked | unlocked} door and see {inventory ? your items | nothing}.
```

**Common Patterns:**

```bard
# Boolean checks
{has_item ? "You have it." | "You don't have it."}

# Numeric comparisons
{health > 75 ? Healthy | {health > 25 ? Wounded | Critical}}

# Empty collections
{cards ? {len(cards)} cards | No cards}

# Existence checks
{player_name ? Hello, {player_name}! | Hello, stranger!}
```

**Design Philosophy:**

Inline conditionals are for **simple, readable text choices**. For complex nested logic or multiple conditions, use multi-line `@if/@elif/@else` blocks instead. This keeps your story text maintainable and easy to read.

---

### Loops

Iterate over collections to generate dynamic content.

```bard
@for variable in collection:
  content using {variable}
@endfor
```

**Examples:**

```bard
# Simple list
@for item in items:
- {item}
@endfor

# Range
@for i in range(5):
Number {i}
@endfor

# Objects
@for card in cards:
{card.name}: {card.get_display_name()}
@endfor

# Enumerate
@for i, item in enumerate(items):
{i+1}. {item}
@endfor

# With start index
@for i, item in enumerate(items, 5):
{i}. {item}
@endfor
```

~~**Inline loops:**~~

```bard
Cards drawn: @for card in cards:{card.name}, @endfor
```

- Opens with `@for variable in collection:` (colon required)
- Closes with `@endfor` (no colon)
- Variable available in expressions within loop
- Collection evaluated once before loop starts
- Can iterate over: lists, tuples, ranges, dicts, etc.
- Supports tuple unpacking (enumerate, zip, etc.)
- Can be nested
- Loop variable is temporary (doesn't persist after loop)

**Nested Loops:**

```bard
@for suit in suits:
  Suit: {suit}
  @for rank in ranks:
    {rank} of {suit}
  @endfor
@endfor
```

**With Conditionals:**

```bard
@for item in inventory:
  @if item.power > 10:
  - {item.name} (powerful!)
  @endif
@endfor
```

**Tuple Unpacking:**

```bard
@for key, value in items.items():
{key}: {value}
@endfor

@for i, card in enumerate(cards):
Card {i+1}: {card.name}
@endfor
```

---

### Comments

Document your story with two types of comments.

#### Full-Line Comments

```bard
# This entire line is a comment
```

Lines starting with `#` are completely ignored by the parser.

#### Inline Comments

Add comments to the end of any line using `//`:

```bard
@if reader.trust_level > 75: // High trust branch
  Deep reading. // Emotional, intuitive response
  {render_card(spread[0])} // Special formatting
@endif

~ health = 100 // starting value

+ [Open door] -> Room // requires key

Normal text here // this part is ignored
```

**Where Inline Comments Work:**

- Passage headers: `:: PassageName // comment about this passage`
- Content lines: `Text here // comment`
- Conditionals: `@if condition: // comment`
- Loops: `@for item in list: // comment`
- Variables: `~ var = value // comment`
- Choices: `+ [Text] -> Target // comment`
- Directives: `@input name="x" // comment`

**Escaping:**

Use `\//` for literal slashes in your text:

```bard
URL: https:\//example.com // This is a comment
```

Output: `URL: https://example.com`

**Important Notes:**

- Everything after `//` is ignored
- `\//` becomes literal `//`
- Only first `//` on a line starts comment
- Works everywhere except inside `@py:` blocks (use Python's `#` there)
- Inside expressions `{}`, use Python syntax (Python handles it)

**Rules:**

- `#` for full-line comments
- `//` for inline comments
- Both extend to end of line
- Ignored by compiler
- Not rendered in output

---

### Hooks (@hook / @unhook)

Register passages to run automatically on specific events. Useful for background systems like poison effects, timers, or turn counters.

**Syntax:**

```bard
@hook event_name PassageName    # Register a hook
@unhook event_name PassageName  # Unregister a hook
```

**Built-in Events:**

- `turn_end` - Fires after every `choose()` call

**Example: Poison System**

```bard
:: Start
You feel fine.
+ [Drink poison] -> DrinkPoison
+ [Continue] -> Room

:: DrinkPoison
You drink the mysterious liquid...
@hook turn_end PoisonTick
~ poison_damage = 5
~ health = 100
-> Room

:: PoisonTick
~ health = health - poison_damage
@if health <= 0:
    @unhook turn_end PoisonTick
@endif

:: Room
Health: {health}
+ [Wait] -> Room
+ [Find antidote] -> Antidote

:: Antidote
You found the cure!
@unhook turn_end PoisonTick
+ [Continue] -> Room
```

**How It Works:**

1. `@hook turn_end PassageName` registers a passage to run after each turn
2. The hooked passage executes silently (content not shown, just side effects)
3. `@unhook turn_end PassageName` removes the registration
4. Multiple passages can hook the same event (FIFO order)
5. Hook registration is idempotent (duplicate registrations ignored)
6. Hooks can self-remove with `@unhook` inside `@if` blocks

**Engine API:**

```python
engine.register_hook("turn_end", "MyPassage")
engine.unregister_hook("turn_end", "MyPassage")
engine.trigger_event("turn_end")  # Returns combined output
```

**Rules:**

- Hook/unhook inside `@if`/`@for` blocks work correctly
- Hook state is included in undo/redo snapshots
- Hooked passages execute their `execute` commands only (content is hidden)
- A passage can unregister itself (for one-time effects)

---

### Imports

Import Python modules at the top of the file.

**Syntax:** Standard Python import statements

```bard
from models.card import Card
from services.tarot import TarotService, draw_from_pool
from utils.narrative import generate_greeting

# Includes come after imports
@include shared/card_mechanics.bard

# Story starts after imports and includes
:: Start
You draw three cards...
```

**Rules:**

- Must be at the top of the file (before any passages or includes)
- Standard Python import syntax (no special prefix needed)
- Available to all passages in the file
- Can import from your project's Python modules
- Each import statement on its own line
- Empty lines and comments allowed in import section
- Imports execute once when engine initializes
- Imported modules/objects available in state

**Examples:**

```bard
# Import specific items
from models.card import Card, Deck

# Import entire module
import random

# Import with alias
from services.tarot import TarotService as Tarot

# Multiple imports
from models.card import Card
from models.client import Client
from services.tarot import TarotService
```

**Error Handling:**

- Import errors show clear messages
- Missing modules are caught at engine initialization
- Imports after other content raise parse errors

---

### Metadata

Specify story metadata like title, author, version, and story ID.

**Syntax:** `@metadata` directive with key-value pairs

```bard
from models.card import Card

@metadata
  title: The Oracle's Journey
  author: Kate Louie
  version: 1.0.0
  story_id: tarot_game
  description: A mystical tarot reading adventure

@include shared/cards.bard

:: Start
Welcome, seeker...
```

**Rules:**

- Must appear after imports, before includes and passages
- Opened with `@metadata` on its own line
- Each metadata field is indented with key-value pairs (`key: value`)
- Empty lines allowed within metadata block
- Block ends when a non-indented line is encountered
- All fields are optional
- Metadata is stored in compiled JSON and accessible at runtime

**Common Fields:**

- `title` - Human-readable story name
- `author` - Story creator
- `version` - Story version (for compatibility checking)
- `story_id` - Unique identifier (used for save files)
- `description` - Brief story description
- You can add any custom fields you need!

**Usage in Engine:**

Metadata is available in `story["metadata"]` and used for:

- Save/load file compatibility checking
- Story listing in web runtime
- Display in UI
- Version tracking

**Example with all features:**

```bard
from models.card import Card
from services.tarot import TarotService

@metadata
  title: The Tarot Reader
  author: Jane Doe
  version: 2.1.0
  story_id: tarot_reader_game
  description: Guide clients through mystical tarot readings
  genre: interactive fiction
  content_warning: none

@include shared/mechanics.bard

:: Start
Your story begins...
```

**Compiled Output:**

```json
{
  "version": "0.1.0",
  "initial_passage": "Start",
  "metadata": {
    "title": "The Tarot Reader",
    "author": "Jane Doe",
    "version": "2.1.0",
    "story_id": "tarot_reader_game",
    "description": "Guide clients through mystical tarot readings",
    "genre": "interactive fiction",
    "content_warning": "none"
  },
  "imports": [...],
  "passages": {...}
}
```

**Backend Usage:**

```python
# Save system automatically uses metadata
save_data = engine.save_state()
# save_data now includes story_id, title, version from metadata

# Story listing uses metadata
story_metadata = story_data.get("metadata", {})
story_title = story_metadata.get("title", "Unknown Story")
story_id = story_metadata.get("story_id", filename)
```

**Benefits:**

- Clean separation of metadata from story content
- Consistent place for story information
- Used automatically by save/load system
- No pollution of game state
- Easy to read and edit
- Optional - stories work fine without it

---

### Tags

Attach metadata to passages, choices, and content lines using the `^tag` syntax.

**Syntax:** `^TAG` or `^CATEGORY:VALUE`

```bard
:: PassageName ^UI:DASHBOARD ^MUSIC:AMBIENT
Content here ^CALLOUT

+ [Choice] -> Target ^STYLE:SPECIAL
```

**Rules:**

- Tags start with `^` followed by alphanumeric characters
- Optional colon `:` for parameterized tags
- Multiple tags allowed (space-separated)
- Works on:
  - Passage headers: `:: Name ^tag1 ^tag2`
  - Content lines: `Text ^tag`
  - Choices: `+ [Text] -> Target ^tag`
- Tags are passed to frontend as-is for interpretation
- Not rendered in output (invisible metadata)

**Use Cases:**

- UI layout hints: `^UI:DASHBOARD`, `^UI:IMMERSIVE`
- Choice categorization: `^CLIENT:SPECIAL`, `^CLIENT:RETURNING`
- Styling: `^CALLOUT`, `^EMPHASIS`, `^WHISPER`
- Game state: `^TUTORIAL:ACTIVE`, `^CUTSCENE`
- Ambient control: `^MUSIC:THEME`, `^AMBIENT:DARK`

### Passage Parameters

Pass data between passages like function arguments. Enables dynamic content patterns like shops, NPC conversations, and combat encounters.

#### Syntax

**Declaration:**

```bard
:: PassageName(param1, param2=default_value)
```

**Navigation:**

```bard
-> PassageName(value1, value2)              # Positional
-> PassageName(param2=value2, param1=value1) # Keyword
+ [Choice] -> PassageName(expression)       # In choices
```

#### Examples

**Basic parameters:**

```bard
:: Start
~ health = 100
+ [Show health] -> Display(health)
+ [Take damage] -> Display(health - 20)

:: Display(hp)
Your health: {hp}
+ [Back] -> Start
```

**Default values:**

```bard
:: Greet(name="World", greeting="Hi")
{greeting}, {name}!

:: Start
+ [Default greeting] -> Greet()
+ [Custom greeting] -> Greet("Alice", "Hello")
```

**Shop system (the killer use case!):**

```bard
:: Shop
~ gold = 500

@for item in shop_inventory:
    + [Buy {item.name} for {item.price} gold] -> BuyItem(item)
@endfor

:: BuyItem(item)
~ gold = gold - item.price
~ player_inventory.append(item)

You bought {item.name}!
+ [Continue] -> Shop
```

#### Rules

- **Declaration:** Parameters defined in passage header with optional defaults
- **Scope:** Parameters are LOCAL variables (don't persist to global state)
- **Arguments:** Support both positional and keyword arguments
- **Validation:** Compile-time checking ensures required params are provided
- **Defaults:** Can reference earlier parameters: `:: Calc(x, y=x*2)`
- **Expressions:** Arguments can be any valid Python expression
- **Persistence:** To save a param value, explicitly assign it: `~ saved_item = item`

#### Implementation Details

- Parameters create a local scope stack in the runtime engine
- Local scope shadows global variables (local takes precedence)
- Scope is automatically cleaned up when leaving the passage
- Compile-time validator checks all passage calls for correct arguments

---

### Render Directives

Tell the frontend to handle custom presentation logic. Render directives emit structured data that your runtime interprets — whether that's rendering React components, instantiating Unity GameObjects, or formatting terminal output.

> **Full reference:** [Render Directives Guide](render-directives.md) — compilation modes, framework hints, frontend integration (React, Unity, CLI), error handling, and complete examples.

**Syntax:** `@render directive_name(args)`

```bard
@render card_spread(cards, layout='celtic_cross')
@render character_portrait(client, emotion='worried')
@render mini_game(game_type='dice', difficulty=3)
```

**Rules:**

- Function-call syntax with Python expressions as arguments
- Not rendered as text — produces structured data for the frontend
- Can appear anywhere: passages, conditionals, loops
- Multiple directives per passage allowed
- Directives are **declarative** — you specify data, the frontend decides how to display it

**Framework hints** (optional): `@render:react card_spread(cards)` adds React-specific fields (PascalCase component names, unique keys, props).

**With conditionals and loops:**

```bard
@if client.trust > 75:
@render character_portrait(client, emotion='happy', size='large')
@else:
@render character_portrait(client, emotion='neutral', size='medium')
@endif

@for card in hand:
@render card_detail(card, interactive=True)
@endfor
```

**Compiled output** is returned in `PassageOutput.render_directives`:

```json
{
  "type": "render_directive",
  "name": "card_spread",
  "mode": "evaluated",
  "data": {"cards": [...], "layout": "celtic_cross"}
}
```

---

### Input Directives

Collect text input from players for names, answers, journal entries, and other custom data.

> **Full reference:** [Input Directives Guide](input-directives.md) — frontend integration (React, NiceGUI, FastAPI), the `_inputs` dictionary, validation patterns, and complete examples.

**Syntax:** `@input name="variable_name" [placeholder="..."] [label="..."]`

```bard
@input name="reader_name" placeholder="Enter your name..." label="Your Name"
```

**Rules:**

- `name` attribute is required (used as dictionary key in `_inputs`)
- `placeholder` and `label` are optional
- Values stored in the `_inputs` dictionary, which persists across all passages
- Access values with `{_inputs.get("reader_name", "Guest")}`

**Common pattern — conditional input display:**

```bard
:: AskName
@if not _inputs.get("reader_name"):
What is your name?
@input name="reader_name" placeholder="Enter your name..."
@else:
Thank you, **{_inputs.get("reader_name")}**!
@endif

+ [Continue] -> NextPassage
```

**Frontend submits input via:**

```python
engine.submit_inputs({'reader_name': 'Kate'})
engine.goto(engine.current_passage_id)  # Re-render with new state
```

---

### Immediate Jumps (Diverts)

Navigate to another passage without a choice. Like Ink's `->` divert.

**Syntax:** `-> PassageName`

```bard
:: CheckHealth
@if health <= 0:
You collapse to the ground...
-> Death
@endif

You're still alive!

:: Death
Game Over.
```

**How It Works:**

1. When `-> Target` is encountered during rendering, it immediately jumps to the target passage
2. Content before the jump is rendered
3. Content after the jump is skipped
4. The target passage is executed and rendered
5. Contents from both passages are combined

**Rules:**

- Syntax: `-> PassageName` (arrow, space, passage name)
- Executes immediately when encountered
- Content BEFORE the jump renders
- Content AFTER the jump is skipped
- Can be used anywhere: passages, conditionals, loops
- Can be conditional (inside `@if` blocks)
- In loops: exits the loop and jumps immediately
- Multiple conditional jumps: only the first true condition jumps
- Jump loop detection prevents infinite recursion
- Compile-time validation: ensures target passages exist

**Examples:**

```bard
# Simple unconditional jump
:: Intro
The game begins...
-> Chapter1

# Conditional jump - automatic progression
:: CheckStatus
@if health <= 0:
You collapse...
-> Death
@elif health < 50:
You're wounded.
-> Injured
@else:
You're healthy.
-> Healthy
@endif

# Jump after Python code
:: ProcessTurn
@py:
turn_count += 1
if turn_count >= 10:
    game_over = True
@endpy

@if game_over:
-> GameOver
@endif

Turn {turn_count} continues...

# Jump in a loop - exits when condition met
:: SearchInventory
@for item in inventory:
Checking {item.name}...
@if item.name == "key":
Found the key!
-> FoundKey
@endif
@endfor

Key not found.

:: FoundKey
You found the key! Time to unlock the door.
```

**Multiple Conditional Jumps:**

Only the first true condition's jump executes:

```bard
:: RoutePlayer
@if score >= 90:
-> GradeA
@elif score >= 80:
-> GradeB
@elif score >= 70:
-> GradeC
@else:
-> GradeF
@endif
```

With `score = 85`, only `-> GradeB` executes. The other branches are never evaluated.

**Content Flow Example:**

```bard
:: Start
~ health = 0

Checking your status...

@if health <= 0:
You feel weak...
-> Death
@endif

You're fine!  # This never renders if health <= 0

:: Death
You have died.
```

**Output when health = 0:**

```txt
Checking your status...

You feel weak...

You have died.
```

Notice:

- "Checking your status..." renders (before conditional)
- "You feel weak..." renders (inside true branch, before jump)
- Jump executes
- "You're fine!" never renders (after jump)
- "You have died." renders (from Death passage)

**Jump in Loops:**

When a jump is found inside a loop, the loop exits immediately:

```bard
:: Search
~ numbers = [1, 2, 3, 4, 5]

Searching for 3...

@for n in numbers:
Checking {n}
@if n == 3:
-> Found
@endif
@endfor

Not found.

:: Found
Found it!
```

**Output:**

```txt
Searching for 3...

Checking 1
Checking 2
Checking 3
Found it!
```

Notice: Loop processes 1, 2, 3, then exits. Never checks 4 or 5. "Not found" never renders.

**Jump Loop Detection:**

Infinite jump loops are detected at runtime:

```bard
:: A
-> B

:: B
-> A
```

Raises: `RuntimeError: Jump loop detected: A -> B -> A`

**Compile-Time Validation:**

The compiler validates that all jump targets exist:

```bard
:: Start
-> NonExistentPassage
```

Raises: `ValueError: Jump target 'NonExistentPassage' not found (in passage 'Start')`

**Use Cases:**

- **Error handling:** Automatic jump to death/failure state
- **State routing:** Different paths based on variables
- **Cutscenes:** Auto-progress through narrative beats
- **Early exits:** Leave loops when conditions met
- **Scene transitions:** Seamless flow between passages
- **Game over conditions:** Immediate end when defeat detected

**Design Notes:**

- Jumps are immediate (like Ink's `->`, not like Twine's `<<goto>>`)
- Only ONE jump executes per passage rendering
- Render methods stay pure - navigation happens in `goto()`
- Jump following includes loop detection
- Content accumulation happens automatically

**Similar to:** Ink's divert (`->`) system

---

### Join Blocks (@join)

Create choices with inline content that merge back together. Similar to Ink's "gather" pattern but with explicit syntax.

**Syntax:**

```bard
+ [Choice text] -> @join
    Indented block content.
    ~ variable = value

@join
Content after all choices merge here.
```

**Basic Example:**

```bard
:: Start
What fruit do you want?

+ [Apple] -> @join
    You pick up the red apple.
    ~ fruit = "apple"

+ [Pear] -> @join
    You grab the green pear.
    ~ fruit = "pear"

@join
You chose the {fruit}. Delicious!
+ [Continue] -> End

:: End
Thanks for playing!
```

**How It Works:**

1. Choices with `-> @join` have indented block content below them
2. When a choice is selected, its block content renders
3. Variables set in the block persist after the merge
4. Execution continues from the `@join` marker
5. Choices after `@join` appear in the next "section"

**Multiple @join Markers (Sections):**

Each `@join` marker divides the passage into sections. Players progress through sections sequentially:

```bard
:: Tournament
Round 1: Attack or Defend?

+ [Attack] -> @join
    You strike fiercely!
    ~ damage = 10

+ [Defend] -> @join
    You raise your shield.
    ~ defense = 5

@join
Round 1 complete.
Round 2: Finish or Mercy?

+ [Finish them] -> @join
    A decisive blow!
    ~ victory = "brutal"

+ [Show mercy] -> @join
    You stay your hand.
    ~ victory = "merciful"

@join
The battle is over. You won with a {victory} victory.
+ [Continue] -> NextScene
```

**Mixed with Regular Choices:**

Regular choices exit the @join flow entirely:

```bard
:: Crossroads
You see something interesting.

+ [Investigate] -> @join
    You look closer...

+ [Leave immediately] -> OtherPlace

@join
After investigating, you continue.
+ [Done] -> End
```

If player chooses "Leave immediately", they go to OtherPlace. If they choose "Investigate", they see the block content and then "Done" appears.

**Works With:**

- **Conditional choices:** `+ {has_key} [Use key] -> @join`
- **One-time choices:** `* [One-time option] -> @join`
- **Hooks:** `@hook`/`@unhook` inside block content
- **Variables:** `~ var = value` in blocks
- **Undo/redo:** Section index included in snapshots

**Block Termination:**

Block content ends when the parser encounters:

- Another choice line (`+ [` or `* [`)
- The `@join` marker
- A new passage header (`::`)
- Block directives (`@if`, `@endif`, `@for`, `@endfor`, `@py`, `@endpy`)

**Rules:**

- `@join` is a reserved target name (cannot have a passage named "@join")
- Empty blocks are valid (choice just continues to @join)
- Block content must be indented more than the choice line
- Multiple @join markers create sequential sections
- Section index resets when re-entering a passage

---

### Previous Passage Target (@prev)

Navigate back to the previous passage. Useful for menus, inventory screens, side conversations, and any "go back to where I came from" pattern.

**Syntax:** `-> @prev`

```bard
:: Tavern
You're at the tavern.
+ [Open inventory] -> Inventory
+ [Talk to barkeep] -> Barkeep

:: Inventory
Your items:
- Sword
- Potion
+ [Close inventory] -> @prev   # Returns to Tavern!

:: Barkeep
The barkeep nods at you.
"What'll it be?"
+ [Ask about rumors] -> Rumors
+ [Never mind] -> @prev        # Returns to Tavern!

:: Rumors
"I heard there's trouble in the north..."
-> @prev                        # Auto-returns to Barkeep
```

**How It Works:**

1. The engine tracks the previous passage (the one you were at immediately before the current one)
2. When `@prev` is encountered as a jump or choice target, it resolves to that passage
3. The previous passage is updated after each navigation
4. Works with both choices (`+ [Text] -> @prev`) and immediate jumps (`-> @prev`)

**Rules:**

- `@prev` is a reserved target name (cannot have a passage named "@prev")
- At story start, there is no previous passage - using `@prev` will raise an error
- Tracks the *immediately previous* passage, not the last player decision point
- In jump chains (`A -> B -> C`), @prev from C goes to B (the last passage visited)
- Persists through save/load (saved in game state)
- Restored correctly with undo/redo (included in snapshots)

**Use Cases:**

- **Menus and screens:** Return to gameplay from inventory/settings/map
- **Side conversations:** Talk to an NPC, then return to the main scene
- **Shop interfaces:** Browse items and return to where you were
- **Information passages:** Read lore/help and go back
- **Cutscenes with choices:** "Ask a question" then return to main dialogue

**With Automatic Jumps:**

When passages automatically jump to other passages, @prev tracks each step:

```bard
:: Hub
+ [Enter shop] -> ShopWelcome

:: ShopWelcome
Welcome to the shop!
-> ShopMenu                     # Auto-jump to menu

:: ShopMenu
What would you like to buy?
+ [Go back] -> @prev            # Goes to ShopWelcome (not Hub)
```

**Error Handling:**

Using @prev when there is no previous passage raises a clear error:

```
ValueError: Cannot navigate to @prev: no previous passage exists.
This typically happens at the start of a story.
```

**Comparison with Undo:**

| Feature | @prev | Undo |
|---------|-------|------|
| **Navigates to** | Previous passage | Previous decision point |
| **Restores state** | No (state unchanged) | Yes (full state rollback) |
| **Use case** | "Go back" in UI | "Try a different choice" |
| **Tracks** | Every passage visited | Only when `choose()` is called |

---

### Tags (Custom Markup)

Mark text for special frontend treatment.

```bard
The spirits speak to you...

[!whisper]This is rendered as a whisper effect[/!whisper]

[!card-display animation=flip] The Fool [/!card-display]

[!dramatic delay=2s]A long silence.[/!dramatic]
```

**Rules:**

- Opening: `[!tagname attr=value]`
- Closing: `[/!tagname]`
- Attributes are optional
- Can be nested
- Compiled to structured data for React

### Includes

Split large stories across multiple files.

**Syntax:** `@include path/to/file.bard`

```bard
from models.card import Card

@include shared/card_mechanics.bard
@include clients/aria/session1.bard
@include clients/marcus/session1.bard

:: Start
Welcome to your desk.

+ [See Aria] -> Aria.Session1.Start
+ [See Marcus] -> Marcus.Session1.Start
```

**Rules:**

- Must appear after imports, before any passages
- Paths are relative to the including file
- Recursive: included files can include other files
- All passages are merged into single compiled output
- Duplicate passage names: last definition wins
- Circular includes are detected and error

**Benefits:**

- Organize large stories into manageable files
- Separate concerns (clients, mechanics, interpretations)
- Enable parallel development
- Better version control
- Reusable components across stories

**Example File Structure:**

```sh
stories/
├── main.bard                 # Entry point with @include directives
├── shared/
│   ├── card_mechanics.bard
│   └── reactions.bard
└── clients/
    ├── aria/
    │   ├── session1.bard
    │   └── session2.bard
    └── marcus/
        └── session1.bard
```

**Critical for:** Stories with multiple client paths, hub-and-spoke structures, or >1000 lines of content.

---

## Advanced Features (Post v1.0)

These are "nice to have" but not essential for first release.

### Scoped Sections

Group passages with shared state.

**Syntax:** `@section Name` ... `@endsection`

```bard
@section ClientAria.Session1

# Section-level setup (runs once when entering section)
@py:
client = load_client('aria')
session_state = {'trust': 50}
@endpy

:: Start
# Has access to client and session_state
Hello, {client.name}.

:: Reading
# Still has access
Your trust level: {session_state['trust']}

@endsection

# Outside the section - no access to section-level variables
:: MainMenu
Back at the main menu.
```

**Rules:**

- Opens with `@section Name`
- Closes with `@endsection`
- Setup code runs once when first entering section
- All passages between open/close share the section state
- Section state doesn't persist outside the section
- Can be nested (subsections)

**Benefits:**

- Group related passages with shared context
- Reduce boilerplate (don't repeat setup in every passage)
- Clear scope boundaries
- Easier to reason about state

**Use Cases:**

- Client sessions with shared client object
- Story chapters with chapter-specific state
- Mini-games with temporary mechanics
- Tutorial sections with special rules

**Status:** Consider after v1.0 if pain point emerges

---

### Sequences/Cycles

Ink-style cycling text.

```bard
{sequence(visit_count('Tavern'), [ "The tavern is bustling.", "The tavern is quieter now.", "The tavern is nearly empty." ])}
````

**Status:** Unplanned — can be achieved with `_visits` and `@if`/`@elif` blocks.

---

## Compiled Format

Bardic compiles `.bard` files to JSON for runtime execution.

### Structure

```json
{
  "version": "0.1.0",
  "initial_passage": "Start",
  "passages": {
    "PassageName": {
      "id": "PassageName",
      "params": {},
      "content": [...],
      "choices": [...],
      "execute": [...]
    }
  }
}
````

### Content Items

```json
{
  "type": "text",
  "value": "Regular text"
}

{
  "type": "expression",
  "code": "variable_name"
}

{
  "type": "conditional",
  "branches": [
    {
      "condition": "health > 50",
      "content": [...]
    }
  ]
}

{
  "type": "for_loop",
  "var": "item",
  "collection": "inventory",
  "content": [...]
}

{
  "type": "tagged_text",
  "tag": "whisper",
  "attributes": {},
  "content": "..."
}

{
  "type": "render",
  "component": "render_spread",
  "args": {...}
}
```

---

## Runtime Behavior

### State Management

**Global State:**

- Persists across passages
- Variables set with `~` are global
- Stored in `engine.state`

**Passage Parameters:**

- Temporary scope
- Passed between passages
- Don't persist unless explicitly saved

**Python Context:**

- Imported modules available everywhere
- Functions/services provided by FastAPI
- Can call any Python code

### Execution Order (Per Passage)

1. Load passage
2. Execute all `@py:` blocks and `~` assignments in order
3. Render content (evaluate expressions, conditionals, loops)
4. Filter available choices (check conditions)
5. Return output to frontend

### Navigation

- Choices navigate via `target` passage ID
- Immediate diverts (`->`) jump without player input
- Can pass parameters during navigation
- Engine tracks current passage ID

### Undo/Redo

Players can rewind and replay their choices. The engine maintains undo and redo stacks.

**Engine API:**

```python
# Check if undo/redo is available
if engine.can_undo():
    engine.undo()  # Go back one choice

if engine.can_redo():
    engine.redo()  # Replay undone choice
```

**How It Works:**

1. Before each `choose()` call, a snapshot is taken
2. Snapshot captures: current passage, all variables, used choices, hooks, @join section index
3. `undo()` restores the previous snapshot and re-renders
4. `redo()` restores the undone state (if no new choices were made)
5. Making a new choice after undo clears the redo stack (timeline branching)

**GameSnapshot Contents:**

```python
@dataclass
class GameSnapshot:
    current_passage: str
    state: dict[str, Any]        # All game variables
    used_choices: set            # One-time choices used
    hooks: dict[str, list[str]]  # Registered hooks
    join_section_index: dict     # @join section tracking
```

**Stack Configuration:**

```python
# Default: 50 undo levels
engine = BardEngine(story)
engine.undo_stack.maxlen  # 50
```

**Browser Template:**

The browser bundle (`bardic bundle`) includes buttons in the header for undo/redo. Button states update automatically based on `can_undo()` / `can_redo()`.

**Integration Example:**

```python
@app.post("/story/undo")
async def undo_choice(session_id: str):
    engine = sessions[session_id]
    if engine.can_undo():
        engine.undo()
        return {"success": True, "output": engine.current()}
    return {"success": False, "message": "Nothing to undo"}
```

**Rules:**

- Snapshots taken BEFORE navigation (so undo returns to choice point)
- Deep copies of state prevent reference issues
- New choice after undo clears redo stack
- Stack is bounded (default 50) to prevent memory issues
- Hook state and @join section index included in snapshots

---

## Integration

### FastAPI Backend

```python
from bardic import BardEngine

@app.post("/story/advance")
async def advance_story(session_id: str, choice_index: int):
    engine = sessions[session_id]

    # Navigate based on choice
    output = engine.choose(choice_index)

    return {
        'content': output.content,
        'choices': output.choices,
        'render_directives': output.render_directives,
        'state': engine.state
    }
```

### React Frontend

```jsx
function StoryView({ passageData }) {
  return (
    <div>
      {/* Custom components */}
      {passageData.render_directives.map(d =>
        <ComponentRegistry name={d.component} props={d.props} />
      )}

      {/* Content with markdown and tags */}
      <ContentRenderer content={passageData.content} />

      {/* Choices */}
      <Choices choices={passageData.choices} />
    </div>
  );
}
```

---

## Examples of Stories

### Simple Story

```bard
:: Start
You wake up in a mysterious room.

+ [Look around] -> Examine
+ [Try the door] -> Door

:: Examine
The room is bare except for a small window.

+ [Go to window] -> Window
+ [Try the door] -> Door

:: Door
The door is locked.

+ [Look around] -> Examine

:: Window
Through the window, you see freedom.
```

### With Imports and Includes

```bard
# main.bard

from models.card import Card
from services.tarot import TarotService

@include shared/card_mechanics.bard
@include shared/reactions.bard
@include clients/aria/session1.bard

:: Start
Welcome to your reader's desk.

+ [See Aria] -> Aria.Session1.Start
```

### With Python Objects (Tarot Game)

```bard
from services.tarot import TarotService
from models.card import Card

@include shared/card_mechanics.bard

:: DrawCards
@py:
# Draw random cards
cards = tarot_service.draw_from_pool(
    pool='major_arcana',
    count=3,
    exclude=client.cards_seen
)

# Set positions
cards[0].in_position('past')
cards[1].in_position('present')
cards[2].in_position('future')

# Random reversals
for card in cards:
    if chance(0.3):
        card.is_reversed = True
@endpy

You draw three cards from the deck...

@render render_spread(cards, layout='three_card')

**Past:** {cards[0].get_display_name()}
{cards[0].position_meaning}

**Present:** {cards[1].get_display_name()}
{cards[1].position_meaning}

**Future:** {cards[2].get_display_name()}
{cards[2].position_meaning}

+ [Interpret traditionally] -> InterpretTraditional(cards=cards)
+ [Use intuition] -> InterpretIntuitive(cards=cards)
+ {reader_stats.shadow_work_unlocked} [Shadow work] -> ShadowWork(cards=cards)
```

---

## Non-Goals

Things Bardic intentionally does NOT do:

- Desktop app packaging (web-native only)
- Built-in graphics/audio system (use React/HTML5)
- Visual editor (code-first approach, but has VSCode IDE graph node navigator)
- Multiplayer/networking (handle in your backend)

These can be built using Bardic + your Python code, but are not built-in features.

---

## Contributing

Bardic is open to contributions. Features should solve real problems actually encountered in production, not hypothetical ones.

**Philosophy:** Build for real needs, not "just in case."

---

Last updated: March 2026
