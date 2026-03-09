# Input Directives — Full Reference

> **See also:** [Language Specification](spec.md) for the syntax summary, [Engine API](api/engine-api.md) for the runtime API.

Input directives let you pause the narrative to collect information from the player. Unlike choices (which are pre-defined options), inputs let players enter free-form text that becomes part of the story state.

**Philosophy:** Like render directives, input directives are declarative. You specify what input you want, and the frontend handles the actual UI. The engine manages the collected data in a persistent `_inputs` dictionary.

## Basic Syntax

**Format:** `@input name="variable_name" [placeholder="..."] [label="..."]`

```bard
@input name="reader_name" placeholder="Enter your name..." label="Your Name"
```

**Rules:**

- Start with `@input` followed by space
- `name` attribute is required (used as dictionary key)
- `placeholder` and `label` are optional
- If `label` is omitted, it's auto-generated from `name` (e.g., `reader_name` → `"Reader Name"`)
- Input values are stored in the special `_inputs` dictionary
- `_inputs` persists across all passages
- Re-using the same `name` overwrites the previous value
- Works anywhere: passages, conditionals, loops

## The `_inputs` Dictionary

All input data is automatically stored in `engine.state['_inputs']`:

```python
# After player submits "Kate" for reader_name:
engine.state['_inputs']  # {'reader_name': 'Kate'}
```

**Access in stories:**

```bard
{_inputs.get("reader_name")}           # Display the value
{_inputs.get("reader_name", "Guest")}  # With fallback
```

**Important:** `_inputs` is always available in all passages, conditionals, and Python blocks. It's automatically initialized as an empty dict when the engine starts.

## Common Pattern: Conditional Input Display

Show the input form only when data hasn't been collected yet, then show a confirmation:

```bard
:: AskName

What is your name?

@if not _inputs.get("reader_name"):
@input name="reader_name" placeholder="Enter your name..." label="Your Name"
@else:
Thank you, **{_inputs.get("reader_name")}**!
@endif

+ [Continue] -> NextPassage

:: NextPassage
@py:
# Process the input
name = _inputs.get("reader_name", "Stranger")
player = Player(name)
@endpy

Welcome, {player.name}!
```

**Flow:**

1. First visit: Conditional evaluates `not _inputs.get("reader_name")` → `True` → shows input form
2. Player enters name and submits
3. Frontend calls `engine.submit_inputs({'reader_name': 'Kate'})`
4. Frontend re-navigates to same passage (`engine.goto('AskName')`)
5. Second render: Shows thank you message
6. Player clicks Continue
7. NextPassage receives the name via `_inputs`

## Examples

### Simple Name Input

```bard
:: GetName
@input name="player_name" label="Your Name"

+ [Submit] -> Greet

:: Greet
Hello, {_inputs.get("player_name", "friend")}!
```

### Multiple Inputs Per Passage

```bard
:: Registration
Please fill out your information:

@input name="username" label="Username" placeholder="Choose a username"
@input name="email" label="Email" placeholder="your@email.com"
@input name="character_name" label="Character Name"

+ [Submit] -> CreateAccount
```

### Input in Conditionals

```bard
:: DivinationQuestion
@if not _inputs.get("question"):
What question do you bring to the cards?

@input name="question" placeholder="Ask your question..." label="Your Question"
@else:
Your question: "{_inputs.get("question")}"

The cards will answer...
@endif

+ [Continue] -> DrawCards
```

### Input in Loops

```bard
:: GatherNames
We need names for all {count} characters:

@for i in range(count):
Character {i+1}:
@input name="char_{i}" label="Character {i+1} Name"
@endfor

+ [Done] -> ProcessNames
```

### Using Input in Python Blocks

```bard
:: ProcessDivination
@py:
question = _inputs.get("question", "")

if "love" in question.lower():
    spread_type = "relationship_spread"
elif "career" in question.lower():
    spread_type = "career_spread"
else:
    spread_type = "general_spread"

current_spread = spread_type
@endpy

Based on your question, I'll use a {current_spread.replace('_', ' ')}.
```

### Validation and Re-prompting

```bard
:: GetAge
@py:
age_str = _inputs.get("age", "")
is_valid = age_str.isdigit() and int(age_str) >= 18
@endpy

@if not age_str or not is_valid:
Please enter your age (must be 18+):

@input name="age" placeholder="18" label="Age"

@if age_str and not is_valid:
**Error:** Please enter a valid age (18 or older).
@endif
@else:
You are {age_str} years old.
@endif

+ [Continue] -> NextStep
```

## Compiled Output

**Story:**

```bard
@input name="reader_name" placeholder="Enter your name..." label="Your Name"
```

**Compiled JSON:**

```json
{
  "type": "input",
  "name": "reader_name",
  "placeholder": "Enter your name...",
  "label": "Your Name"
}
```

Input directives in conditionals are collected dynamically based on which branch evaluates to true.

## Frontend Integration

The engine returns input directives in `PassageOutput.input_directives`:

```python
output = engine.goto('AskName')
print(output.input_directives)
# [{'type': 'input', 'name': 'reader_name', 'placeholder': '...', 'label': '...'}]
```

### Submitting Input

Frontend calls `engine.submit_inputs()` with collected data:

```python
input_data = {'reader_name': 'Kate'}
engine.submit_inputs(input_data)
engine.goto(engine.current_passage_id)  # Re-navigate to refresh display
```

### React Example

