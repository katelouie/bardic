# Render Directives — Full Reference

> **See also:** [Language Specification](spec.md) for the syntax summary, [Engine API](api/engine-api.md) for the runtime API.

Render directives tell the frontend to handle custom presentation logic. They emit structured data that your runtime interprets — whether that's rendering React components, instantiating Unity GameObjects, or formatting terminal output.

## Concept

Bardic stories run in a **backend engine** (Python) that produces **structured output** for a **frontend runtime** (React, Unity, CLI, etc.). Most content is just text, but sometimes you need custom UI elements:

- **Card spread visualization** — Show tarot cards in specific layouts
- **Character portraits** — Display character art with expressions
- **Mini-games** — Embed interactive elements
- **Data visualizations** — Charts, graphs, dashboards
- **Custom animations** — Trigger specific visual effects

**Render directives** let you specify these custom elements directly in your story, without breaking out of the narrative flow.

**Philosophy:** Bardic doesn't know how to render cards or portraits — your frontend does. Bardic just provides the data in a structured format your frontend can consume.

## Basic Syntax

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
- Not rendered as text — produces no output in story content
- Compiled to structured data sent to frontend
- Can appear anywhere in passage content
- Multiple directives per passage allowed
- Works in conditionals, loops, and regular content

**Important:** Directives are **declarative**, not imperative. You're saying "here's data about a card spread," not "render this component." The frontend decides how to interpret it.

---

## Examples

### Simple Directive

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

### Multiple Directives

```bard
:: Reading
@render card_spread(cards, layout='three_card', animation='flip')

The cards reveal:
{cards[0].name}, {cards[1].name}, {cards[2].name}

@render interpretation_panel(cards, style='traditional')

Do you understand their meaning?
```

Each directive is collected and returned in the `render_directives` list.

### With Conditionals

```bard
:: ShowReaction
@if client.trust > 75:
@render character_portrait(client, emotion='happy', size='large')
@elif client.trust > 25:
@render character_portrait(client, emotion='neutral', size='medium')
@else:
@render character_portrait(client, emotion='worried', size='small')
@endif

{client.name}'s reaction speaks volumes.
```

Only the directive from the true branch is collected.

### In Loops

```bard
:: DisplayDeck
@for card in hand:
@render card_detail(card, position=loop.index, interactive=True)
@endfor

Your hand is complete.
```

One directive is emitted per loop iteration. All are collected.

### Complex Arguments

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

## Framework Hints (Optional)

**Syntax:** `@render:framework directive_name(args)`

Tell Bardic to optimize the data structure for a specific framework. This is **optional** — the default format works for any runtime.

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

### React Framework Hint

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

### Future Framework Hints

Unity and Godot hints are not yet implemented but follow the same pattern. Want to add a framework hint? See [Extending Bardic](#extending-bardic-adding-framework-hints) below.

---

## Compilation Modes

Bardic can compile render directives in two modes:

### Evaluated Mode (Default)

**Configuration:** `BardEngine(story, evaluate_directives=True)`

Python expressions in directive arguments are **evaluated at runtime** in the backend. The frontend receives fully evaluated data.

```bard
@render card_spread(cards, layout='celtic_cross')
```

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

- Standard use case for most apps
- Backend has full game logic and state
- Frontend just displays data
- You want type-safe, validated data

### Raw Mode (Advanced)

**Configuration:** `BardEngine(story, evaluate_directives=False)`

Expressions are **NOT evaluated**. The frontend receives raw expressions and must evaluate them.

```bard
@render card_spread(cards, layout='celtic_cross')
```

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

**Most users should use evaluated mode.**

---

## Behavior with Story Features

### With Jumps

Directives from all passages in a jump chain are collected:

```bard
:: Start
@render title_screen(game_title)
-> Intro

:: Intro
@render fade_in()

The game begins...
```

**Output combines both directives.**

### With Conditionals

Only directives from the true branch are collected.

### With Loops

One directive per iteration — if `cards` has 3 items, you get 3 directives.

---

## Frontend Integration

### Generic TypeScript

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

### React

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
      <ReactMarkdown>{passage.content}</ReactMarkdown>

      {passage.render_directives.map((directive) => {
        const Component = componentRegistry[directive.react.componentName];
        if (!Component) return null;
        return (
          <Component
            key={directive.react.key}
            {...directive.react.props}
          />
        );
      })}

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

### Unity (Hypothetical)

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

### CLI/Terminal

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

## Error Handling

### Evaluation Errors

If evaluation fails in evaluated mode, you get an error directive:

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

### Missing Components

```jsx
const Component = componentRegistry[directive.name];
if (!Component) {
  console.warn(`Component '${directive.name}' not found`);
  return <div className="missing-component">
    Warning: Component not implemented: {directive.name}
  </div>;
}
```

---

## Extending Bardic (Adding Framework Hints)

Want to add support for your own framework? Here's how:

**1. Create a processor function:**

```python
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

---

## Design Philosophy

### Why Not Just Use Python Blocks?

**You could do this:**

```bard
@py:
component_data = {
    'type': 'card_spread',
    'cards': cards,
    'layout': 'celtic_cross'
}
components.append(component_data)
@endpy
```

**But directives are better because:**

- **Declarative** — Say what you want, not how to build it
- **Compiled** — Validated at compile time, not runtime
- **Visible** — Stand out in story text
- **Framework-agnostic** — Frontend-specific details in one place
- **Traceable** — Easy to find all custom UI in your story

### Why "Render" and Not "Component" or "Emit"?

- `@component` — Too React-specific
- `@emit` — Sounds like event system
- `@custom` — Too vague
- `@render` — **Familiar** (React, game engines), **short**, **directional**

---

## Use Cases

### Tarot Reading Game

```bard
:: DrawCards
~ cards = draw_tarot_cards(3)

You draw three cards from the deck...

@render:react card_spread(
    cards=cards,
    layout='past_present_future',
    animation='flip',
    interactive=True
)

+ [Interpret] -> Interpret
```

### Character Dialogue

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

### Data Visualization

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

---

## Limitations

**Current limitations:**

- No inline directives (`Text with @render inline(x) here`)
- No directive nesting (`@render outer(@render inner())`)
- No conditional directive expressions (`@render {var if cond else other}`)
- Can't return values to story (`~ result = @render thing()`)

**These are intentional design decisions.** Render directives are **one-way**: story → frontend. They produce UI, not story data.

**If you need computed values:**

```bard
# Do this:
@py:
result = compute_something(args)
@endpy
@render display(result)

# Not this:
~ result = @render compute(args)  # Won't work
```

---

## Troubleshooting

**Directive not appearing in output?**
1. Is it inside a false conditional?
2. Is the passage being jumped over?
3. Is there a Python error? (Check console/logs)
4. Is `evaluate_directives=False` and frontend not handling raw mode?

**"Unknown directive" warnings in frontend?**
1. Is the component registered in your component registry?
2. Does the name match exactly? (case-sensitive)
3. Did you rebuild your frontend after adding the component?

**Props not passing correctly?**
1. Variable names in Bardic vs React props
2. Data types (arrays vs objects)
3. Framework hint format (`directive.react.props` vs `directive.data`)

---

## Complete Example

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
      {passage.render_directives?.map((directive) => {
        const Component = componentRegistry[directive.react.componentName];
        return Component ? (
          <Component
            key={directive.react.key}
            {...directive.react.props}
          />
        ) : null;
      })}

      <ReactMarkdown>{passage.content}</ReactMarkdown>

      <ChoiceButtons choices={passage.choices} />
    </div>
  );
}
```
