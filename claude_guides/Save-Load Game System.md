Perfect! Now I can see the full structure. Let me create a comprehensive save/load system tutorial:

<artifact identifier="save-load-system-tutorial" type="text/markdown" title="Complete Save/Load System Implementation Tutorial"> # Implementing Save/Load System - Complete Guide

**Goal:** Build a full save/load system that persists game state, allowing players to save their progress and resume later.

**Time Estimate:** 60-90 minutes

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: ENGINE (Core Save/Load Logic)                 │
│  - Serialize engine state to JSON                       │
│  - Deserialize JSON to restore state                    │
│  - Methods: save_state(), load_state()                  │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: FASTAPI BACKEND (Storage & API)               │
│  - Save files to disk (JSON)                            │
│  - List available saves                                 │
│  - Load saves from disk                                 │
│  - Endpoints: /save, /load, /saves/list, /saves/delete  │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: REACT FRONTEND (UI)                           │
│  - Save button in UI                                    │
│  - Load screen with save slots                          │
│  - Auto-save support                                    │
│  - Save metadata display                                │
└─────────────────────────────────────────────────────────┘
```

---

## Part 1: Engine Save/Load (20 minutes)

### Step 1.1: Add Save Methods to BardEngine

**File:** `bardic/runtime/engine.py`

**Add these methods to the `BardEngine` class (after `reset_one_time_choices`):**

```python
def save_state(self) -> dict[str, Any]:
    """
    Serialize engine state to a dictionary that can be saved to JSON.
    
    Returns a complete snapshot of the current game state including:
    - Current passage ID
    - All variables in state
    - Used one-time choices
    - Story metadata for validation
    
    Returns:
        Dictionary containing all state needed to restore the game
        
    Example:
        >>> state = engine.save_state()
        >>> with open('save.json', 'w') as f:
        ...     json.dump(state, f)
    """
    return {
        "version": "1.0.0",  # Save format version
        "story_version": self.story.get("version", "unknown"),
        "story_name": self.story.get("name", "unknown"),
        "timestamp": self._get_timestamp(),
        "current_passage_id": self.current_passage_id,
        "state": self._serialize_state(self.state),
        "used_choices": list(self.used_choices),
        "metadata": {
            "passage_count": len(self.passages),
            "initial_passage": self.story["initial_passage"],
        }
    }

def load_state(self, save_data: dict[str, Any]) -> None:
    """
    Restore engine state from a saved dictionary.
    
    Validates the save data before loading to ensure compatibility.
    
    Args:
        save_data: Dictionary from save_state()
        
    Raises:
        ValueError: If save data is invalid or incompatible
        
    Example:
        >>> with open('save.json') as f:
        ...     save_data = json.load(f)
        >>> engine.load_state(save_data)
    """
    # Validate save format
    if not isinstance(save_data, dict):
        raise ValueError("Save data must be a dictionary")
    
    if "version" not in save_data:
        raise ValueError("Save data missing version field")
    
    # Validate story compatibility
    saved_story = save_data.get("story_name", "unknown")
    current_story = self.story.get("name", "unknown")
    
    if saved_story != current_story and saved_story != "unknown":
        print(f"Warning: Save is from a different story: '{saved_story}' vs '{current_story}'")
    
    # Validate passage exists
    target_passage = save_data.get("current_passage_id")
    if target_passage not in self.passages:
        raise ValueError(
            f"Save data references unknown passage: '{target_passage}'\n"
            f"Available passages: {', '.join(sorted(self.passages.keys())[:5])}..."
        )
    
    # Restore state
    self.state = self._deserialize_state(save_data.get("state", {}))
    self.used_choices = set(save_data.get("used_choices", []))
    
    # Navigate to saved passage (this re-renders with restored state)
    self.goto(target_passage)

