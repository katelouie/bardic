# NiceGUI Tutorial: Minimal Bardic IF Player

**Goal:** Build a minimal interactive fiction player to test NiceGUI's developer experience.

**Time:** ~30-40 minutes

**What you'll build:** A simple locked room escape story with clickable choices.

---

## Step 1: Setup & Installation

### Install NiceGUI

```bash
pyenv activate bardic
pip install nicegui
```

### Create the project file

```bash
touch nicegui_test_player.py
```

Open `nicegui_test_player.py` in your editor.

---

## Step 2: Hello World (Verify It Works)

Let's start with the absolute minimum to verify NiceGUI works.

**Type this:**

```python
from nicegui import ui

ui.label('Hello, NiceGUI!')

ui.run()
```

**Run it:**

```bash
python nicegui_test_player.py
```

**You should see:**
- Server starts on http://localhost:8080
- Browser opens automatically (or visit that URL)
- A page with "Hello, NiceGUI!" text

**Press Ctrl+C in terminal to stop the server.**

**Feel check:** How was that? Easy startup?

---

## Step 3: Story Data Structure

Now let's add our story data. We'll hardcode the locked room escape.

**Replace everything in the file with:**

```python
from nicegui import ui

# Story data structure
STORY = {
    "Start": {
        "text": "You wake up in a dimly lit room. A door to your left, window to your right.",
        "choices": [
            {"text": "Check the door", "target": "Door"},
            {"text": "Look out window", "target": "Window"}
        ]
    },
    "Door": {
        "text": "The door is locked. A keyhole glints.",
        "choices": [
            {"text": "Pick the lock", "target": "Ending1"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Window": {
        "text": "Through the window: a moonlit garden. Window is ajar.",
        "choices": [
            {"text": "Climb out", "target": "Ending2"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Ending1": {
        "text": "Lock clicks open! Freedom!",
        "choices": []  # No choices = THE END
    },
    "Ending2": {
        "text": "You slip into the cool night air.",
        "choices": []  # No choices = THE END
    }
}

ui.label('Story data loaded!')

ui.run()
```

**Run it again:**

```bash
python nicegui_test_player.py
```

**You should see:** "Story data loaded!" (story is ready but not displayed yet)

**Stop the server (Ctrl+C).**

---

## Step 4: Display Current Passage

