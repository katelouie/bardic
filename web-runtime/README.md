# Bardic Web Runtime

A FastAPI + React web application for running compiled Bardic interactive fiction stories in the browser.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Backend (FastAPI)](#backend-fastapi)
- [Frontend (React)](#frontend-react)
- [Data Flow](#data-flow)
- [Render Directives System](#render-directives-system)
- [Extensions System](#extensions-system)
- [Setup & Running](#setup--running)
- [Development Guide](#development-guide)
- [Current Features](#current-features)

---

## Overview

The Bardic Web Runtime is a generic story player that can run **any** compiled Bardic story (`.json` files) in a web browser. It consists of:

- **Backend**: FastAPI server that hosts the Bardic engine, manages sessions, and exposes REST API endpoints
- **Frontend**: React SPA that displays story content, handles user choices, and renders custom components

**Key Design Principle**: The backend does all story execution and state management. The frontend is purely presentational.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User's Browser                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  React Frontend (Vite Dev Server - Port 5173)            │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │  │
│  │  │   App.jsx   │  │ Component    │  │   Extensions/   │ │  │
│  │  │ (Main UI)   │──│  Registry    │──│ Custom React    │ │  │
│  │  │             │  │              │  │   Components    │ │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │ HTTP REST API
                           │ (CORS enabled)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  main.py (Core Server)                                    │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │  │
│  │  │   API       │  │   Session    │  │   Extensions    │ │  │
│  │  │ Endpoints   │──│  Management  │──│   (Context +    │ │  │
│  │  │             │  │              │  │    Routes)      │ │  │
│  │  └─────────────┘  └──────────────┘  └─────────────────┘ │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           │                                     │
│                           ▼                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │         BardEngine (from bardic package)                  │  │
│  │  • Loads compiled .json stories                           │  │
│  │  • Executes passages & evaluates expressions             │  │
│  │  • Manages state variables                                │  │
│  │  • Filters conditional choices                            │  │
│  │  • Renders content & directives                           │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  compiled_stories/      │
              │  (JSON story files)     │
              │                         │
              │  • story1.json          │
              │  • story2.json          │
              │  • ...                  │
              └─────────────────────────┘
```

---

## Backend (FastAPI)

### File Structure

```
backend/
├── main.py                 # Core FastAPI server & API endpoints
├── extensions/
│   ├── __init__.py        # Exports get_game_context & register_custom_routes
│   ├── context.py         # Custom context functions for stories
│   └── routes.py          # Custom API endpoints (optional)
```

### Core Components

#### `main.py` - FastAPI Server

**Key Responsibilities:**
- Load compiled stories from `compiled_stories/` directory
- Manage story sessions (one `BardEngine` instance per session)
- Expose REST API endpoints for frontend
- Handle CORS for cross-origin requests (localhost:5173 ↔ 127.0.0.1:8000)

**Session Management:**
- Sessions stored in-memory: `sessions: dict[str, BardEngine] = {}`
- Each session identified by unique `session_id` (generated by frontend)
- Session persists for duration of story playthrough

**Path Configuration:**
- `PROJECT_ROOT`: Parent directory (bardic/)
- `GAME_LOGIC_DIR`: Custom game logic directory (game_logic/)
- `STORIES_DIR`: Compiled stories (compiled_stories/)
- All paths added to `sys.path` for imports

### API Endpoints

#### `GET /`
Root endpoint with API documentation.

**Response:**
```json
{
  "message": "Bardic Web Runtime",
  "version": "0.1.0",
  "endpoints": { ... }
}
```

#### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

#### `GET /api/stories`
List all available compiled stories.

**Response:**
```json
{
  "stories": [
    {
      "id": "story_name",
      "name": "Story Name",
      "path": "/path/to/story.json"
    }
  ]
}
```

#### `POST /api/story/start`
Start a new story session.

**Request Body:**
```json
{
  "story_id": "story_name",
  "session_id": "session_abc123"
}
```

**Response:**
```json
{
  "content": "Rendered passage content (markdown)",
  "choices": [
    {"index": 0, "text": "Choice text"}
  ],
  "passage_id": "PassageName",
  "is_end": false,
  "render_directives": [
    {
      "name": "component_name",
      "data": { ... },
      "react": {
        "componentName": "ComponentName",
        "props": { ... },
        "key": "unique_key"
      }
    }
  ]
}
```

**Process:**
1. Load story JSON from `compiled_stories/{story_id}.json`
2. Create `BardEngine` instance with custom context
3. Store engine in `sessions[session_id]`
4. Call `engine.current()` to get first passage
5. Return passage data to frontend

#### `POST /api/story/choose`
Make a choice and advance the story.

**Request Body:**
```json
{
  "session_id": "session_abc123",
  "choice_index": 0
}
```

**Response:**
Same format as `/api/story/start`.

**Process:**
1. Retrieve engine from `sessions[session_id]`
2. Call `engine.choose(choice_index)`
3. Return new passage data

### Extensions System

#### `extensions/context.py`

Provides custom context functions that are available in Bardic stories.

**What it does:**
- Defines Python functions that can be called from `.bard` files
- Returns a dictionary mapping function names to implementations
- Injected into `BardEngine` on story initialization

**Example:**
```python
def get_game_context():
    return {
        # Utility functions
        "random_int": lambda min_val, max_val: random.randint(min_val, max_val),
        "random_choice": lambda items: random.choice(items),

        # Game-specific functions
        "draw_tarot_cards": tarot_service.draw_cards,
        "get_card_meaning": tarot_service.get_card_meaning,

        # Classes (for instantiation)
        "Card": Card,
        "Client": Client,
    }
```

**Usage in .bard files:**
```bard
~ cards = draw_tarot_cards(3)
~ lucky_number = random_int(1, 10)
~ my_card = Card("The Fool", 0, False)
```

#### `extensions/routes.py`

Provides custom API endpoints for game-specific functionality.

**What it does:**
- Defines additional REST API routes
- Useful for LLM calls, database access, external APIs
- Registered with FastAPI app via `register_custom_routes(app)`

**Example Routes:**
- `POST /api/game/interpret-cards` - Custom card interpretation
- `POST /api/game/save-session` - Save game session
- `GET /api/game/load-session/{id}` - Load saved session

---

## Frontend (React)

### File Structure

```
frontend/
├── src/
│   ├── main.jsx              # React app entry point
│   ├── App.jsx               # Main application component
│   ├── App.css               # Application styles (purple theme)
│   ├── index.css             # Global styles
│   └── extensions/
│       ├── componentRegistry.jsx      # Maps directive names to components
│       ├── DefaultDirective.jsx       # Fallback for unknown directives
│       ├── TarotCard.jsx             # Example custom component
│       ├── CardSpread.jsx            # Example custom component
│       ├── CardDetail.jsx            # Example custom component
│       ├── InterpretationPanel.jsx   # Example custom component
│       └── README.md                 # Extension documentation
├── package.json
└── vite.config.js
```

### Core Components

#### `App.jsx` - Main Application

**Key Responsibilities:**
- Manage application state (current passage, loading, errors)
- Handle story selection and session management
- Make API calls to backend
- Render markdown content with `react-markdown`
- Render custom components from render directives

**State Management:**
```javascript
const [passage, setPassage] = useState(null)          // Current passage data
const [loading, setLoading] = useState(false)         // Loading state
const [error, setError] = useState(null)              // Error messages
const [sessionId] = useState(() => 'session_...')     // Unique session ID
const [stories, setStories] = useState([])            // Available stories
const [selectedStory, setSelectedStory] = useState(null)
const [showStorySelect, setShowStorySelect] = useState(true)
```

**Key Functions:**

- **`loadStories()`**: Fetches story list from `GET /api/stories`
- **`startStory()`**: Starts a new story session via `POST /api/story/start`
- **`makeChoice(index)`**: Makes a choice via `POST /api/story/choose`

**UI States:**
1. **Story Selection**: Shows list of available stories
2. **Loading**: Shows spinner while loading/processing
3. **Story Playthrough**: Shows passage content, render directives, and choices
4. **End State**: Shows "The End" with restart button
5. **Error State**: Shows error message with retry button

**Markdown Rendering:**
Uses `react-markdown` with plugins:
- `rehype-raw`: Allows HTML in markdown
- `remark-gfm`: GitHub Flavored Markdown support

**Render Directives Rendering:**
See [Render Directives System](#render-directives-system) section below.

#### `extensions/componentRegistry.jsx`

Maps render directive names to React components.

**Structure:**
```javascript
import TarotCard from './TarotCard'
import CardSpread from './CardSpread'
// ... other imports

const componentRegistry = {
  'card_spread': CardSpread,
  'CardSpread': CardSpread,      // PascalCase for :react hint
  'tarot_card': TarotCard,
  // ... other mappings
  'default': DefaultDirective    // Fallback
}

export default componentRegistry
```

**Lookup Process:**
1. Backend sends directive with `name` field (e.g., `"card_spread"`)
2. If `:react` hint used, also sends `react.componentName` (e.g., `"CardSpread"`)
3. Frontend looks up component in registry
4. Falls back to `DefaultDirective` if not found

#### Custom Components

See `frontend/src/extensions/README.md` for detailed documentation on creating custom components.

**Example Components:**
- **`TarotCard.jsx`**: Displays a single tarot card
- **`CardSpread.jsx`**: Displays multiple cards in a layout
- **`CardDetail.jsx`**: Detailed view of a card with position info
- **`InterpretationPanel.jsx`**: Styled interpretation text display
- **`DefaultDirective.jsx`**: Debug view showing raw props as JSON

---

## Data Flow

### Story Execution Flow

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. Author writes story in .bard file                            │
│    stories/my_story.bard                                         │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 2. Compile story to JSON                                         │
│    $ bardic compile stories/my_story.bard                        │
│    → compiled_stories/my_story.json                              │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 3. Frontend loads story list                                     │
│    GET /api/stories                                              │
│    ← {stories: [{id: "my_story", ...}]}                          │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. User selects story                                            │
│    POST /api/story/start                                         │
│    → {story_id: "my_story", session_id: "abc123"}                │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. Backend creates BardEngine instance                           │
│    • Loads my_story.json                                         │
│    • Injects custom context functions                            │
│    • Stores in sessions["abc123"]                                │
│    • Executes first passage                                      │
│    • Renders content & directives                                │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. Backend returns passage data                                  │
│    ← {content: "...", choices: [...], render_directives: [...]}  │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 7. Frontend renders passage                                      │
│    • Markdown content → ReactMarkdown                            │
│    • Render directives → Custom React components                 │
│    • Choices → <button> elements                                 │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ 8. User makes choice                                             │
│    POST /api/story/choose                                        │
│    → {session_id: "abc123", choice_index: 0}                     │
└──────────────────────────────────────────────────────────────────┘
                           │
                           ▼ (back to step 5)
```

### Request/Response Cycle

**Start Story:**
```
Frontend                    Backend                    BardEngine
   │                          │                            │
   ├─ POST /api/story/start ─>│                            │
   │                          ├─ Load story JSON           │
   │                          ├─ Create engine ───────────>│
   │                          │                            ├─ Initialize state
   │                          │                            ├─ Execute first passage
   │                          │<─ Return PassageOutput ────┤
   │<─ Return passage data ───┤                            │
   ├─ Render UI               │                            │
```

**Make Choice:**
```
Frontend                    Backend                    BardEngine
   │                          │                            │
   ├─ POST /api/story/choose >│                            │
   │                          ├─ Get engine from session   │
   │                          ├─ Call choose() ──────────>│
   │                          │                            ├─ Navigate to target
   │                          │                            ├─ Execute passage
   │                          │                            ├─ Filter choices
   │                          │<─ Return PassageOutput ────┤
   │<─ Return passage data ───┤                            │
   ├─ Update UI               │                            │
```

---

## Render Directives System

**Render directives** allow embedding custom React components in Bardic stories.

### Full Flow: .bard → JSON → Engine → React

#### 1. Write directive in .bard file

```bard
:: MyPassage
~ cards = [
    Card("The Fool", 0, False),
    Card("The Magician", 1, False)
]

Here are your cards:

@render:react card_spread(cards=cards, layout='three_card')

+ [Continue] -> Next
```

**Syntax:**
- `@render` - Basic directive (props wrapped in `data` object)
- `@render:react` - React hint (props passed directly to component)

#### 2. Parser compiles to JSON

**Compiled output** (`compiled_stories/my_story.json`):
```json
{
  "passages": {
    "MyPassage": {
      "content": [
        {"type": "text", "value": "Here are your cards:\n\n"},
        {
          "type": "render_directive",
          "name": "card_spread",
          "args": "cards=cards, layout='three_card'",
          "framework_hint": "react"
        }
      ],
      "execute": [
        {
          "type": "set_var",
          "var": "cards",
          "expression": "[Card(...), Card(...)]"
        }
      ]
    }
  }
}
```

#### 3. BardEngine executes & renders

**When passage is entered:**
1. Execute commands: `engine._execute_passage("MyPassage")`
   - Evaluates `cards = [Card(...), ...]`
   - Stores in `engine.state["cards"]`

2. Render content: `engine._render_passage("MyPassage")`
   - Text tokens → rendered as-is
   - Expression tokens → evaluated with `engine.state`
   - **Render directive tokens** → processed by `_process_render_directive()`

**Render Directive Processing** (`engine.py:_process_render_directive()`):

```python
def _process_render_directive(self, directive: dict) -> dict:
    # Parse arguments: "cards=cards, layout='three_card'"
    args = self._parse_render_args(directive["args"])

    # Evaluate each argument with current state
    evaluated_data = {}
    for key, expr in args.items():
        evaluated_data[key] = eval(expr, {"__builtins__": {}}, self.state)

    # Build output
    result = {
        "name": directive["name"],
        "data": evaluated_data
    }

    # If framework_hint="react", add special format
    if directive.get("framework_hint") == "react":
        result["react"] = {
            "componentName": to_pascal_case(directive["name"]),
            "props": evaluated_data,  # Props passed directly
            "key": generate_unique_key()
        }

    return result
```

**Example output:**
```python
{
  "name": "card_spread",
  "data": {
    "cards": [Card(...), Card(...)],  # Evaluated!
    "layout": "three_card"
  },
  "react": {
    "componentName": "CardSpread",
    "props": {
      "cards": [Card(...), Card(...)],
      "layout": "three_card"
    },
    "key": "card_spread_abc123"
  }
}
```

#### 4. Backend sends to frontend

**API response:**
```json
{
  "content": "Here are your cards:\n\n",
  "choices": [...],
  "render_directives": [
    {
      "name": "card_spread",
      "data": {
        "cards": [
          {"name": "The Fool", "number": 0, "reversed": false},
          {"name": "The Magician", "number": 1, "reversed": false}
        ],
        "layout": "three_card"
      },
      "react": {
        "componentName": "CardSpread",
        "props": {
          "cards": [...],
          "layout": "three_card"
        },
        "key": "card_spread_abc123"
      }
    }
  ]
}
```

**Note:** Python objects (like `Card` instances) are serialized to JSON-compatible dicts.

#### 5. Frontend renders React component

**In `App.jsx`:**
```javascript
{passage.render_directives && passage.render_directives.map((directive, i) => {
  // Check for React hint
  if (directive.react) {
    // Look up component by PascalCase name
    const Component = componentRegistry[directive.react.componentName]
      || componentRegistry.default

    // Render with props passed directly
    return (
      <Component
        key={directive.react.key}
        {...directive.react.props}  // Props spread directly!
      />
    )
  }

  // Fallback: generic format (props wrapped in "data")
  const Component = componentRegistry[directive.name]
    || componentRegistry.default

  return (
    <Component
      key={i}
      data={directive.data}
      name={directive.name}
    />
  )
})}
```

**Component receives:**
```javascript
<CardSpread
  cards={[
    {name: "The Fool", number: 0, reversed: false},
    {name: "The Magician", number: 1, reversed: false}
  ]}
  layout="three_card"
/>
```

**Component renders:**
```javascript
function CardSpread({ cards, layout = 'simple' }) {
  return (
    <div className="card-spread">
      <h3>Card Spread ({layout})</h3>
      <div className="card-grid">
        {cards.map((card, i) => (
          <TarotCard key={i} card={card} size="medium" />
        ))}
      </div>
    </div>
  )
}
```

### Key Points

✅ **Backend evaluates all expressions** - Frontend receives final data
✅ **Named arguments required** - Use `card=cards[0]`, not positional args
✅ **`:react` hint recommended** - Props passed directly to component
✅ **Component registry maps names** - Both snake_case and PascalCase supported
✅ **Fallback to DefaultDirective** - Shows debug view for unknown components

---

## Extensions System

### Adding Custom Context Functions

**Purpose:** Make Python functions available in `.bard` stories.

**Steps:**

1. **Edit `backend/extensions/context.py`:**
   ```python
   def get_game_context():
       return {
           # Add your function
           "my_function": lambda x: x * 2,

           # Or import from game logic
           "do_something": my_module.do_something,

           # Or add a class
           "MyClass": MyClass,
       }
   ```

2. **Use in .bard files:**
   ```bard
   ~ result = my_function(5)
   ~ obj = MyClass("param")
   ```

3. **Restart backend** to apply changes.

### Adding Custom API Routes

**Purpose:** Create custom endpoints for external services, databases, LLMs, etc.

**Steps:**

1. **Edit `backend/extensions/routes.py`:**
   ```python
   @router.post("/api/game/my-endpoint")
   async def my_endpoint(data: dict) -> dict:
       # Your custom logic
       result = do_something(data)
       return {"result": result}
   ```

2. **Call from frontend:**
   ```javascript
   const response = await fetch('http://127.0.0.1:8000/api/game/my-endpoint', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({...})
   })
   const data = await response.json()
   ```

3. **Restart backend** to register new routes.

### Adding Custom React Components

**Purpose:** Create custom UI components for render directives.

**See:** `frontend/src/extensions/README.md` for comprehensive guide.

**Quick Steps:**

1. **Create component file:** `frontend/src/extensions/MyComponent.jsx`
   ```javascript
   function MyComponent({ myProp, anotherProp }) {
     return (
       <div className="my-component">
         <h3>{myProp}</h3>
         <p>{anotherProp}</p>
       </div>
     )
   }

   export default MyComponent
   ```

2. **Register in `componentRegistry.jsx`:**
   ```javascript
   import MyComponent from './MyComponent'

   const componentRegistry = {
     // ... existing
     'my_component': MyComponent,
     'MyComponent': MyComponent,  // For :react hint
     'default': DefaultDirective
   }
   ```

3. **Use in .bard stories:**
   ```bard
   @render:react my_component(myProp="Hello", anotherProp="World")
   ```

4. **No restart needed** - Vite hot-reloads automatically.

---

## Setup & Running

### Prerequisites

- **Python 3.12+** with `pyenv`
- **Node.js 18+** with `npm`
- Bardic CLI installed (`pip install -e .` from project root)

### Initial Setup

#### 1. Backend Setup

```bash
cd web-runtime/backend

# Activate pyenv environment
pyenv activate bardic

# Install dependencies (if any)
# (FastAPI, uvicorn, etc. should already be installed with Bardic)
```

#### 2. Frontend Setup

```bash
cd web-runtime/frontend

# Install dependencies
npm install
```

### Running the Application

**You need TWO terminal windows:**

#### Terminal 1: Backend Server

```bash
cd web-runtime/backend
pyenv activate bardic
python -m uvicorn main:app --reload --port 8000
```

**Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Test:** Open http://127.0.0.1:8000 in browser - should see API info.

#### Terminal 2: Frontend Dev Server

```bash
cd web-runtime/frontend
npm run dev
```

**Output:**
```
VITE v7.1.7  ready in 500 ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

**Test:** Open http://localhost:5173 in browser - should see story selection.

### Workflow

1. **Write story:** Create `.bard` file in `stories/`
2. **Compile:** `bardic compile stories/my_story.bard`
3. **Refresh browser:** Story appears in list automatically
4. **Select & play:** Click story name, click "Start Story"

**Note:** Backend automatically detects new `.json` files in `compiled_stories/`.

---

## Development Guide

### Project Structure

```
web-runtime/
├── backend/
│   ├── main.py                # FastAPI server
│   └── extensions/
│       ├── __init__.py       # Exports
│       ├── context.py        # Custom context functions
│       └── routes.py         # Custom API routes
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # React entry point
│   │   ├── App.jsx          # Main UI component
│   │   ├── App.css          # Styles (purple theme)
│   │   └── extensions/
│   │       ├── componentRegistry.jsx  # Component mapping
│   │       ├── DefaultDirective.jsx   # Fallback
│   │       ├── TarotCard.jsx         # Custom component
│   │       ├── CardSpread.jsx        # Custom component
│   │       ├── CardDetail.jsx        # Custom component
│   │       ├── InterpretationPanel.jsx # Custom component
│   │       └── README.md             # Extension docs
│   ├── package.json
│   └── vite.config.js
└── README.md                 # This file
```

### Key Files to Edit

**For story logic:**
- `backend/extensions/context.py` - Add Python functions for stories
- `backend/extensions/routes.py` - Add custom API endpoints

**For UI:**
- `frontend/src/App.jsx` - Main application UI
- `frontend/src/App.css` - Application styles
- `frontend/src/extensions/` - Custom React components

**For configuration:**
- `backend/main.py` - API endpoints, CORS, paths
- `frontend/vite.config.js` - Vite configuration

### Debugging

#### Backend Debugging

**Enable debug output:**
- Backend already logs to console (see `main.py:149-154, 191-197`)
- Check terminal running `uvicorn` for logs

**Common issues:**
- **Import errors**: Check `sys.path` configuration in `main.py:48-57`
- **Context function errors**: Check `extensions/context.py` imports
- **Session not found**: Session cleared or backend restarted

#### Frontend Debugging

**Check browser console:**
- `console.log('Story started:', data)` - After starting story
- `console.log('Render directives:', data.render_directives)` - Directive data
- `console.log('Choice made:', data)` - After making choice

**Common issues:**
- **CORS errors**: Check `allow_origins` in `backend/main.py:33-36`
- **Component not rendering**: Check `componentRegistry.jsx` registration
- **Props undefined**: Check directive uses named arguments in `.bard` file

#### Render Directive Debugging

**Test with DefaultDirective:**
1. Remove component from `componentRegistry.jsx`
2. Refresh browser
3. Should show debug view with JSON props
4. Verify data structure is correct

**Check compiled JSON:**
```bash
cat compiled_stories/my_story.json | grep -A 10 "render_directive"
```

Verify:
- `type`: "render_directive"
- `name`: Matches your directive name
- `args`: Contains correct argument string
- `framework_hint`: "react" if using `:react`

### Testing

**Backend:**
```bash
# Health check
curl http://127.0.0.1:8000/api/health

# List stories
curl http://127.0.0.1:8000/api/stories

# Start story (requires compiled story)
curl -X POST http://127.0.0.1:8000/api/story/start \
  -H "Content-Type: application/json" \
  -d '{"story_id": "test_render_directives", "session_id": "test123"}'
```

**Frontend:**
- Open http://localhost:5173
- Open browser DevTools (F12)
- Check Console, Network tabs

### Performance Considerations

**Backend:**
- Sessions stored in-memory (lost on restart)
- One `BardEngine` per session (lightweight)
- No database queries (all in-memory)

**Frontend:**
- Vite dev server has hot module reload
- ReactMarkdown renders on each passage
- Custom components should be lightweight

**Production notes:**
- For production, use persistent session storage (Redis, database)
- Build frontend: `npm run build`
- Serve with production ASGI server (Gunicorn + Uvicorn)
- Consider nginx reverse proxy for both services

---

## Current Features

### Working Features ✅

**Core Story Engine:**
- [x] Load and execute compiled Bardic stories
- [x] Session management (in-memory)
- [x] Variable assignments and expressions
- [x] Conditional choices (filtered by state)
- [x] Markdown rendering in content
- [x] Format specifiers in expressions (`{var:.2f}`)

**Render Directives:**
- [x] Basic render directives (`@render`)
- [x] React framework hint (`@render:react`)
- [x] Named argument parsing
- [x] Expression evaluation in directive arguments
- [x] Custom React component rendering
- [x] Component registry system
- [x] DefaultDirective fallback

**API:**
- [x] List available stories
- [x] Start story sessions
- [x] Make choices and advance story
- [x] CORS configuration for local development

**UI:**
- [x] Story selection screen
- [x] Passage rendering (markdown)
- [x] Choice buttons
- [x] Custom component rendering
- [x] Loading states
- [x] Error handling with retry
- [x] End state detection
- [x] Restart story

**Extensions:**
- [x] Custom context functions
- [x] Custom API routes (template)
- [x] Tarot-specific game logic integration
- [x] Example custom components

### Known Limitations ⚠️

- **No persistent storage**: Sessions lost on backend restart
- **No save/load system**: Stories restart from beginning
- **In-memory only**: Not suitable for production at scale
- **No authentication**: Sessions are not user-authenticated
- **Limited error recovery**: Some errors require full restart

### Future Enhancements 🚀

**Planned improvements:**
- Persistent session storage (Redis/database)
- Save/load game system
- User authentication
- Story history/rollback
- Enhanced debugging tools
- Production deployment guide
- Automated testing
- Story metadata (author, description, cover image)

---

## Troubleshooting

### Backend won't start

**Symptom:** `python main.py` crashes or shows import errors

**Solutions:**
1. Activate pyenv: `pyenv activate bardic`
2. Check Python version: `python --version` (should be 3.12+)
3. Install Bardic: `pip install -e .` from project root
4. Check imports in `extensions/context.py` and `extensions/routes.py`

### Frontend shows "Loading Stories..."

**Symptom:** Story list never appears

**Solutions:**
1. Check backend is running: `curl http://127.0.0.1:8000/api/health`
2. Check CORS: Look for CORS errors in browser console
3. Check compiled_stories exists: `ls ../compiled_stories/`
4. Check stories endpoint: `curl http://127.0.0.1:8000/api/stories`

### Render directives show "undefined"

**Symptom:** Components render but show undefined values

**Solutions:**
1. Check compiled JSON has correct args: `cat compiled_stories/story.json`
2. Use named arguments in .bard: `card=cards[0]` not just `cards[0]`
3. Check component expects correct prop names
4. Use `:react` hint: `@render:react component_name(...)`

### Components not rendering

**Symptom:** Raw @render text appears or component missing

**Solutions:**
1. Check componentRegistry.jsx has correct import and mapping
2. File extension must be `.jsx` not `.js`
3. Check directive name matches registry key exactly (case-sensitive)
4. Check DefaultDirective fallback isn't showing instead

### CORS errors

**Symptom:** Network errors in browser console

**Solutions:**
1. Check backend CORS config includes both localhost and 127.0.0.1
2. Ensure frontend uses same host as CORS config
3. Restart backend after CORS changes

---

## Additional Resources

- **Bardic Documentation**: See `/docs/` in project root
- **Engine API**: See `/docs/engine-api.md`
- **Language Spec**: See `/spec.md`
- **Extension Guide**: See `frontend/src/extensions/README.md`
- **Parser Details**: See `bardic/compiler/parser.py`
- **Engine Details**: See `bardic/runtime/engine.py`

---

## License

Part of the Bardic project. See project root for license information.
