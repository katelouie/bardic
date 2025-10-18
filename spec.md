# Bardic Language Specification v1.0

**Status:** Living Document (Updated as features are implemented)
**Target Completion:** v1.0 by Week 8
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
| `@section` / `@endsection` | Scoped section (future) | `@section Name` |
| `@ render` | Render directive | `@ render_spread(cards)` |
| `<<py>>` | Python code block | `<<py\ncode\n>>` |
| `<<if>>` | Conditional | `<<if condition>>` |
| `<<for>>` | Loop | `<<for item in list>>` |
| `~` | Variable assignment | `~ health = 100` |
| `{}` | Expression | `{variable}` or `{function()}` or `{var:.2f}` |
| `+` | Sticky choice | `+ [Text] -> Target` |
| `*` | One-time choice | `* [Text] -> Target` |
| `->` | Immediate jump | `-> Target` |
| `#` | Comment | `# This is a comment` |
| `[!tag]` | Custom markup | `[!whisper]text[/!whisper]` |

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

**Status:** ✅ Implemented (Week 1)

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

**Status:** ✅ Implemented (Week 2, Session 6)

---

### Text Content

Regular text is rendered as-is. Markdown is supported.

```bard
:: Example This is regular text.

This is **bold** and _italic_.

- Bullet list
- Another item
```

**Whitespace Rules (Like Ink):**

- Single newline = space (flow together)
- Double newline = paragraph break
- Logic blocks produce no whitespace
- Leading/trailing whitespace trimmed

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

**Status:**

- Basic text: ✅ Implemented (Week 1)
- Markdown: 📅 Week 5
- Whitespace perfection: 📅 Week 6

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

**Status:**

- Basic choices: ✅ Implemented (Week 1)
- Conditional: ✅ Implemented (Week 1)
- One-time (*): ✅ Implemented (Week 3)
- Parameters: 📅 Week 4

---

### Variables

Store and manipulate state.

```bard
~ variable_name = value
```

**Supported Types:**

- Numbers: `~ health = 100`
- Strings: `~ name = "Hero"`
- Booleans: `~ has_key = True`
- Lists: `~ inventory = []`
- Objects: `~ card = Card()`

**Display Variables:**

```bard
You have {health} health. Your name is {name}.
```

**Format Specifiers:**

Use Python's format specification mini-language to control how values are displayed:

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

**Expressions:**

```bard
~ health = health - 10
~ total = (gold * 2) + bonus
```

**Status:** ✅ Implemented (Week 2, Session 6)

---

### Python Code Blocks

Execute multi-line Python code in passages.

**Syntax:** `<<py>> ... >>`

```bard
:: Example
<<py
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
>>
Results: {total} (average: {average:.1f})
Outcome: {outcome}
````

**Rules:**

- Opens with `<<py`
- Closes with `>>`
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
<<py
result = roll_dice(20)
greeting = greet("Hero")
>>
```

**Error Handling:**

- Syntax errors show the problematic line
- Runtime errors show full traceback
- Undefined variables list available variables

**Status:** ✅ Implemented (Week 3, Session 7)

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
  - Imported modules (from `<<py>>` blocks)

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

**Status:** ✅ Implemented (Week 3, Session 8)

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

**Status:** ✅ Implemented (Week 2, Session 6)

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

**Status:** ✅ Implemented (Week 3, Session 9)

---

### Conditionals

Branch content based on conditions.

```bard
<<if condition>>
Content if true.
<<elif other_condition>>
Content if other is true.
<<else>>
Default content.
<<endif>>
```

**Examples:**

```bard
<<if health > 75>>
You feel strong and healthy.
<<elif health > 25>>
You're wounded but standing.
<<else>>
You're barely conscious.
<<endif>>
```

**Rules:**

- Conditions are Python expressions
- Can access all variables and functions
- Can be nested
- Produces no whitespace itself (only renders chosen branch)
- Must close with `<<endif>>`
- Multiple `<<elif>>` branches allowed
- `<<else>>` is optional
- First true condition wins (like Python if/elif/else)

**Complex Conditions:**

```bard
<<if gold > 100 and trust > 50>>
Wealthy and trusted!
<<elif gold > 50 or has_key>>
Have resources.
<<elif not has_key and gold < 20>>
Poor and locked out.
<<else>>
Getting by.
<<endif>>
```

**With Objects:**

```bard
<<if client.trust_level > 75>>
Deeply trusted.
<<elif any(card.is_major_arcana() for card in cards)>>
Major arcana drawn!
<<else>>
Standard reading.
<<endif>>
```