```jsx
function InputForm({ directives }) {
  const [values, setValues] = useState({});

  const handleSubmit = async () => {
    await api.submitInputs(sessionId, values);
    await refetchPassage();
  };

  return (
    <div className="input-form">
      {directives.map(directive => (
        <div key={directive.name} className="input-field">
          <label>{directive.label || directive.name}</label>
          <input
            type="text"
            placeholder={directive.placeholder || ''}
            value={values[directive.name] || ''}
            onChange={e => setValues({
              ...values,
              [directive.name]: e.target.value
            })}
          />
        </div>
      ))}
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
}
```

### NiceGUI Example

```python
def render_input_form(input_directives: list[dict]):
    """Render text input form from input directives."""
    input_widgets = {}

    with ui.column().classes('w-full gap-4 my-6 p-6 bg-purple-900/20 border border-purple-400/30 rounded-lg'):
        for spec in input_directives:
            name = spec.get('name', '')
            label = spec.get('label', name.replace('_', ' ').title())
            placeholder = spec.get('placeholder', '')

            input_widgets[name] = ui.input(
                label=label,
                placeholder=placeholder
            ).classes('w-full')

        ui.button('Submit', on_click=lambda: submit_inputs(input_widgets))

def submit_inputs(input_widgets: dict):
    """Collect and submit input data to engine."""
    data = {name: widget.value or '' for name, widget in input_widgets.items()}
    engine.submit_inputs(data)
    engine.goto(engine.current_passage_id)
    update_ui()
```

### FastAPI Backend

```python
@app.post("/story/submit-inputs")
async def submit_inputs(
    session_id: str,
    inputs: dict[str, str]
):
    engine = get_session_engine(session_id)
    engine.submit_inputs(inputs)
    output = engine.goto(engine.current_passage_id)

    return {
        'content': output.content,
        'choices': output.choices,
        'input_directives': output.input_directives
    }
```

## Backend API

```python
def submit_inputs(self, input_data: dict) -> None:
    """Submit user input data and store in state.

    Inputs are stored in the special '_inputs' dictionary in state,
    which persists across passage transitions. New inputs with the
    same name overwrite previous values.

    Args:
        input_data: Dictionary mapping input names to values
    """
    if '_inputs' not in self.state:
        self.state['_inputs'] = {}

    self.state['_inputs'].update(input_data)
```

## Use Cases

- **Character Names** — Let players name their character, companions, pets
- **Divination Questions** — Collect the player's question for tarot readings
- **Journal Entries** — Free-form text for player reflection
- **Spell Words** — Enter words of power for magic systems
- **Puzzle Answers** — Text-based puzzle solutions
- **Custom Choices** — When predefined choices aren't enough
- **Story Branching** — Use input content to influence narrative direction

## Design Philosophy

**Why not use choices for everything?**

Choices are great for predefined options, but sometimes you need open-ended input: player creativity (naming, custom answers), personalization (real questions, reflections), replayability (different text = different experience).

**Why `_inputs` instead of regular variables?**

- **Namespaced** — Won't conflict with story variables
- **Persistent** — Automatically available everywhere
- **Frontend-controlled** — Clear separation of concerns
- **Optional** — Empty by default, no required setup
- **Discoverable** — Always in the same place

**Why declarative directives instead of imperative code?**

```bard
# Declarative (preferred):
@input name="question" label="Your Question"

# Imperative (don't do this):
@py:
show_input_form("question", "Your Question")
wait_for_input()
@endpy
```

Directives are visible in story text, validated at compile time, frontend-agnostic, and separate concerns cleanly.

## Limitations

- Text input only (no checkboxes, radio buttons, dropdowns — use choices for predefined options)
- No client-side validation (handle in frontend)
- No required/optional marking (handle with conditionals)
- No multi-line text areas (single-line text only)

**These are intentional** — input directives are for simple text collection. Complex forms should be built in your frontend with regular HTML/React components.

## Troubleshooting

**Input not showing?**
1. Is it inside a false conditional branch?
2. Did you navigate to the passage correctly?
3. Is frontend checking for `input_directives`?

**Input value not persisting?**
1. Is `submit_inputs()` being called correctly?
2. Is frontend re-navigating after submit? (`engine.goto(current_id)`)
3. Is the input `name` correct?

**Conditional showing wrong branch?**
1. Is frontend re-rendering after submit? (need to call `goto()`, not `current()`)
2. Is the condition checking the right variable? (`_inputs.get("name")`)
3. Is the condition logic correct? (`not _inputs.get()` for "show when empty")

## Complete Example

**Story (`character_creator.bard`):**

```bard
from models.character import Character

:: Start
Welcome to character creation!

+ [Begin] -> GetName

:: GetName
@if not _inputs.get("name"):
What is your character's name?

@input name="name" placeholder="Enter name..." label="Character Name"
@else:
Your character: **{_inputs.get("name")}**
@endif

+ [Continue] -> GetClass

:: GetClass
@if not _inputs.get("backstory"):
Tell us about {_inputs.get("name", "your character")}'s backstory:

@input name="backstory" placeholder="A brief history..." label="Backstory"
@else:
Backstory: "{_inputs.get("backstory")}"
@endif

+ [Continue] -> CreateCharacter

:: CreateCharacter
@py:
char = Character(
    name=_inputs.get("name", "Unknown"),
    backstory=_inputs.get("backstory", "")
)
@endpy

**{char.name}** has been created!

"{char.backstory}"

+ [Start adventure] -> Adventure
```

This example shows:

- Multiple input passages
- Conditional display (input vs confirmation)
- Accessing inputs in later passages
- Using inputs in Python blocks
- Fallback values for safety
