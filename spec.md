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
- Conditional: 📅 Week 2
- One-time (*): 📅 Week 4
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

Inline Python evaluation.

```bard
You rolled a {roll_dice(20)}.
The card is {card.get_display_name()}.
{greet(player_name)}
```

**Rules:**

- Wrapped in `{}`
- Can be variable names, function calls, or expressions
- Evaluated at render time
- Result is converted to string for display

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

---

### Conditionals

Branch content based on conditions.

```bard
<<if condition>> Content if true. <<elif other_condition>> Content if other is true. <<else>> Default content. <<endif>>
```

**Examples:**

```bard
<<if health > 75>> You feel strong. <<elif health > 25>> You're wounded but standing. <<else>> You're barely conscious. <<endif>>
```

**Rules:**

- Conditions are Python expressions
- Can access all variables and functions
- Can be nested
- Produces no whitespace itself (only renders chosen branch)

**Status:** 📅 Week 3

---

### Loops

Iterate over collections.

```bard
<<for item in collection>> {item.name} <<endfor>>
```

**Examples:**

```bard
Your inventory: <<for item in inventory>>

- {item.name} (quantity: {item.quantity}) <<endfor>>
```

**Inline loops:**

```bard
Cards drawn: <<for card in cards>>{card.name}, <<endfor>>
```

**Status:** 📅 Week 3

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

**Status:** 📅 Week 5

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

Tell React to render custom components.

```bard
@ render_spread(cards, layout='celtic_cross')
@ render_client_reaction(client, intensity='high')
```

**Rules:**

- Start with `@` followed by space
- Function-call syntax
- Arguments are Python expressions
- Compiled to structured data for frontend
- Not rendered as text (no output in story flow)
- Can appear anywhere in passage content

**Examples:**

```bard
:: DrawCards
<<py
cards = draw_cards(3)
>>

The cards are laid out before you...

@ render_spread(cards, layout='three_card', animation='flip')

The first card is {cards[0].name}.

@ render_card_detail(cards[0], position='past')
```

**Compiled Output:**

```json
{
  "render_directives": [
    {
      "component": "render_spread",
      "props": {
        "cards": [...],
        "layout": "three_card",
        "animation": "flip"
      }
    },
    {
      "component": "render_card_detail",
      "props": {
        "card": {...},
        "position": "past"
      }
    }
  ]
}
```

**React Integration:**

```jsx
{passageData.render_directives.map((directive, i) => {
  const Component = componentRegistry[directive.component];
  return <Component key={i} {...directive.props} />;
})}
```

**Status:** 📅 Week 4

---

### Immediate Jumps (Diverts)

Navigate without a choice.

```bard
:: CheckHealth <<if health <= 0>> -> Death <<endif>>

You're still alive...
```

**Rules:**

- `-> PassageName` immediately jumps
- No choice needed
- Can be conditional
- Useful for error handling, automatic progression

**Status:** 📅 Week 4

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

## Examples

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