**Nested Conditionals:**

```bard
<<if player_class == "warrior">>
  <<if health > 75>>
  Strong warrior!
  <<else>>
  Wounded warrior.
  <<endif>>
<<else>>
  Not a warrior.
<<endif>>
```

**Error Handling:**

- Failed conditions skip that branch
- Warnings printed to console
- Story continues with next branch
- Missing `<<endif>>` causes parse error

**Status:** ✅ Implemented (Week 3, Session 10)

---

### Loops

Iterate over collections to generate dynamic content.

```bard
<<for variable in collection>>
  content using {variable}
<<endfor>>
```

**Examples:**

```bard
# Simple list
<<for item in items>>
- {item}
<<endfor>>

# Range
<<for i in range(5)>>
Number {i}
<<endfor>>

# Objects
<<for card in cards>>
{card.name}: {card.get_display_name()}
<<endfor>>

# Enumerate
<<for i, item in enumerate(items)>>
{i+1}. {item}
<<endfor>>

# With start index
<<for i, item in enumerate(items, 5)>>
{i}. {item}
<<endfor>>
```

~~**Inline loops:**~~

```bard
Cards drawn: <<for card in cards>>{card.name}, <<endfor>>
```

- Opens with `<<for variable in collection>>`
- Closes with `<<endfor>>`
- Variable available in expressions within loop
- Collection evaluated once before loop starts
- Can iterate over: lists, tuples, ranges, dicts, etc.
- Supports tuple unpacking (enumerate, zip, etc.)
- Can be nested
- Loop variable is temporary (doesn't persist after loop)

**Nested Loops:**

```bard
<<for suit in suits>>
  Suit: {suit}
  <<for rank in ranks>>
    {rank} of {suit}
  <<endfor>>
<<endfor>>
```

**With Conditionals:**

```bard
<<for item in inventory>>
  <<if item.power > 10>>
  - {item.name} (powerful!)
  <<endif>>
<<endfor>>
```

**Tuple Unpacking:**

```bard
<<for key, value in items.items()>>
{key}: {value}
<<endfor>>

<<for i, card in enumerate(cards)>>
Card {i+1}: {card.name}
<<endfor>>
```

**Status:** ✅ Implemented (Week 3, Session 11)

---

### Comments

Document your story.

```bard
# This is a comment

Text content. # Inline comment

- [Choice] -> Target # This choice goes to Target
```

**Rules:**

- Start with `#`
- Extend to end of line
- Ignored by compiler
- Not rendered in output

**Status:** 📅 Week 5

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

**Status:** ✅ Implemented (Week 3, Session 9.5)

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

- ✅ Clean separation of metadata from story content
- ✅ Consistent place for story information
- ✅ Used automatically by save/load system
- ✅ No pollution of game state
- ✅ Easy to read and edit
- ✅ Optional - stories work fine without it

**Status:** ✅ Implemented (Session 12)

---

### Passage Parameters

Pass data between passages like function arguments.

```bard
:: DrawCards(count=3, spread_type='three_card') <<py cards = deck.draw(count) layout = SPREADS[spread_type]

Drawing {count} cards...

- [Continue] -> Interpret(cards=cards, style='traditional')

:: Interpret(cards=None, style='traditional') <<if cards is None>> Error: No cards provided! -> Start <<endif>>

Interpreting with {style} approach...
```

**Rules:**

- Parameters defined in passage header
- Can have default values
- Passed when navigating: `-> Target(param=value)`
- Temporary scope (don't persist unless assigned to global state)

**Status:** 📅 Week 4

---

### Render Directives

**Status:** ✅ Implemented (Week 4)

Tell the frontend to handle custom presentation logic. Render directives emit structured data that your runtime interprets - whether that's rendering React components, instantiating Unity GameObjects, or formatting terminal output.

#### Concept

Bardic stories run in a **backend engine** (Python) that produces **structured output** for a **frontend runtime** (React, Unity, CLI, etc.). Most content is just text, but sometimes you need custom UI elements:

- **Card spread visualization** - Show tarot cards in specific layouts
- **Character portraits** - Display character art with expressions
- **Mini-games** - Embed interactive elements
- **Data visualizations** - Charts, graphs, dashboards
- **Custom animations** - Trigger specific visual effects

**Render directives** let you specify these custom elements directly in your story, without breaking out of the narrative flow.

**Philosophy:** Bardic doesn't know how to render cards or portraits - your frontend does. Bardic just provides the data in a structured format your frontend can consume.

#### Basic Syntax

**Format:** `@render directive_name(args)`

```bard
@render card_spread(cards, layout='celtic_cross')
@render character_portrait(client, emotion='worried')
@render mini_game(game_type='dice', difficulty=3)
```

**Rules:**

- Start with `@render` followed by space
- Function-call syntax with Python expressions as arguments
- Arguments can be variables, literals, or complex expressions
- Not rendered as text - produces no output in story content
- Compiled to structured data sent to frontend
- Can appear anywhere in passage content
- Multiple directives per passage allowed
- Works in conditionals, loops, and regular content

**Important:** Directives are **declarative**, not imperative. You're saying "here's data about a card spread," not "render this component." The frontend decides how to interpret it.

---

#### Examples

##### Simple Directive

```bard
:: DrawCards
~ cards = [Card("The Fool", 0), Card("The Magician", 1)]

You draw two cards from the deck...

@render card_spread(cards, layout='two_card')

The first card is {cards[0].name}.
```

**Compiled output:**

```json
{
  "render_directives": [
    {
      "type": "render_directive",
      "name": "card_spread",
      "mode": "evaluated",
      "data": {
        "cards": [
          {"name": "The Fool", "number": 0},
          {"name": "The Magician", "number": 1}
        ],
        "layout": "two_card"
      }
    }
  ]
}
```

##### Multiple Directives

```bard
:: Reading
@render card_spread(cards, layout='three_card', animation='flip')

The cards reveal:
{cards[0].name}, {cards[1].name}, {cards[2].name}

@render interpretation_panel(cards, style='traditional')

Do you understand their meaning?
```

Each directive is collected and returned in the `render_directives` list.

##### With Conditionals

```bard
:: ShowReaction
<<if client.trust > 75>>
@render character_portrait(client, emotion='happy', size='large')
<<elif client.trust > 25>>
@render character_portrait(client, emotion='neutral', size='medium')
<<else>>
@render character_portrait(client, emotion='worried', size='small')
<<endif>>

{client.name}'s reaction speaks volumes.
```

Only the directive from the true branch is collected.

##### In Loops

```bard
:: DisplayDeck
<<for card in hand>>
@render card_detail(card, position=loop.index, interactive=True)
<<endfor>>

Your hand is complete.
```

One directive is emitted per loop iteration. All are collected.

##### Complex Arguments

```bard
:: AdvancedReading
~ interpretation = analyze_spread(cards, client.past_readings)
~ confidence = calculate_confidence(cards)

@render spread_visualization(
    cards=cards,
    layout='celtic_cross',
    highlights=[c for c in cards if c.is_major_arcana()],
    metadata={
        'confidence': confidence,
        'timestamp': current_time(),
        'reader_notes': interpretation.notes
    }
)
```

Arguments can be any valid Python expression.

---

#### Framework Hints (Optional)

**Syntax:** `@render:framework directive_name(args)`

Tell Bardic to optimize the data structure for a specific framework. This is **optional** - the default format works for any runtime.

```bard
@render:react card_spread(cards, layout='celtic_cross')
@render:unity spawn_cards(cards, transform='hand')
@render:godot display_cards(cards, scene='CardLayout')
```

**When to use framework hints:**

- You want React-specific optimizations (PascalCase component names, unique keys)
- You're building for multiple platforms and want framework-specific data shapes
- Your frontend code expects a particular structure

**When NOT to use framework hints:**

- You only have one frontend (just use the default format)
- You control both backend and frontend (customize as needed)
- You want maximum flexibility (default format is most generic)

##### React Framework Hint

**Syntax:** `@render:react directive_name(args)`

```bard
@render:react card_spread(cards, layout='celtic_cross')
```

**Additional fields in output:**

```json
{
  "type": "render_directive",
  "name": "card_spread",
  "mode": "evaluated",
  "data": {
    "cards": [...],
    "layout": "celtic_cross"
  },
  "framework": "react",
  "react": {
    "componentName": "CardSpread",
    "key": "card_spread_a4b3c2d1",
    "props": {
      "cards": [...],
      "layout": "celtic_cross"
    }
  }
}
```

**React benefits:**

- `componentName`: Suggested component name in PascalCase
- `key`: Unique key for list rendering
- `props`: Arguments formatted as React props

**Usage in React:**

```jsx
const componentRegistry = {
  CardSpread: CardSpreadComponent,
  CharacterPortrait: CharacterPortraitComponent,
  // ... other components
};

{passage.render_directives.map((directive, i) => {
  if (directive.react) {
    const Component = componentRegistry[directive.react.componentName];
    return <Component key={directive.react.key} {...directive.react.props} />;
  }
  // Fallback for directives without React hint
  const Component = componentRegistry[directive.name];
  return <Component key={i} {...directive.data} />;
})}
```

##### Future Framework Hints

**Unity (not yet implemented):**

```bard
@render:unity spawn_cards(cards, transform='hand', prefab='CardPrefab')
```

Might compile to:

```json
{
  "unity": {
    "prefab": "CardPrefab",
    "instanceId": "cards_a4b3c2d1",
    "args": {
      "cards": [...],
      "transform": "hand"
    }
  }
}
```

**Godot (not yet implemented):**

```bard
@render:godot display_scene(cards, scene_path='res://CardLayout.tscn')
```

Might compile to:

```json
{
  "godot": {
    "scenePath": "res://CardLayout.tscn",
    "instanceId": "scene_a4b3c2d1",
    "args": {
      "cards": [...]
    }
  }
}
```

**Want to add a framework hint?** See "Extending Bardic" below.

---

#### Compilation Modes

Bardic can compile render directives in two modes:

##### Evaluated Mode (Default)

**Configuration:** `BardEngine(story, evaluate_directives=True)`

Python expressions in directive arguments are **evaluated at runtime** in the backend. The frontend receives fully evaluated data.

```bard
@render card_spread(cards, layout='celtic_cross')
```

**Backend evaluates:** `cards` variable, `'celtic_cross'` literal

**Frontend receives:**

```json
{
  "name": "card_spread",
  "mode": "evaluated",
  "data": {
    "cards": [
      {"name": "The Fool", "number": 0},
      {"name": "The Magician", "number": 1}
    ],
    "layout": "celtic_cross"
  }
}
```

**Use when:**

- ✅ Standard use case for most apps
- ✅ Backend has full game logic and state
- ✅ Frontend just displays data
- ✅ You want type-safe, validated data

##### Raw Mode (Advanced)

**Configuration:** `BardEngine(story, evaluate_directives=False)`

Expressions are **NOT evaluated**. The frontend receives raw expressions and must evaluate them.

```bard
@render card_spread(cards, layout='celtic_cross')
```

**Backend does NOT evaluate!**

**Frontend receives:**

```json
{
  "name": "card_spread",
  "mode": "raw",
  "raw_args": "cards, layout='celtic_cross'",
  "state_snapshot": {
    "cards": [...],
    "layout": "...",
    "health": 100
  }
}
```

**Frontend must:**

1. Parse the expression
2. Use `state_snapshot` to resolve variables
3. Evaluate the expression in JavaScript

**Use when:**

- ⚠️ You want client-side evaluation for some reason
- ⚠️ You need the exact expression string
- ⚠️ Building a dev tool that shows raw expressions

**Most users should use evaluated mode.**

#### Behavior with Story Features

##### With Jumps

Directives from all passages in a jump chain are collected:

```bard
:: Start
@render title_screen(game_title)
-> Intro

:: Intro
@render fade_in()

The game begins...
```

**Output combines both:**

```json
{
  "content": "The game begins...",
  "render_directives": [
    {"name": "title_screen", "data": {...}},
    {"name": "fade_in", "data": {}}
  ]
}
```

##### With Conditionals (Again)

Only directives from the true branch are collected:

```bard
<<if health > 50>>
@render health_bar(health, color='green')
<<else>>
@render health_bar(health, color='red')
<<endif>>
```

If `health = 75`, only the green health bar directive is emitted.

##### With Loops

One directive per iteration:

```bard
<<for card in cards>>
@render card_icon(card, index=loop.index)
<<endfor>>
```

If `cards` has 3 items, you get 3 directives.

---

#### Frontend Integration

##### Generic JavaScript/TypeScript

```typescript
interface RenderDirective {
  type: "render_directive";
  name: string;
  mode: "evaluated" | "raw" | "error";
  data?: Record<string, any>;
  framework?: string;
  react?: {
    componentName: string;
    key: string;
    props: Record<string, any>;
  };
  error?: string;
  raw_args?: string;
  state_snapshot?: Record<string, any>;
}

// Handle directives
passageData.render_directives.forEach((directive: RenderDirective) => {
  switch (directive.name) {
    case "card_spread":
      renderCardSpread(directive.data.cards, directive.data.layout);
      break;
    case "character_portrait":
      renderPortrait(directive.data.character, directive.data.emotion);
      break;
    default:
      console.warn(`Unknown directive: ${directive.name}`);
  }
});
```

##### React

**With React hint:**

```jsx
const componentRegistry = {
  CardSpread: CardSpreadComponent,
  CharacterPortrait: CharacterPortraitComponent,
  InterpretationPanel: InterpretationPanelComponent,
};

function PassageRenderer({ passage }) {
  return (
    <div>
      {/* Regular content */}
      <ReactMarkdown>{passage.content}</ReactMarkdown>

      {/* Render directives */}
      {passage.render_directives.map((directive) => {
        const Component = componentRegistry[directive.react.componentName];
        if (!Component) {
          console.warn(`Component not found: ${directive.react.componentName}`);
          return null;
        }
        return (
          <Component
            key={directive.react.key}
            {...directive.react.props}
          />
        );
      })}

      {/* Choices */}
      <ChoiceButtons choices={passage.choices} />
    </div>
  );
}
```

**Without React hint (generic):**

```jsx
function PassageRenderer({ passage }) {
  return (
    <div>
      <ReactMarkdown>{passage.content}</ReactMarkdown>

      {passage.render_directives.map((directive, i) => {
        const Component = componentRegistry[directive.name];
        if (!Component) return null;
        return <Component key={i} {...directive.data} />;
      })}

      <ChoiceButtons choices={passage.choices} />
    </div>
  );
}
```

##### Unity (Hypothetical)

```csharp
public class BardicRuntime : MonoBehaviour {
    [SerializeField] private GameObject cardPrefab;
    [SerializeField] private Transform cardParent;

    void HandleRenderDirective(RenderDirective directive) {
        switch (directive.name) {
            case "spawn_cards":
                SpawnCards(
                    directive.data["cards"] as List<Card>,
                    directive.data["transform"] as string
                );
                break;

            case "display_effect":
                PlayEffect(
                    directive.data["effect_name"] as string,
                    directive.data["duration"] as float
                );
                break;
        }
    }

    void SpawnCards(List<Card> cards, string transformName) {
        Transform target = transform.Find(transformName);
        foreach (var card in cards) {
            var go = Instantiate(cardPrefab, target);
            go.GetComponent<CardDisplay>().SetCard(card);
        }
    }
}
```

##### CLI/Terminal (Text Only)

```python
def render_directive_as_text(directive: dict) -> str:
    """Render directives as ASCII art for terminal"""

    if directive['name'] == 'card_spread':
        cards = directive['data']['cards']
        layout = directive['data']['layout']

        if layout == 'three_card':
            return format_three_card_ascii(cards)
        elif layout == 'celtic_cross':
            return format_celtic_cross_ascii(cards)

    elif directive['name'] == 'character_portrait':
        char = directive['data']['character']
        emotion = directive['data']['emotion']

        return f"""
        ╔══════════════╗
        ║ {char['name']:^12} ║
        ║ [{emotion:^10}] ║
        ╚══════════════╝
        """

    return ""
```

---

#### Error Handling

##### Evaluation Errors

If evaluation fails in evaluated mode, you get an error directive:

```bard
@render card_spread(undefined_variable, layout='bad')
```

**Output:**

```json
{
  "type": "render_directive",
  "name": "card_spread",
  "mode": "error",
  "error": "name 'undefined_variable' is not defined",
  "raw_args": "undefined_variable, layout='bad'"
}
```

**Frontend handling:**

```jsx
if (directive.mode === "error") {
  console.error(`Render directive failed: ${directive.error}`);
  return null; // Or show error UI
}
```

##### Missing Components

If your component registry doesn't have a component:

```jsx
const Component = componentRegistry[directive.name];
if (!Component) {
  console.warn(`Component '${directive.name}' not found`);
  return <div className="missing-component">
    ⚠️ Component not implemented: {directive.name}
  </div>;
}
```

---

#### Extending Bardic (Adding Framework Hints)

Want to add support for your own framework? Here's how:

**1. Create a processor function:**

```python
# In your backend code
def _process_for_my_framework(self, component_name: str, args: dict) -> dict:
    """Format directive data for MyFramework."""
    return {
        "widget_name": component_name.upper(),
        "instance_id": f"{component_name}_{uuid.uuid4().hex[:8]}",
        "parameters": args
    }
```

**2. Register it with the engine:**

```python
engine = BardEngine(story, context=context)
engine.framework_processors['myframework'] = engine._process_for_my_framework
```

**3. Use it in stories:**

```bard
@render:myframework my_widget(param1=value1, param2=value2)
```

**4. Handle it in your frontend:**

```python
for directive in passage.render_directives:
    if 'myframework' in directive:
        my_framework_data = directive['myframework']
        widget_name = my_framework_data['widget_name']
        parameters = my_framework_data['parameters']
        # Render in your framework
```

#### Design Philosophy

##### Why Not Just Use Python Blocks?

**You could do this:**

```bard
<<py
component_data = {
    'type': 'card_spread',
    'cards': cards,
    'layout': 'celtic_cross'
}
components.append(component_data)
>>
```

**But directives are better because:**

- ✅ **Declarative** - Say what you want, not how to build it
- ✅ **Compiled** - Validated at compile time, not runtime
- ✅ **Visible** - Stand out in story text
- ✅ **Framework-agnostic** - Frontend-specific details in one place
- ✅ **Traceable** - Easy to find all custom UI in your story

##### Why "Render" and Not "Component" or "Emit"?

**Considered names:**

- `@component` - Too React-specific
- `@emit` - Sounds like event system
- `@custom` - Too vague
- `@visual` - Not always visual (could be audio, haptics)
- `@render` - **Familiar** (React, game engines), **short**, **directional**

**"Render" is framework-agnostic in practice:**

- React devs: "Render a component"
- Unity devs: "Render objects"
- CLI devs: "Render formatted output"
- Everyone understands: "Display this data somehow"

With good docs (like this!), the term works for all platforms.

#### Use Cases

##### Tarot Reading Game

```bard
:: DrawCards
~ cards = draw_tarot_cards(3)

You draw three cards...

@render:react card_spread(
    cards=cards,
    layout='past_present_future',
    animation='flip',
    interactive=True
)

+ [Interpret] -> Interpret
```

##### Character Dialogue

```bard
:: Conversation
@render:react character_portrait(
    character=aria,
    emotion='worried',
    position='left'
)

"I don't understand the cards," she says nervously.

+ [Reassure her] -> Reassure
+ [Be direct] -> Direct
```

##### Data Visualization

```bard
:: Statistics
~ client_data = analyze_all_sessions()

Here's how your clients are doing:

@render:react progress_chart(
    data=client_data,
    type='bar',
    labels=['Trust', 'Satisfaction', 'Growth']
)

+ [Continue] -> Next
```

##### Mini-Games

```bard
:: DiceGame
Time to roll for destiny!

@render:react dice_roller(
    num_dice=3,
    sides=6,
    on_result='handle_dice_result',
    animated=True
)

+ [Continue] -> AfterRoll
```

#### Common Patterns

##### Progressive Disclosure

Show UI elements only when relevant:

```bard
:: Reading
You draw the cards.

<<if show_tutorial>>
@render:react tutorial_overlay(step='card_spread')
<<endif>>

@render:react card_spread(cards, layout='three_card')
```

##### Dynamic Layouts

```bard
:: DrawCards
~ layout = choose_layout_for_question(question_type)

@render:react card_spread(cards, layout=layout)
```

##### Conditional Rendering

```bard
:: ClientReaction
<<if trust > 75>>
@render:react character_portrait(client, emotion='happy', size='large')
<<elif trust > 25>>
@render:react character_portrait(client, emotion='neutral', size='medium')
<<else>>
@render:react character_portrait(client, emotion='worried', size='small')
<<endif>>
```

##### Combining Multiple Directives

```bard
:: ComplexScene
@render:react background(scene='mystic_shop', time='evening')
@render:react character_portrait(client, position='left')
@render:react card_spread(cards, position='center')
@render:react mood_lighting(intensity=0.7, color='purple')

The scene is set for the reading.
```

#### Limitations

**Current limitations:**

- ❌ No inline directives (`Text with @render inline(x) here`)
- ❌ No directive nesting (`@render outer(@render inner())`)
- ❌ No conditional directive expressions (`@render {var if cond else other}`)
- ❌ Can't return values to story (`~ result = @render thing()`)

**These are intentional design decisions.** Render directives are **one-way**: story → frontend. They produce UI, not story data.

**If you need computed values:**

```bard
# ✅ Do this:
<<py
result = compute_something(args)
>>
@render display(result)

# ❌ Not this:
~ result = @render compute(args)  # Won't work
```

#### Troubleshooting

##### Directive not appearing in output?

**Check:**

1. Is it inside a false conditional?
2. Is the passage being jumped over?
3. Is there a Python error? (Check console/logs)
4. Is `evaluate_directives=False` and frontend not handling raw mode?

##### "Unknown directive" warnings in frontend?

**Check:**

1. Is the component registered in your component registry?
2. Does the name match exactly? (case-sensitive)
3. Did you rebuild your frontend after adding the component?

##### Props not passing correctly?

**Check:**

1. Variable names in Bardic vs React props
2. Data types (arrays vs objects)
3. Framework hint format (`directive.react.props` vs `directive.data`)

##### Directives rendering as text?

**Check:**

1. Frontend is actually handling `render_directives` array
2. Not just displaying `passage.content` alone
3. Component registry configured correctly

#### Complete Example

**Story file (`tarot_reading.bard`):**

```bard
from models.card import Card
from services.tarot import TarotService

:: Start
~ client = load_client('aria')
~ tarot = TarotService()

Welcome back to your desk. {client.name} has arrived.

@render:react character_portrait(client, emotion='neutral', position='left')

She sits down nervously.

+ [Begin reading] -> DrawCards

:: DrawCards
~ cards = tarot.draw_cards(3, pool='major_arcana')

You shuffle the deck and draw three cards...

@render:react card_spread(
    cards=cards,
    layout='past_present_future',
    animation='flip',
    interactive=False
)

**Past:** {cards[0].name}
**Present:** {cards[1].name}
**Future:** {cards[2].name}

+ [Interpret] -> Interpret

:: Interpret
~ interpretation = tarot.interpret(cards, client)

@render:react interpretation_panel(
    interpretation=interpretation,
    confidence=0.85,
    style='traditional'
)

You explain the meaning...

@render:react character_portrait(
    client,
    emotion='enlightened',
    position='left'
)

She seems to understand.

+ [End session] -> End

:: End
@render:react session_complete(client, cards)

Session complete. Thank you!
```

**Backend (`main.py`):**

```python
from fastapi import FastAPI
from bardic import BardEngine
import json

app = FastAPI()

@app.post("/story/start")
async def start_story(story_id: str, session_id: str):
    with open(f'stories/{story_id}.json') as f:
        story = json.load(f)

    context = {
        'load_client': load_client,
        'TarotService': TarotService,
    }

    engine = BardEngine(story, context=context)
    output = engine.current()

    return {
        'content': output.content,
        'choices': output.choices,
        'render_directives': output.render_directives
    }
```

**Frontend (`App.jsx`):**

```jsx
import CardSpread from './components/CardSpread';
import CharacterPortrait from './components/CharacterPortrait';
import InterpretationPanel from './components/InterpretationPanel';
import SessionComplete from './components/SessionComplete';

const componentRegistry = {
  CardSpread,
  CharacterPortrait,
  InterpretationPanel,
  SessionComplete,
};

function PassageView({ passage }) {
  return (
    <div className="passage">
      {/* Render custom components */}
      {passage.render_directives?.map((directive) => {
        const Component = componentRegistry[directive.react.componentName];
        return Component ? (
          <Component
            key={directive.react.key}
            {...directive.react.props}
          />
        ) : null;
      })}

      {/* Render text content */}
      <ReactMarkdown>{passage.content}</ReactMarkdown>

      {/* Render choices */}
      <ChoiceButtons choices={passage.choices} />
    </div>
  );
}
```

**Output:** A fully interactive tarot reading with custom card visualizations, animated character portraits, and rich interpretation panels - all defined in the story file!

**Status:** ✅ Fully Implemented (Week 4)

### Immediate Jumps (Diverts)

Navigate to another passage without a choice. Like Ink's `->` divert.

**Syntax:** `-> PassageName`

```bard
:: CheckHealth
<<if health <= 0>>
You collapse to the ground...
-> Death
<<endif>>

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
- Can be conditional (inside `<<if>>` blocks)
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
<<if health <= 0>>
You collapse...
-> Death
<<elif health < 50>>
You're wounded.
-> Injured
<<else>>
You're healthy.
-> Healthy
<<endif>>

# Jump after Python code
:: ProcessTurn
<<py
turn_count += 1
if turn_count >= 10:
    game_over = True
>>

<<if game_over>>
-> GameOver
<<endif>>

Turn {turn_count} continues...

# Jump in a loop - exits when condition met
:: SearchInventory
<<for item in inventory>>
Checking {item.name}...
<<if item.name == "key">>
Found the key!
-> FoundKey
<<endif>>
<<endfor>>

Key not found.

:: FoundKey
You found the key! Time to unlock the door.
```

**Multiple Conditional Jumps:**

Only the first true condition's jump executes:

```bard
:: RoutePlayer
<<if score >= 90>>
-> GradeA
<<elif score >= 80>>
-> GradeB
<<elif score >= 70>>
-> GradeC
<<else>>
-> GradeF
<<endif>>
```

With `score = 85`, only `-> GradeB` executes. The other branches are never evaluated.

**Content Flow Example:**

```bard
:: Start
~ health = 0

Checking your status...

<<if health <= 0>>
You feel weak...
-> Death
<<endif>>

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

<<for n in numbers>>
Checking {n}
<<if n == 3>>
-> Found
<<endif>>
<<endfor>>

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

**Status:** ✅ Implemented (Week 3)

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

**Status:** 📅 Week 5

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

**Status:** ✅ Implemented (Week 2, Session 6)

---

## Advanced Features (Post v1.0)

These are "nice to have" but not essential for first release.

### Scoped Sections

Group passages with shared state.

**Syntax:** `@section Name` ... `@endsection`

```bard
@section ClientAria.Session1

# Section-level setup (runs once when entering section)
<<py
client = load_client('aria')
session_state = {'trust': 50}
>>

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

**Status:** 🤔 Consider after v1.0 if pain point emerges

---

### Visit Tracking

Track how many times passages have been visited.

```bard
:: Library <<if visit_count('Library') == 0>> First time here. <<else>> You've been here {visit_count('Library')} times. <<endif>>
```

**Status:** 🤔 Consider after v1.0 if needed

---

### Sequences/Cycles

Ink-style cycling text.

```bard
{sequence(visit_count('Tavern'), [ "The tavern is bustling.", "The tavern is quieter now.", "The tavern is nearly empty." ])}
````

**Status:** 🤔 Consider after v1.0 if needed

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
2. Execute all `<<py>>` blocks and `~` assignments in order
3. Render content (evaluate expressions, conditionals, loops)
4. Filter available choices (check conditions)
5. Return output to frontend

### Navigation

- Choices navigate via `target` passage ID
- Immediate diverts (`->`) jump without player input
- Can pass parameters during navigation
- Engine tracks current passage ID

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

## Development Roadmap

### ✅ Week 1: Foundation (Complete)

- [x] Basic parser
- [x] Passage navigation
- [x] Simple choices
- [x] Compiler to JSON
- [x] Runtime engine
- [x] CLI compilation
- [x] CLI player

### ✅ Week 2: State & Organization (Complete)

- [x] Variable assignment (`~`)
- [x] Variable display (`{}`)
- [x] Variable display with format specifiers (`{var:.2f}`)
- [x] Expressions in assignments
- [x] Conditional choices (`+ {condition} [Text] -> Target`)
- [x] **File includes (`@include`)**

### 📅 Week 3: Python Integration

- [x] `<<py>>` blocks
- [x] Function calls in expressions
- [x] Object attributes (via Python blocks and expressions)
- [ ] Conditionals (`<<if>>`)
- [ ] Loops (`<<for>>`)

### 📅 Week 4: Navigation & Web

- [ ] Passage parameters
- [ ] Immediate diverts (`->`)
- [ ] One-time choices (`*`)
- [ ] Render directives (`@`)
- [ ] FastAPI integration
- [ ] React example

### 📅 Week 5: Polish

- [ ] Markdown support
- [ ] Custom tags `[!tag]`
- [ ] Comments (`#`)
- [ ] Imports (plain Python)
- [ ] Better error messages

### 📅 Week 6: Refinement

- [ ] Whitespace perfection
- [ ] HTML export
- [ ] Documentation
- [ ] Example stories
- [ ] Testing framework

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
<<py
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
>>

You draw three cards from the deck...

@ render_spread(cards, layout='three_card')

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

- ❌ Desktop app packaging (web-native only)
- ❌ Built-in graphics/audio system (use React/HTML5)
- ❌ Visual editor (code-first approach)
- ❌ Built-in game mechanics (inventory, combat, etc.)
- ❌ Save/load system (handle in your backend)
- ❌ Multiplayer/networking (handle in your backend)

These can be built using Bardic + your Python code, but are not built-in features.

---

## Contributing

Until v1.0, this is a personal project. After v1.0 is released and battle-tested on the tarot game, contributions may be accepted.

**Philosophy:** Features should solve real problems we've actually encountered, not hypothetical ones.

---

## Version History

- **v0.1.0** - Initial implementation (Week 1)
  - Basic passages
  - Simple choices
  - Compiler and runtime

---

## Questions to Answer Later

- Should we support includes? (`::include other.bard`)
- Do we need story-level metadata? (author, version, etc.)
- Should there be a plugin system?
- How should we handle localization/i18n?
- Should visit tracking be built-in or external?

**Decision:** Add these only when we hit a real need in production.

---

*This specification is a living document. It evolves based on actual usage in building the tarot game.*

Last updated: September 30, 2025