def _serialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
    """
    Serialize state dictionary for JSON storage.
    
    Handles special cases:
    - Objects with __dict__ (convert to dict representation)
    - Lists and sets (ensure JSON compatible)
    - Custom types (convert to string representation)
    
    Args:
        state: Raw state dictionary
        
    Returns:
        JSON-serializable dictionary
    """
    serialized = {}
    
    for key, value in state.items():
        try:
            # Try to serialize directly (handles primitives)
            json.dumps(value)
            serialized[key] = value
        except (TypeError, ValueError):
            # Can't serialize directly - try special cases
            if hasattr(value, '__dict__'):
                # Object with attributes - store as dict with type info
                serialized[key] = {
                    "_type": type(value).__name__,
                    "_module": type(value).__module__,
                    "_data": {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
                }
            elif isinstance(value, (list, tuple)):
                # Recursively serialize collections
                serialized[key] = [self._serialize_value(v) for v in value]
            else:
                # Fallback: store string representation
                serialized[key] = {
                    "_type": "string_repr",
                    "_value": str(value)
                }
                print(f"Warning: Serializing {key} as string representation")
    
    return serialized

def _serialize_value(self, value: Any) -> Any:
    """Serialize a single value for JSON storage."""
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        if hasattr(value, '__dict__'):
            return {
                "_type": type(value).__name__,
                "_module": type(value).__module__,
                "_data": {k: v for k, v in value.__dict__.items() if not k.startswith('_')}
            }
        else:
            return str(value)

def _deserialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
    """
    Deserialize state from JSON storage.
    
    Attempts to reconstruct objects if their classes are available.
    Falls back to dict representation if class not found.
    
    Args:
        state: Serialized state dictionary
        
    Returns:
        Restored state dictionary
    """
    deserialized = {}
    
    for key, value in state.items():
        if isinstance(value, dict) and "_type" in value:
            # This was a special serialized object
            if value["_type"] == "string_repr":
                # Was stored as string - keep as string
                deserialized[key] = value["_value"]
            else:
                # Try to reconstruct the object
                try:
                    obj_type = value["_type"]
                    obj_module = value.get("_module", "builtins")
                    obj_data = value.get("_data", {})
                    
                    # Try to get the class from context
                    if obj_type in self.context:
                        cls = self.context[obj_type]
                        # Try to reconstruct using __dict__
                        obj = cls.__new__(cls)
                        obj.__dict__.update(obj_data)
                        deserialized[key] = obj
                    else:
                        # Class not available - keep as dict
                        deserialized[key] = obj_data
                        print(f"Warning: Could not reconstruct {obj_type}, keeping as dict")
                except Exception as e:
                    print(f"Warning: Failed to deserialize {key}: {e}")
                    deserialized[key] = value.get("_data", {})
        elif isinstance(value, list):
            # Recursively deserialize lists
            deserialized[key] = [self._deserialize_value(v) for v in value]
        else:
            # Primitive value - use directly
            deserialized[key] = value
    
    return deserialized

def _deserialize_value(self, value: Any) -> Any:
    """Deserialize a single value from JSON storage."""
    if isinstance(value, dict) and "_type" in value:
        obj_type = value["_type"]
        if obj_type in self.context:
            cls = self.context[obj_type]
            obj = cls.__new__(cls)
            obj.__dict__.update(value.get("_data", {}))
            return obj
        else:
            return value.get("_data", {})
    return value

def _get_timestamp(self) -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime
    return datetime.now().isoformat()

def get_save_metadata(self) -> dict[str, Any]:
    """
    Get metadata about the current save state without full serialization.
    
    Useful for displaying save slot information without loading the full save.
    
    Returns:
        Dictionary with save metadata (passage, timestamp, etc.)
    """
    return {
        "current_passage": self.current_passage_id,
        "timestamp": self._get_timestamp(),
        "story_name": self.story.get("name", "unknown"),
        "has_choices": self.has_choices(),
    }
```

**✅ Checkpoint 1: Engine can save/load state!**

Test it:

```python
from bardic import BardEngine
import json

# Create engine
with open('compiled_stories/test_story.json') as f:
    story = json.load(f)

engine = BardEngine(story)

# Play a bit
engine.choose(0)

# Save
save_data = engine.save_state()
print(json.dumps(save_data, indent=2))

# Continue playing
engine.choose(0)

# Load
engine.load_state(save_data)
print(f"Restored to: {engine.current_passage_id}")
```

---

## Part 2: FastAPI Backend (25 minutes)

### Step 2.1: Create Saves Directory

**Add to the top of `web-runtime/backend/main.py`:**

```python
# After STORIES_DIR definition
SAVES_DIR = PROJECT_ROOT / "saves"
SAVES_DIR.mkdir(exist_ok=True)
```

### Step 2.2: Add Save/Load Models

**Add after the existing `MakeChoiceRequest` model:**

```python
class SaveGameRequest(BaseModel):
    session_id: str
    save_name: str  # User-provided name like "Before boss fight"
    
class LoadGameRequest(BaseModel):
    session_id: str
    save_id: str  # Filename (without .json)
    story_id: str  # Which story to load

class DeleteSaveRequest(BaseModel):
    save_id: str
```

### Step 2.3: Add Save/Load Endpoints

**Add these endpoints to `main.py` (after the `/api/story/choose` endpoint):**

```python
@app.post("/api/story/save")
async def save_game(request: SaveGameRequest):
    """
    Save the current game state to disk.
    
    Creates a JSON file in the saves directory with:
    - Complete engine state
    - User-provided save name
    - Timestamp
    - Story metadata
    """
    # Get the engine for this session
    engine = sessions.get(request.session_id)
    
    if not engine:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        # Get save data from engine
        save_data = engine.save_state()
        
        # Add user metadata
        save_data["save_name"] = request.save_name
        save_data["user_timestamp"] = save_data["timestamp"]  # For display
        
        # Generate unique save ID (timestamp-based)
        from datetime import datetime
        save_id = f"save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        save_path = SAVES_DIR / f"{save_id}.json"
        
        # Write to disk
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        return {
            "success": True,
            "save_id": save_id,
            "save_path": str(save_path),
            "metadata": {
                "save_name": request.save_name,
                "passage": save_data["current_passage_id"],
                "timestamp": save_data["timestamp"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save: {str(e)}")


@app.post("/api/story/load")
async def load_game(request: LoadGameRequest):
    """
    Load a saved game from disk and restore the session.
    
    Creates a new engine instance with the saved state.
    """
    # Load the save file
    save_path = SAVES_DIR / f"{request.save_id}.json"
    
    if not save_path.exists():
        raise HTTPException(status_code=404, detail=f"Save file not found: {request.save_id}")
    
    try:
        # Read save data
        with open(save_path) as f:
            save_data = json.load(f)
        
        # Load the story
        story_path = STORIES_DIR / f"{request.story_id}.json"
        
        if not story_path.exists():
            raise HTTPException(status_code=404, detail=f"Story not found: {request.story_id}")
        
        with open(story_path) as f:
            story_data = json.load(f)
        
        # Create new engine
        context = get_default_context()
        engine = BardEngine(story_data, context=context)
        
        # Restore state
        engine.load_state(save_data)
        
        # Store in sessions
        sessions[request.session_id] = engine
        
        # Get current passage
        output = engine.current()
        
        return {
            "success": True,
            "content": output.content,
            "choices": [
                {"index": i, "text": choice["text"]}
                for i, choice in enumerate(output.choices)
            ],
            "passage_id": output.passage_id,
            "is_end": engine.is_end(),
            "render_directives": output.render_directives,
            "metadata": {
                "save_name": save_data.get("save_name", "Unnamed Save"),
                "timestamp": save_data.get("timestamp")
            }
        }
    
    except ValueError as e:
        # Invalid save data
        raise HTTPException(status_code=400, detail=f"Invalid save file: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load: {str(e)}")


@app.get("/api/saves/list")
async def list_saves():
    """
    List all available save files with their metadata.
    
    Returns summary information for display in the load menu.
    """
    saves = []
    
    for save_file in SAVES_DIR.glob("save_*.json"):
        try:
            with open(save_file) as f:
                save_data = json.load(f)
            
            saves.append({
                "save_id": save_file.stem,
                "save_name": save_data.get("save_name", "Unnamed Save"),
                "story_name": save_data.get("story_name", "Unknown"),
                "passage": save_data.get("current_passage_id", "Unknown"),
                "timestamp": save_data.get("timestamp"),
                "date_display": _format_timestamp(save_data.get("timestamp")),
            })
        except Exception as e:
            print(f"Warning: Could not read save file {save_file}: {e}")
            continue
    
    # Sort by timestamp (newest first)
    saves.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
    
    return {"saves": saves}


@app.delete("/api/saves/delete/{save_id}")
async def delete_save(save_id: str):
    """Delete a save file."""
    save_path = SAVES_DIR / f"{save_id}.json"
    
    if not save_path.exists():
        raise HTTPException(status_code=404, detail="Save not found")
    
    try:
        save_path.unlink()
        return {"success": True, "message": f"Deleted save: {save_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


def _format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp for display."""
    if not timestamp:
        return "Unknown date"
    
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return timestamp
```

**✅ Checkpoint 2: Backend has save/load endpoints!**

Test with curl:

```bash
# Save
curl -X POST http://localhost:8000/api/story/save \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "save_name": "My Save"}'

# List saves
curl http://localhost:8000/api/saves/list

# Load
curl -X POST http://localhost:8000/api/story/load \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test2", "save_id": "save_20250101_120000", "story_id": "test_story"}'
```

---

## Part 3: React Frontend (35 minutes)

### Step 3.1: Update App.jsx State

**Add new state variables after existing useState declarations:**

```javascript
function App() {
  // ... existing state ...
  const [showSaveMenu, setShowSaveMenu] = useState(false)
  const [showLoadMenu, setShowLoadMenu] = useState(false)
  const [saveName, setSaveName] = useState('')
  const [saves, setSaves] = useState([])
  const [saveMessage, setSaveMessage] = useState(null)
```

### Step 3.2: Add Save/Load Functions

**Add these functions after `makeChoice`:**

```javascript
const saveGame = async () => {
  if (!saveName.trim()) {
    setSaveMessage({ type: 'error', text: 'Please enter a save name' })
    return
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/story/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        save_name: saveName
      })
    })

    if (!response.ok) throw new Error('Failed to save game')

    const data = await response.json()
    console.log('Game saved:', data)

    setSaveMessage({ type: 'success', text: `Saved: ${saveName}` })
    setSaveName('')
    
    // Hide message after 3 seconds
    setTimeout(() => setSaveMessage(null), 3000)
  } catch (err) {
    console.error('Save failed:', err)
    setSaveMessage({ type: 'error', text: 'Failed to save game' })
  }
}

const loadSaves = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/saves/list')
    
    if (!response.ok) throw new Error('Failed to load saves')
    
    const data = await response.json()
    console.log('Saves loaded:', data.saves)
    setSaves(data.saves)
  } catch (err) {
    console.error('Failed to load saves:', err)
  }
}

const loadGame = async (saveId, storyId) => {
  setLoading(true)
  setShowLoadMenu(false)
  setShowStorySelect(false)

  try {
    const response = await fetch('http://127.0.0.1:8000/api/story/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        save_id: saveId,
        story_id: storyId
      })
    })

    if (!response.ok) throw new Error('Failed to load game')

    const data = await response.json()
    console.log('Game loaded:', data)
    setPassage(data)
    setSaveMessage({ type: 'success', text: `Loaded: ${data.metadata.save_name}` })
    setTimeout(() => setSaveMessage(null), 3000)
  } catch (err) {
    console.error('Load failed:', err)
    setError(err.message)
    setShowStorySelect(true)
  } finally {
    setLoading(false)
  }
}

const deleteSave = async (saveId) => {
  if (!confirm('Delete this save?')) return

  try {
    const response = await fetch(`http://127.0.0.1:8000/api/saves/delete/${saveId}`, {
      method: 'DELETE'
    })

    if (!response.ok) throw new Error('Failed to delete save')

    // Refresh save list
    loadSaves()
    setSaveMessage({ type: 'success', text: 'Save deleted' })
    setTimeout(() => setSaveMessage(null), 3000)
  } catch (err) {
    console.error('Delete failed:', err)
    setSaveMessage({ type: 'error', text: 'Failed to delete save' })
  }
}

const openSaveMenu = () => {
  setShowSaveMenu(true)
  setSaveName('')
  setSaveMessage(null)
}

const openLoadMenu = async () => {
  setShowLoadMenu(true)
  await loadSaves()
}
```

### Step 3.3: Add Save Menu UI

**Add this after the story selection screen (before "Starting state" check):**

```javascript
  // Save menu
  if (showSaveMenu && passage) {
    return (
      <div className="app">
        <div className="container">
          <header className="app-header">
            <h1>Save Game</h1>
          </header>

          <div className="save-menu">
            <div className="save-form">
              <label htmlFor="saveName">Save Name:</label>
              <input
                id="saveName"
                type="text"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                placeholder="e.g., Before boss fight"
                className="save-input"
                autoFocus
              />
              
              <div className="save-buttons">
                <button onClick={saveGame} className="save-button">
                  Save Game
                </button>
                <button onClick={() => setShowSaveMenu(false)} className="cancel-button">
                  Cancel
                </button>
              </div>
            </div>

            {saveMessage && (
              <div className={`save-message ${saveMessage.type}`}>
                {saveMessage.text}
              </div>
            )}

            <div className="save-info">
              <p><strong>Current Passage:</strong> {passage.passage_id}</p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Load menu
  if (showLoadMenu) {
    return (
      <div className="app">
        <div className="container">
          <header className="app-header">
            <h1>Load Game</h1>
          </header>

          <div className="load-menu">
            {saves.length === 0 ? (
              <p className="no-saves">No saved games found</p>
            ) : (
              <div className="save-list">
                {saves.map((save) => (
                  <div key={save.save_id} className="save-slot">
                    <div className="save-slot-info">
                      <h3>{save.save_name}</h3>
                      <p className="save-detail">Story: {save.story_name}</p>
                      <p className="save-detail">Passage: {save.passage}</p>
                      <p className="save-date">{save.date_display}</p>
                    </div>
                    <div className="save-slot-actions">
                      <button
                        onClick={() => {
                          // Extract story ID from story name (reverse of title formatting)
                          const storyId = save.story_name.toLowerCase().replace(/ /g, '_')
                          loadGame(save.save_id, storyId)
                        }}
                        className="load-button"
                      >
                        Load
                      </button>
                      <button
                        onClick={() => deleteSave(save.save_id)}
                        className="delete-button"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <button onClick={() => setShowLoadMenu(false)} className="back-button">
              Back
            </button>

            {saveMessage && (
              <div className={`save-message ${saveMessage.type}`}>
                {saveMessage.text}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }
```

### Step 3.4: Add Save/Load Buttons to Story Screen

**Update the footer section in the story playthrough return:**

```javascript
        <footer className="app-footer">
          <div className="footer-buttons">
            <button onClick={openSaveMenu} className="small-button">
              💾 Save Game
            </button>
            <button onClick={openLoadMenu} className="small-button">
              📁 Load Game
            </button>
            <button onClick={startStory} className="small-button">
              🔄 Restart Story
            </button>
          </div>
        </footer>
```

### Step 3.5: Add Load Option to Story Select

**Update the story select screen to include a load button:**

```javascript
// In the story selection screen, after the start button:
            {selectedStory && (
              <>
                <button onClick={startStory} className="start-button">
                  Start Story
                </button>
                <button onClick={openLoadMenu} className="load-from-menu-button">
                  Load Saved Game
                </button>
              </>
            )}
```

---

## Part 4: Styling (10 minutes)

### Step 4.1: Add CSS for Save/Load UI

**Add to `App.css`:**

```css
/* Save/Load Menus */
.save-menu,
.load-menu {
  background: rgba(37, 37, 37, 0.8);
  padding: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(168, 85, 247, 0.2);
}

/* Save Form */
.save-form {
  margin-bottom: 30px;
}

.save-form label {
  display: block;
  color: #a855f7;
  margin-bottom: 10px;
  font-size: 1.1rem;
  font-weight: 600;
}

.save-input {
  width: 100%;
  padding: 15px;
  background: rgba(51, 51, 51, 0.8);
  border: 2px solid #a855f7;
  border-radius: 8px;
  color: #e0e0e0;
  font-size: 1rem;
  margin-bottom: 20px;
  transition: border-color 0.3s;
}

.save-input:focus {
  outline: none;
  border-color: #c084fc;
  background: rgba(58, 58, 58, 0.9);
}

.save-buttons {
  display: flex;
  gap: 15px;
}

.save-button,
.cancel-button,
.load-button,
.delete-button,
.back-button {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-button,
.load-button {
  background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%);
  color: #ffffff;
  flex: 1;
}

.save-button:hover,
.load-button:hover {
  background: linear-gradient(135deg, #c084fc 0%, #a855f7 100%);
  transform: translateY(-2px);
}

.cancel-button,
.back-button {
  background: rgba(51, 51, 51, 0.8);
  color: #e0e0e0;
  border: 2px solid #666;
  flex: 1;
}

.cancel-button:hover,
.back-button:hover {
  background: rgba(58, 58, 58, 0.9);
  border-color: #888;
}

.delete-button {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 2px solid #ff6b6b;
  padding: 8px 16px;
  font-size: 0.9rem;
}

.delete-button:hover {
  background: rgba(255, 107, 107, 0.3);
  border-color: #ff8888;
}

/* Save Message */
.save-message {
  padding: 15px 20px;
  border-radius: 8px;
  margin-top: 20px;
  font-size: 1rem;
  text-align: center;
  animation: fadeIn 0.3s ease-out;
}

.save-message.success {
  background: rgba(81, 207, 102, 0.2);
  border: 2px solid #51cf66;
  color: #51cf66;
}

.save-message.error {
  background: rgba(255, 107, 107, 0.2);
  border: 2px solid #ff6b6b;
  color: #ff6b6b;
}

/* Save Info */
.save-info {
  margin-top: 30px;
  padding: 20px;
  background: rgba(26, 26, 26, 0.6);
  border-radius: 8px;
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.save-info p {
  color: #c084fc;
  margin: 5px 0;
}

/* Save List */
.save-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 30px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 10px;
}

.save-list::-webkit-scrollbar {
  width: 8px;
}

.save-list::-webkit-scrollbar-track {
  background: rgba(26, 26, 26, 0.6);
  border-radius: 4px;
}

.save-list::-webkit-scrollbar-thumb {
  background: #a855f7;
  border-radius: 4px;
}

.save-slot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: rgba(51, 51, 51, 0.8);
  border: 2px solid rgba(168, 85, 247, 0.3);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.save-slot:hover {
  background: rgba(58, 58, 58, 0.9);
  border-color: #a855f7;
  transform: translateX(5px);
}

.save-slot-info {
  flex: 1;
}

.save-slot-info h3 {
  color: #a855f7;
  margin-bottom: 8px;
  font-size: 1.2rem;
}

.save-detail {
  color: #c084fc;
  font-size: 0.9rem;
  margin: 3px 0;
}

.save-date {
  color: #888;
  font-size: 0.85rem;
  margin-top: 8px;
}

.save-slot-actions {
  display: flex;
  gap: 10px;
}

.no-saves {
  text-align: center;
  color: #888;
  padding: 40px;
  font-size: 1.1rem;
}

/* Footer Buttons */
.footer-buttons {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.load-from-menu-button {
  width: 100%;
  padding: 15px;
  margin-top: 10px;
  background: rgba(51, 51, 51, 0.8);
  color: #a855f7;
  border: 2px solid #a855f7;
  border-radius: 12px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.load-from-menu-button:hover {
  background: rgba(168, 85, 247, 0.2);
  border-color: #c084fc;
  transform: scale(1.02);
}

/* Responsive */
@media (max-width: 768px) {
  .save-slot {
    flex-direction: column;
    gap: 15px;
  }

  .save-slot-actions {
    width: 100%;
  }

  .save-button,
  .cancel-button,
  .load-button,
  .delete-button {
    flex: 1;
  }

  .footer-buttons {
    flex-direction: column;
  }

  .footer-buttons .small-button {
    width: 100%;
  }
}
```

**✅ Checkpoint 3: Frontend save/load UI complete!**

---

## Part 5: Test Everything! (10 minutes)

### Test Story

**Create:** `stories/test/test_save_load.bard`

```bard
:: Start
~ gold = 100
~ health = 100
~ inventory = []

**The Adventure Begins**

You start with {gold} gold and {health} health.

* [Buy sword (50 gold)] -> BuySword
* [Buy potion (30 gold)] -> BuyPotion
+ [Continue adventure] -> Forest

:: BuySword
~ gold = gold - 50
~ inventory = inventory + ["sword"]

You buy a shiny sword!

Gold remaining: {gold}

+ [Continue] -> Start

:: BuyPotion
~ gold = gold - 30
~ inventory = inventory + ["potion"]

You buy a healing potion!

Gold remaining: {gold}

+ [Continue] -> Start

:: Forest
**The Dark Forest**

Health: {health}
Gold: {gold}
Inventory: {", ".join(inventory) if inventory else "Empty"}

You enter a dark forest...

+ [Fight monster] -> Combat
+ [Return to town] -> Start

:: Combat
~ health = health - 20

You fight a monster! Lost 20 health.

<<if health <= 0>>
-> Death
<<endif>>

Health remaining: {health}

+ [Continue] -> Forest

:: Death
**Game Over**

You have died!

Final stats:
- Health: {health}
- Gold: {gold}
- Inventory: {", ".join(inventory) if inventory else "Empty"}
```

### Test Flow

1. **Compile:**

```bash
bardic compile stories/test/test_save_load.bard -o compiled_stories/test_save_load.json
```

2. **Start server:**

```bash
bardic serve
```

3. **Test in browser:**
    
    - Select "Test Save Load"
    - Buy sword (one-time choice disappears!)
    - Buy potion
    - Click **💾 Save Game**
    - Name it "Before forest"
    - Continue to forest
    - Fight monster (lose health)
    - Click **📁 Load Game**
    - Load "Before forest"
    - **Check:** Should be back at Start with full health!
4. **Test save persistence:**
    
    - Close browser
    - Restart server
    - Click **📁 Load Game** on menu
    - Load your save
    - **Check:** Everything restored!

---

## Part 6: Advanced Features (Optional)

### 6.1: Auto-Save

**Add to App.jsx after `makeChoice`:**

```javascript
const autoSave = async () => {
  try {
    await fetch('http://127.0.0.1:8000/api/story/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        save_name: '__autosave__'
      })
    })
    console.log('Auto-saved')
  } catch (err) {
    console.error('Auto-save failed:', err)
  }
}

// Trigger auto-save after each choice
const makeChoiceWithAutoSave = async (choiceIndex) => {
  await makeChoice(choiceIndex)
  await autoSave()
}

// Use makeChoiceWithAutoSave instead of makeChoice in buttons
```

### 6.2: Save Slots (Multiple Saves)

Already supported! The save system creates unique files for each save.

### 6.3: Cloud Saves

**Add to backend:**

```python
# Add to main.py
import boto3  # If using AWS S3

@app.post("/api/story/save/cloud")
async def save_to_cloud(request: SaveGameRequest):
    """Upload save to cloud storage."""
    # Implementation depends on your cloud provider
    # AWS S3, Google Cloud Storage, etc.
    pass
```

---

## Troubleshooting

### Issue: "Session not found" when saving

**Fix:** Make sure the session_id is consistent between requests.

```javascript
// Check sessionId generation
console.log('Session ID:', sessionId)
```

### Issue: Objects don't restore correctly

**Fix:** Make sure object classes are in context:

```python
context = {
    'Card': Card,
    'Client': Client,
    # ... all your custom classes
}
```

### Issue: Save file corrupted

**Check:**

1. Is the JSON valid?
2. Are all values JSON-serializable?
3. Debug with:

```python
import json
try:
    json.dumps(save_data)
except TypeError as e:
    print(f"Not serializable: {e}")
```

---

## Summary

**What We Built:**

1. **Engine Layer:**
    
    - `save_state()` - Serialize everything
    - `load_state()` - Restore everything
    - Object serialization/deserialization
2. **Backend Layer:**
    
    - `/api/story/save` - Save to disk
    - `/api/story/load` - Load from disk
    - `/api/saves/list` - List all saves
    - `/api/saves/delete` - Delete save
3. **Frontend Layer:**
    
    - Save menu with name input
    - Load menu with save slots
    - Delete confirmation
    - Success/error messages

**Benefits:**

- ✅ Save anywhere in the story
- ✅ Multiple save slots
- ✅ Persistent across browser restarts
- ✅ Preserves one-time choices
- ✅ Easy to extend (cloud saves, auto-save, etc.)

**Ready for production save/load!** 🎉 </artifact>

There you go! A complete, production-ready save/load system. The architecture is solid:

**Key Design Decisions:**

1. **JSON Storage** - Easy to inspect, debug, and version control
2. **Separate Saves Directory** - Keeps saves organized
3. **Timestamp-based IDs** - Unique, sortable save files
4. **Full State Serialization** - Everything needed to restore
5. **Object Support** - Handles custom Python objects via context

**What's Great:**

- ✅ **Backwards compatible** - Old stories work without changes
- ✅ **Extensible** - Easy to add cloud saves, compression, encryption
- ✅ **User-friendly** - Named saves, timestamps, metadata
- ✅ **Developer-friendly** - Clear error messages, debugging support

Want to implement it? I can guide you through each step! The tutorial is designed to be followed sequentially, with checkpoints at each stage. 🚀