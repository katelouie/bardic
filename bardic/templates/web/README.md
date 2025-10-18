# Bardic Web Template

A complete FastAPI + React web application for running Bardic interactive fiction stories in the browser.

## Features

- 🚀 **FastAPI Backend** - RESTful API with session management
- ⚛️ **React Frontend** - Modern SPA with Vite
- 📦 **@render Directives** - Custom React components in stories
- 🔌 **Extensions System** - Add custom context functions and API routes
- 🎨 **Production Ready** - Complete architecture for deployment

## Quick Start

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 3. Compile Your Story

```bash
bardic compile example.bard -o frontend/public/stories/example.json
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

Backend runs on `http://127.0.0.1:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend runs on `http://localhost:5173`

Open `http://localhost:5173` in your browser!

## Project Structure

```
your-game/
├── backend/
│   ├── main.py              # FastAPI server & API endpoints
│   └── extensions/
│       ├── context.py       # Custom context functions for stories
│       └── routes.py        # Custom API endpoints (optional)
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main React component
│   │   ├── StoryDisplay.jsx # Story rendering
│   │   └── components/      # Custom React components for @render
│   ├── public/
│   │   └── stories/         # Compiled .json stories go here
│   ├── package.json
│   └── vite.config.js
├── requirements.txt         # Backend Python dependencies
└── README.md               # This file
```

## Architecture

**Backend (FastAPI):**
- Hosts BardEngine for story execution
- Manages sessions (one engine instance per session)
- Exposes REST API endpoints for story interaction
- Provides custom context functions via extensions

**Frontend (React):**
- Purely presentational - no game logic
- Displays story content and choices
- Sends choice selections to backend
- Renders custom components via @render directives

**Key Principle:** Backend does all story execution and state management. Frontend just displays what the backend sends.

## API Endpoints

- `POST /api/story/start` - Start a new story session
- `GET /api/story/current` - Get current passage
- `POST /api/story/choose` - Make a choice
- `POST /api/story/save` - Save game state
- `POST /api/story/load` - Load game state
- `GET /api/saves/list` - List all saves
- `DELETE /api/saves/delete/{save_id}` - Delete a save

## Writing Stories

Place your `.bard` files anywhere, then compile them to `frontend/public/stories/`:

```bash
bardic compile my_story.bard -o frontend/public/stories/my_story.json
```

### Using @render Directives

Create custom React components for rich interactions:

**In your story:**
```bard
@render show_card(card_name="The Fool", orientation="upright")
```

**In frontend/src/components/:**
Create `CardDisplay.jsx` and register it in the component registry.

See `README-FULL.md` for complete @render directive documentation.

## Extensions System

### Custom Context Functions

Add Python functions your stories can call:

**backend/extensions/context.py:**
```python
def get_game_context():
    return {
        'calculate_damage': lambda attacker, defender: ...,
        'roll_dice': lambda sides: ...
    }
```

**In your story:**
```bard
<<py>>
damage = calculate_damage(player, enemy)
<<endpy>>
```

### Custom API Routes

Add your own endpoints:

**backend/extensions/routes.py:**
```python
def register_custom_routes(app):
    @app.get("/api/custom/endpoint")
    async def custom_endpoint():
        return {"data": "..."}
```

## Development

### Frontend Development

```bash
cd frontend
npm run dev      # Development server
npm run build    # Production build
npm run preview  # Preview production build
```

### Backend Development

The backend auto-reloads on code changes when running with `python main.py`.

## Deployment

### Backend

Deploy with Uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend

Build and serve static files:
```bash
cd frontend
npm run build
# Serve dist/ folder with nginx, Apache, or static hosting
```

## Need Help?

- [Bardic Documentation](https://github.com/katelouie/bardic)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)

## Example Game

Check out [Arcanum](https://github.com/katelouie/arcanum-game) for a complete example built with Bardic!
