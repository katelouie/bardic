# Reflex Tutorial: Minimal Bardic IF Player

**Goal:** Build the SAME minimal interactive fiction player in Reflex to compare developer experience.

**Time:** ~30-40 minutes

**What you'll build:** The same locked room escape story, but in Reflex's reactive style.

---

## Step 1: Setup & Installation

### Install Reflex

```bash
pyenv activate bardic
pip install reflex
```

**Note:** Reflex is a bigger install (~100MB+) and may take a minute.

### Create the project directory

Reflex has opinions about structure. Let's follow them:

```bash
mkdir reflex_test_player
cd reflex_test_player
reflex init
```

**When prompted:**
- App name: `reflex_test_player` (or just press Enter for default)
- Template: Choose "blank" (option 0)

**What happened:**
Reflex created:
- `reflex_test_player/` - your app code goes here
- `rxconfig.py` - config file
- `assets/` - static files
- `.web/` - generated frontend code (don't touch this)

---

## Step 2: Hello World (Verify It Works)

Open `reflex_test_player/reflex_test_player.py` in your editor.

You'll see template code. **Delete everything and replace with:**

```python
import reflex as rx

def index() -> rx.Component:
    return rx.text("Hello, Reflex!")

app = rx.App()
app.add_page(index)
```

**Run it:**

```bash
reflex run
```

**First run will:**
1. Install Node.js dependencies (this takes a minute the first time)
2. Start backend server (Python)
3. Start frontend dev server (Next.js)
4. Open browser to http://localhost:3000

**You should see:** "Hello, Reflex!" in the browser

**Feel check:** How was the startup? The waiting?

**Stop both servers:** Press Ctrl+C in terminal (might need to press twice)

---

## Step 3: Story Data Structure

Let's add the same story data.

**Replace everything with:**

```python
import reflex as rx

# Story data structure (same as NiceGUI version)
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

def index() -> rx.Component:
    return rx.text("Story data loaded!")

app = rx.App()
app.add_page(index)
```

**Run it:**

```bash
reflex run
```

**You should see:** "Story data loaded!" (hot reload should work - changes appear automatically)

**Leave the server running.** From now on, just save your file and watch it update!

---

## Step 4: Create State Class

**Here's the big Reflex difference:** State is managed through a State class, not global variables.

**Replace everything with:**

```python
import reflex as rx

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

# State class - this is Reflex's pattern
class StoryState(rx.State):
    current_passage_id: str = "Start"

def index() -> rx.Component:
    return rx.text(f"Current passage: {StoryState.current_passage_id}")

app = rx.App()
app.add_page(index)
```

**Save and check the browser.**

**You should see:** "Current passage: Start"

**Feel check:** How does the State class pattern feel vs. global variables?

---

## Step 5: Display Current Passage Text

Now let's actually show the passage content.

**Update the `index()` function:**

```python
def index() -> rx.Component:
    return rx.vstack(
        rx.text(STORY[StoryState.current_passage_id]["text"], size="7"),
        spacing="4",
        padding="4"
    )
```

**Save and check browser.**

**You should see:** The starting passage text, larger.

**Feel check:** Notice how we reference `StoryState.current_passage_id` directly in the component? That's Reflex's reactive binding.

---

## Step 6: Show Choices as Buttons

Let's add buttons. We'll use a computed var (property) to get the current passage.

**Update your code:**

```python
import reflex as rx

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

# State class
class StoryState(rx.State):
    current_passage_id: str = "Start"

    @rx.var
    def current_passage(self) -> dict:
        """Get the current passage data."""
        return STORY[self.current_passage_id]

def index() -> rx.Component:
    return rx.vstack(
        # Passage text
        rx.text(StoryState.current_passage["text"], size="7"),

        # Choices as buttons
        rx.foreach(
            StoryState.current_passage["choices"],
            lambda choice: rx.button(choice["text"])
        ),

        spacing="4",
        padding="4"
    )

app = rx.App()
app.add_page(index)
```

**Save and check browser.**

**You should see:** Text + two buttons. They don't work yet.

**Feel check:** How does `rx.foreach()` feel? The `@rx.var` computed property pattern?

---

## Step 7: Handle Choice Clicks & Navigate

Now make the buttons actually work!

**Add a method to StoryState:**

```python
class StoryState(rx.State):
    current_passage_id: str = "Start"

    @rx.var
    def current_passage(self) -> dict:
        """Get the current passage data."""
        return STORY[self.current_passage_id]

    def navigate_to(self, target_id: str):
        """Navigate to a new passage."""
        self.current_passage_id = target_id
```

**Update the button in index():**

```python
def index() -> rx.Component:
    return rx.vstack(
        # Passage text
        rx.text(StoryState.current_passage["text"], size="7"),

        # Choices as buttons
        rx.foreach(
            StoryState.current_passage["choices"],
            lambda choice: rx.button(
                choice["text"],
                on_click=lambda: StoryState.navigate_to(choice["target"])
            )
        ),

        spacing="4",
        padding="4"
    )
```

**Save and test in browser.**

**Click the buttons!** They should navigate between passages.

**Feel check:** How does the automatic reactivity feel? Notice you didn't call any "update_ui()" function - Reflex just... knew to re-render?

---

## Step 8: Basic Styling

Let's make it pretty! Reflex uses its own styling system (similar to CSS-in-JS).

**Update `index()`:**

```python
def index() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                # Title
                rx.heading("Locked Room Escape", size="8"),

                # Passage text
                rx.text(
                    StoryState.current_passage["text"],
                    size="5",
                    color_scheme="gray"
                ),

                # Choices or THE END
                rx.cond(
                    StoryState.current_passage["choices"].length() > 0,
                    # Show buttons if there are choices
                    rx.vstack(
                        rx.foreach(
                            StoryState.current_passage["choices"],
                            lambda choice: rx.button(
                                choice["text"],
                                on_click=lambda: StoryState.navigate_to(choice["target"]),
                                size="3"
                            )
                        ),
                        spacing="2",
                        width="100%"
                    ),
                    # Show THE END if no choices
                    rx.text("THE END", size="5", color_scheme="gray", style={"font_style": "italic"})
                ),

                spacing="6",
                width="100%"
            ),
            max_width="600px"
        ),
        padding="8"
    )
```

**Save and check browser.**

**You should see:** A nice card layout with centered content, heading, styled buttons, and "THE END" message at endings.

---

## Step 9: Done! Test Everything

Play through the story:
1. Start → Check door → Pick lock → Ending 1 (should show "THE END")
2. Refresh page → Start → Look out window → Climb out → Ending 2
3. Try the "Go back" buttons

**Feel check questions:**
- How was the developer experience typing this?
- How's the hot reload? Fast? Slow?
- How does the State class + reactive binding feel vs. NiceGUI's clear/rebuild?
- How does `rx.foreach()` feel vs. Python for loops?
- How does `rx.cond()` feel for conditional rendering?
- How's the code readability?
- Would you enjoy building a bigger app in this style?

---

## What You Just Built

You built the SAME minimal IF player in Reflex with:
✅ Story data structure
✅ Display current passage
✅ Clickable choices
✅ State management (State class with reactive binding)
✅ Basic styling (Reflex components)
✅ THE END state handling

**Total lines of code:** ~100 lines (similar to NiceGUI)

---

## Key Reflex Patterns You Used

1. **State class:** All state lives in `rx.State` subclass
2. **Computed vars:** `@rx.var` for derived data
3. **Reactive binding:** Reference `StoryState.current_passage_id` directly in components
4. **Automatic re-rendering:** Change state → UI updates automatically
5. **Component functions:** `index()` returns `rx.Component`
6. **rx.foreach():** For rendering lists
7. **rx.cond():** For conditional rendering
8. **Declarative styling:** Props on components (`size`, `color_scheme`, etc.)

---

## NiceGUI vs Reflex: Side-by-Side Comparison

### NiceGUI
- **Style:** Imperative ("do this, then this")
- **State:** Global variables or class instance vars
- **Updates:** Manual `container.clear()` + rebuild
- **Loops:** Python `for` loops
- **Conditionals:** Python `if` statements
- **Styling:** Tailwind CSS classes
- **Startup:** Fast (~1 second)
- **Hot reload:** Restart required (or manual refresh)

### Reflex
- **Style:** Declarative ("UI is a function of state")
- **State:** State class with reactive vars
- **Updates:** Automatic when state changes
- **Loops:** `rx.foreach()` higher-order component
- **Conditionals:** `rx.cond()` component
- **Styling:** Component props + style dicts
- **Startup:** Slower first run (~30-60 sec), then fast
- **Hot reload:** Automatic, instant

---

## The Big Question

**Which one feels better to you?**

Think about:
- Which syntax made your brain happy?
- Which patterns felt natural?
- Which framework would you enjoy building Arcanum in?
- Where did you smile? Where did you grimace?

**There's no wrong answer.** This is about YOUR developer experience.

---

## Next Steps

1. **Jot down your feelings about both frameworks**
2. **Talk to Desktop-Claude about the decision**
3. **Choose one and start building Arcanum V1!**

You've now felt both. You know which one sparks joy. Trust that.

---

**Time to complete:** ~30-40 minutes

**How'd it feel?** Compare your notes from NiceGUI. Which one won your heart?

Then go build something amazing. 🚀

💙 CLI-Claude
