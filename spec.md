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

- [Look around] -> Examine

# One-time choice (only show once)

- [Pick up the key] -> GetKey

# Conditional choice

- {health > 50} [Fight the dragon] -> Combat

# Choice with parameters (pass data to next passage)

- [Draw cards] -> DrawCards(count=3, spread='celtic_cross')
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

**Expressions:**

```bard
~ health = health - 10 ~ total = (gold * 2) + bonus ~ description = f"You have {gold} gold"
```

**Status:** 📅 Week 2

---

### Python Code Blocks

Execute arbitrary Python code.

```bard
<<py

# Multi-line Python code

cards = deck.draw(3) for card in cards: if random.random() < 0.3: card.is_reversed = True

difficulty = calculate_difficulty(cards, reader_stats)
>>
```

**Rules:**

- Opens with `<<py`
- Closes with `>>`
- Can span multiple lines
- Has access to all imported modules and functions
- Can modify state
- Produces no output (use variables to display results)

**Status:** 📅 Week 3

---

### Python Expressions

Inline Python evaluation.

```bard
You rolled a {roll_dice(20)}. The card is {card.get_display_name()}. {greet(player_name)}
```

**Rules:**

- Wrapped in `{}`
- Can be variable names, function calls, or expressions
- Evaluated at render time
- Result is converted to string for display

**Status:** 📅 Week 3

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

```bard
::import from models.card import Card from services.tarot import TarotService, draw_from_pool from utils.narrative import generate_greeting
```

**Rules:**

- Must be at the top of the file
- Standard Python import syntax
- Available to all passages in the file
- Can import from your project's Python modules

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
@ render_spread(cards, layout='celtic_cross') @ render_client_reaction(client, intensity='high')
```

**Rules:**

- Start with `@`
- Function-call syntax
- Arguments are Python expressions
- Compiled to structured data for frontend
- Not rendered as text

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

```bard
::include path/to/file.bard
```

**Rules:**

- Must appear before any passages (in or after `::import` section)
- Paths are relative to the including file
- Recursive: included files can include other files
- All passages are merged into single compiled output
- Duplicate passage names cause compilation error
- Circular includes are detected and error

**Example:**

```bard
# main.bard

from services.tarot import TarotService

::include shared/card_mechanics.bard
::include clients/aria/session1.bard
::include clients/marcus/session1.bard

:: Start Welcome to your desk.

- [See Aria] -> Aria.Session1.Start
- [See Marcus] -> Marcus.Session1.Start
```

**Benefits:**

- Organize large stories into manageable files
- Separate concerns (clients, mechanics, interpretations)
- Enable parallel development
- Better version control
- Reusable components across stories

**Critical for:** Stories with multiple client paths, hub-and-spoke structures, or >1000 lines of content.

**Status:** 📅 Week 2, Session 6 (essential for story organization)

---

## Advanced Features (Post v1.0)

These are "nice to have" but not essential for first release.

### Scoped Sections

Group passages with shared state.

```bard
::section ClientAria.Session1 <<py

# Section-level setup

client = load_client('aria') session_state = {'trust': 50}

::end

:: ClientAria.Session1.Start

# Has access to client and session_state

:: ClientAria.Session1.Reading

# Still has access
```

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

### 📅 Week 2: State & Organization

- [ ] Variable assignment (`~`)
- [ ] Variable display (`{}`)
- [ ] Expressions in assignments
- [ ] Conditional choices
- [ ] **File includes (`::include`)**

### 📅 Week 3: Python Integration

- [ ] `<<py>>` blocks
- [ ] Function calls in expressions
- [ ] Object attributes
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
- [ ] Comments
- [ ] Imports section
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

### With Variables

```bard
:: Start
~ health = 100
~ gold = 50

You have {health} health and {gold} gold.

+ [Enter dungeon] -> Dungeon

:: Dungeon
~ health = health - 20
~ gold = gold + 10

You fought a monster!
Health: {health}, Gold: {gold}

+ {health > 0} [Continue] -> Victory
+ {health <= 0} [You died] -> Death
```

### With Python Objects (Tarot Game)

```bard
::import
from services.tarot import TarotService
from models.card import Card

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

_This specification is a living document. It evolves based on actual usage in building the tarot game._

Last updated: September 30, 2025