Now let's actually show the current passage text. We'll need to track state (which passage we're on).

**Replace everything with:**

```python
from nicegui import ui

# Story data
STORY = {
    "Start": {
        "text": "You wake up in a dimly lit room. A door to your left, window to your right.",
        "choices": [
            {"text": "Check the door", "target": "Door"},
            {"text": "Look out window", "target": "Window"}
        ]
    },
    "Door": {
        "text": "The door is locked. A keyhole glints.",
        "choices": [
            {"text": "Pick the lock", "target": "Ending1"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Window": {
        "text": "Through the window: a moonlit garden. Window is ajar.",
        "choices": [
            {"text": "Climb out", "target": "Ending2"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Ending1": {
        "text": "Lock clicks open! Freedom!",
        "choices": []
    },
    "Ending2": {
        "text": "You slip into the cool night air.",
        "choices": []
    }
}

# State: track current passage
current_passage_id = "Start"

# Display the current passage text
def show_passage():
    passage = STORY[current_passage_id]
    ui.label(passage["text"]).classes('text-xl mb-4')

# Build the UI
show_passage()

ui.run()
```

**Run it:**

```bash
python nicegui_test_player.py
```

**You should see:** The starting passage text displayed.

**Feel check:** Notice how you just call `ui.label()` and it appears? That's NiceGUI's imperative style.

**Stop server.**

---

## Step 5: Show Choices as Buttons

Let's add buttons for each choice. They won't do anything yet.

**Update the `show_passage()` function:**

```python
# Display the current passage text and choices
def show_passage():
    passage = STORY[current_passage_id]

    # Show passage text
    ui.label(passage["text"]).classes('text-xl mb-4')

    # Show choices as buttons
    for choice in passage["choices"]:
        ui.button(choice["text"])
```

**Full file should now look like:**

```python
from nicegui import ui

# Story data
STORY = {
    "Start": {
        "text": "You wake up in a dimly lit room. A door to your left, window to your right.",
        "choices": [
            {"text": "Check the door", "target": "Door"},
            {"text": "Look out window", "target": "Window"}
        ]
    },
    "Door": {
        "text": "The door is locked. A keyhole glints.",
        "choices": [
            {"text": "Pick the lock", "target": "Ending1"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Window": {
        "text": "Through the window: a moonlit garden. Window is ajar.",
        "choices": [
            {"text": "Climb out", "target": "Ending2"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Ending1": {
        "text": "Lock clicks open! Freedom!",
        "choices": []
    },
    "Ending2": {
        "text": "You slip into the cool night air.",
        "choices": []
    }
}

# State
current_passage_id = "Start"

# Display the current passage text and choices
def show_passage():
    passage = STORY[current_passage_id]

    # Show passage text
    ui.label(passage["text"]).classes('text-xl mb-4')

    # Show choices as buttons
    for choice in passage["choices"]:
        ui.button(choice["text"])

# Build UI
show_passage()

ui.run()
```

**Run it:**

```bash
python nicegui_test_player.py
```

**You should see:** Text + two buttons ("Check the door" and "Look out window"). They don't work yet.

**Stop server.**

---

## Step 6: Handle Choice Clicks & Update State

Now the important part: make buttons work! When clicked, navigate to the target passage.

**Here's the key concept in NiceGUI:** We need to:
1. Clear the current UI
2. Update the state
3. Rebuild the UI

**Update your code:**

```python
from nicegui import ui

# Story data
STORY = {
    "Start": {
        "text": "You wake up in a dimly lit room. A door to your left, window to your right.",
        "choices": [
            {"text": "Check the door", "target": "Door"},
            {"text": "Look out window", "target": "Window"}
        ]
    },
    "Door": {
        "text": "The door is locked. A keyhole glints.",
        "choices": [
            {"text": "Pick the lock", "target": "Ending1"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Window": {
        "text": "Through the window: a moonlit garden. Window is ajar.",
        "choices": [
            {"text": "Climb out", "target": "Ending2"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Ending1": {
        "text": "Lock clicks open! Freedom!",
        "choices": []
    },
    "Ending2": {
        "text": "You slip into the cool night air.",
        "choices": []
    }
}

# State
current_passage_id = "Start"

# Container that will hold our story UI
story_container = ui.column()

# Navigate to a new passage
def navigate_to(target_id):
    global current_passage_id
    current_passage_id = target_id
    update_ui()

# Rebuild the UI with current passage
def update_ui():
    story_container.clear()

    with story_container:
        passage = STORY[current_passage_id]

        # Show passage text
        ui.label(passage["text"]).classes('text-xl mb-4')

        # Show choices as buttons
        for choice in passage["choices"]:
            target = choice["target"]
            ui.button(choice["text"], on_click=lambda t=target: navigate_to(t))

# Initial render
update_ui()

ui.run()
```

**Run it:**

```bash
python nicegui_test_player.py
```

**Test it:**
- Click "Check the door" → should show door scene
- Click "Go back" → should return to start
- Try both paths to both endings

**Feel check:** How does the hot reload feel? How does the `story_container.clear()` + rebuild pattern feel?

**Stop server.**

---

## Step 7: Basic Styling

Let's make it not ugly. NiceGUI uses Tailwind CSS classes.

**Update `update_ui()` function:**

```python
# Rebuild the UI with current passage
def update_ui():
    story_container.clear()

    with story_container:
        passage = STORY[current_passage_id]

        # Show passage text (larger, with margin)
        ui.label(passage["text"]).classes('text-2xl mb-6 text-gray-700')

        # Show choices as buttons (styled)
        if passage["choices"]:
            for choice in passage["choices"]:
                target = choice["target"]
                ui.button(
                    choice["text"],
                    on_click=lambda t=target: navigate_to(t)
                ).classes('mb-2')
        else:
            # No choices = THE END
            ui.label("THE END").classes('text-xl text-gray-500 italic mt-4')
```

**Also add a container with styling at the top level:**

```python
# Create a centered, padded container
with ui.card().classes('max-w-2xl mx-auto mt-8 p-6'):
    ui.markdown('# Locked Room Escape').classes('mb-6')

    # Container that will hold our story UI
    story_container = ui.column()
```

**Full file:**

```python
from nicegui import ui

# Story data
STORY = {
    "Start": {
        "text": "You wake up in a dimly lit room. A door to your left, window to your right.",
        "choices": [
            {"text": "Check the door", "target": "Door"},
            {"text": "Look out window", "target": "Window"}
        ]
    },
    "Door": {
        "text": "The door is locked. A keyhole glints.",
        "choices": [
            {"text": "Pick the lock", "target": "Ending1"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Window": {
        "text": "Through the window: a moonlit garden. Window is ajar.",
        "choices": [
            {"text": "Climb out", "target": "Ending2"},
            {"text": "Go back", "target": "Start"}
        ]
    },
    "Ending1": {
        "text": "Lock clicks open! Freedom!",
        "choices": []
    },
    "Ending2": {
        "text": "You slip into the cool night air.",
        "choices": []
    }
}

# State
current_passage_id = "Start"

# Navigate to a new passage
def navigate_to(target_id):
    global current_passage_id
    current_passage_id = target_id
    update_ui()

# Rebuild the UI with current passage
def update_ui():
    story_container.clear()

    with story_container:
        passage = STORY[current_passage_id]

        # Show passage text (larger, with margin)
        ui.label(passage["text"]).classes('text-2xl mb-6 text-gray-700')

        # Show choices as buttons (styled)
        if passage["choices"]:
            for choice in passage["choices"]:
                target = choice["target"]
                ui.button(
                    choice["text"],
                    on_click=lambda t=target: navigate_to(t)
                ).classes('mb-2')
        else:
            # No choices = THE END
            ui.label("THE END").classes('text-xl text-gray-500 italic mt-4')

# Create a centered, padded container
with ui.card().classes('max-w-2xl mx-auto mt-8 p-6'):
    ui.markdown('# Locked Room Escape').classes('mb-6')

    # Container that will hold our story UI
    story_container = ui.column()

# Initial render
update_ui()

ui.run()
```

**Run it:**

```bash
python nicegui_test_player.py
```

**You should see:** A nicely styled card with centered content, bigger text, styled buttons, and "THE END" message at endings.

---

## Step 8: Done! Test Everything

Play through the story:
1. Start → Check door → Pick lock → Ending 1
2. Start → Look out window → Climb out → Ending 2
3. Try the "Go back" buttons

**Feel check questions:**
- How was the developer experience typing this?
- Did the hot reload work well when you saved changes?
- How does the `story_container.clear()` + rebuild pattern feel?
- Did the Tailwind classes feel natural?
- How's the code readability?
- Would you enjoy building a bigger app in this style?

---

## What You Just Built

You built a minimal IF player in NiceGUI with:
✅ Story data structure
✅ Display current passage
✅ Clickable choices
✅ State management (navigate between passages)
✅ Basic styling (Tailwind CSS)
✅ THE END state handling

**Total lines of code:** ~85 lines

---

## Key NiceGUI Patterns You Used

1. **Imperative UI:** Just call `ui.button()` and it appears
2. **Container + clear() + rebuild:** For reactive updates
3. **Tailwind CSS classes:** For styling
4. **Lambdas for click handlers:** `on_click=lambda: navigate_to(target)`
5. **Context managers:** `with ui.card():` for nesting

---

## Next Step

Now let's build the EXACT same app in Reflex and see how it compares!

When you're ready, open `tutorial-reflex-minimal-player.md`.

---

**Time to complete:** ~30-40 minutes

**How'd it feel?** Jot down notes about:
- What you liked
- What felt awkward
- What made you happy
- What annoyed you

Then we'll compare to Reflex! 🚀
