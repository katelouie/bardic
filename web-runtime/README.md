# Bardic Generic Web Runtime

A reusable FastAPI + React application that can run ANY Bardic story.

## Architecture

```sh
web-runtime/
├── backend/ # FastAPI server
│ └── main.py # API endpoints
└── frontend/ # React app
└── src/ ├── App.jsx # Story player component
└── App.css # Styles
````

## Running Locally

### Backend (Terminal 1)

```bash
cd web-runtime/backend
uvicorn main:app --reload
```

Runs on <http://127.0.0.1:8000>

### Frontend (Terminal 2)

```bash
cd web-runtime/frontend
npm run dev
```

Runs on <http://localhost:5173>

## Adding Stories

1. Compile your `.bard` file:

    ```bash
    bardic compile my_story.bard
    ```

2. Copy the `.json` to `compiled_stories/`:

    ```bash
    cp my_story.json compiled_stories/
    ```

3. Refresh the browser - your story will appear in the list!

## Adding Custom Context

Edit `web-runtime/backend/main.py` and update the `get_default_context()` function:

```python
def get_default_context():
    return {
        'my_function': lambda x: x * 2,
        # Add your game-specific functions here
    }
```

## API Endpoints

- `GET /api/stories` - List available stories
- `POST /api/story/start` - Start a new story session
- `POST /api/story/choose` - Make a choice and advance
