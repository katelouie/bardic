# Part 4: Building a "Game" with a Custom UI

You've built a working inventory system that runs in the terminal. That's awesome! But let's be honest—most players don't want to experience your story through command-line prompts.

In this tutorial, we'll transform your terminal game into a **beautiful web-based interface** using NiceGUI (a Python web framework) and Bardic's `@render` and `@input` directives.

**By the end of this tutorial, you will know how to:**

- Use `@input` to collect player information (like their name)
- Use `@render` to send data to custom UI components
- Create a simple NiceGUI web interface for your story
- Connect your Bardic story to a real web server

---

## What is NiceGUI?

NiceGUI is a Python web framework that lets you build modern, responsive web interfaces **entirely in Python**—no JavaScript required. It's perfect for Bardic because you can create custom components that visualize your game state.

## 1. Install NiceGUI

First, install NiceGUI in your project:

```bash
pip install nicegui
```

---

## 2. Your First `@input` Directive

Let's start by asking the player for their name. The `@input` directive creates a special input field that the UI can render.

Create a new file called **`story_with_ui.bard`**:

```bard
from item import Item

:: Start
@start
Welcome, traveler! Before we begin, what's your name?

@input name="player_name" label="Enter your name" placeholder="Hero"

+ [Continue] -> Greeting

:: Greeting
~ name = _inputs["player_name"]  # Save the input to a variable

Welcome, **{name}**! You stand in the Merchant's Quarter.

The autumn wind carries the scent of spices and roasting meat.

+ [Approach the vendor] -> Vendor_Desk
+ [Explore the market] -> Market

:: Market
The market is bustling with activity.

+ [Return to the main square] -> Greeting
```

**What's happening here?**

- `@input` creates an input field with the name `player_name`
- When the player submits their name, it becomes available as `_inputs["player_name"]`
- We save it to a permanent variable: `~ name = _inputs["player_name"]`
- We can now use `{name}` throughout the story

---

## 3. Your First `@render` Directive

The `@render` directive tells the UI to display a custom component. This is how you visualize complex data like inventory, stats, or card spreads.

Let's add inventory visualization to our story. Add this passage:

```bard
:: Vendor_Desk
~ brass_key = Item("Brass Key", "Opens the town library", weight=0.2)
~ iron_dagger = Item("Iron Dagger", "A basic weapon", weight=2.5)
~ health_potion = Item("Health Potion", "Restores 50 HP", weight=0.5)

The vendor lays out three items on the wooden counter.

+ [Ask about the dagger] -> Ask_Dagger
+ [Buy the brass key (3 gold)] -> Buy_Key
+ [Buy the dagger (5 gold)] -> Buy_Dagger
+ [View inventory] -> Inventory
+ [Leave] -> Greeting

:: Buy_Dagger
@py:
# Initialize inventory and gold if needed
if 'inventory' not in globals():
    inventory = []
if 'gold' not in globals():
    gold = 10

if gold >= 5:
    inventory.append(iron_dagger)
    gold -= 5
    purchase_success = True
else:
    purchase_success = False
@endpy

@if purchase_success:
"Sold!" The vendor hands you the dagger.

You now have **{gold} gold** remaining.

+ [View inventory] -> Inventory
+ [Continue shopping] -> Vendor_Desk

@else:
The vendor shakes her head. "You don't have enough gold, friend."

+ [Go back] -> Vendor_Desk
@endif

:: Buy_Key
@py:
if 'inventory' not in globals():
    inventory = []
if 'gold' not in globals():
    gold = 10

if gold >= 3:
    inventory.append(brass_key)
    gold -= 3
    purchase_success = True
else:
    purchase_success = False
@endpy

@if purchase_success:
The brass key is yours. "Good choice," says the vendor.

+ [View inventory] -> Inventory
+ [Continue shopping] -> Vendor_Desk
@else:
"Not enough coin for that one, I'm afraid."

+ [Go back] -> Vendor_Desk
@endif

:: Inventory
@py:
# Prepare inventory data for the UI
inventory_data = []
total_weight = 0

if 'inventory' in globals() and len(inventory) > 0:
    for item in inventory:
        inventory_data.append({
            'name': item.name,
            'description': item.description,
            'weight': item.weight
        })
        total_weight += item.weight
@endpy

# Send inventory to the UI component
@render render_inventory(inventory_data, total_weight, gold)

You check your inventory.

@if len(inventory_data) > 0:
You're carrying {len(inventory_data)} item<>
@if len(inventory_data) != 1:
s<>
@endif
, weighing {total_weight:.1f} lbs total.

@else:
Your inventory is empty.
@endif

+ [Back to vendor] -> Vendor_Desk
+ [Back to square] -> Greeting

:: Ask_Dagger
The vendor picks up the dagger.

"This? {iron_dagger.get_description()}. Standard issue, but reliable."

She sets it back down on the counter.

+ [Buy it (5 gold)] -> Buy_Dagger
+ [Back to items] -> Vendor_Desk
```

**What's happening here?**

- We use `@py:` blocks (note the colon!) for multi-line Python code
- We prepare the inventory as a list of dictionaries for the UI
- `@render render_inventory(...)` sends the data to a custom UI component
- We use the glue operator `<>` to handle singular/plural ("item" vs "items")
- We use `@if:` and `@endif` (with colons) for conditionals

---

## 4. Create the NiceGUI Web Interface

Now let's create the actual web server and UI components. Create a file called **`web_ui.py`**:

```python
from nicegui import ui
from bardic import BardEngine
import json

class GameUI:
    """Web-based UI for the Bardic story."""

    def __init__(self, story_file):
        # Load and compile the story
        with open(story_file, 'r') as f:
            story_code = f.read()

        self.engine = BardEngine()
        self.engine.load_story(story_code)

        # UI containers
        self.content_area = None
        self.choices_area = None
        self.inventory_display = None

    def render_inventory(self, items, total_weight, gold):
        """Render directive handler for inventory."""
        if self.inventory_display:
            self.inventory_display.clear()

            with self.inventory_display:
                ui.label(f'Gold: {gold}').classes('text-xl text-yellow-600 font-bold')

                if items:
                    ui.label(f'Total Weight: {total_weight:.1f} lbs').classes('text-sm text-gray-600')

                    with ui.card().classes('w-full'):
                        for item in items:
                            with ui.row().classes('items-center gap-4 p-2'):
                                ui.icon('inventory_2').classes('text-2xl')
                                with ui.column().classes('flex-grow'):
                                    ui.label(item['name']).classes('font-bold')
                                    ui.label(item['description']).classes('text-sm text-gray-600')
                                ui.label(f"{item['weight']} lbs").classes('text-sm')
                else:
                    ui.label('Empty').classes('text-gray-500 italic')

    def handle_render_directive(self, directive):
        """Process @render directives from Bardic."""
        component_name = directive['component']
        args = directive.get('args', {})

        if component_name == 'render_inventory':
            self.render_inventory(
                args.get('inventory_data', []),
                args.get('total_weight', 0),
                args.get('gold', 0)
            )

    def display_passage(self, output):
        """Display the current passage content and choices."""
        # Clear previous content
        self.content_area.clear()
        self.choices_area.clear()

        # Display text content
        with self.content_area:
            # Parse and display markdown content
            content_html = output.get('content', '')
            ui.markdown(content_html).classes('text-lg prose max-w-none')

            # Handle any @render directives
            for directive in output.get('render_directives', []):
                self.handle_render_directive(directive)

        # Display choices
        with self.choices_area:
            for i, choice in enumerate(output.get('choices', [])):
                ui.button(
                    choice['text'],
                    on_click=lambda idx=i: self.make_choice(idx)
                ).classes('w-full text-left bg-blue-600 hover:bg-blue-700 text-white')

            # Show input fields if present
            for input_field in output.get('inputs', []):
                self.show_input_field(input_field)

    def show_input_field(self, input_data):
        """Display an @input directive field."""
        name = input_data['name']
        label = input_data.get('label', 'Enter value')
        placeholder = input_data.get('placeholder', '')

        with self.choices_area:
            input_element = ui.input(label, placeholder=placeholder).classes('w-full')

            def submit_input():
                # Store the input value in the engine state
                self.engine.set_input(name, input_element.value)
                # Continue to next passage
                output = self.engine.continue_story()
                self.display_passage(output)

            ui.button('Submit', on_click=submit_input).classes('w-full bg-green-600 text-white')

    def make_choice(self, choice_index):
        """Handle player choice selection."""
        output = self.engine.choose(choice_index)
        self.display_passage(output)

    def start(self):
        """Initialize the web interface."""
        with ui.card().classes('w-full max-w-4xl mx-auto p-6'):
            ui.label('Merchant Quarter Adventure').classes('text-3xl font-bold mb-4')

            with ui.row().classes('w-full gap-4'):
                # Main content area (left side)
                with ui.column().classes('flex-grow'):
                    self.content_area = ui.column().classes('mb-4')
                    self.choices_area = ui.column().classes('gap-2')

                # Sidebar for inventory (right side)
                with ui.card().classes('w-64'):
                    ui.label('Inventory').classes('text-xl font-bold mb-2')
                    self.inventory_display = ui.column().classes('gap-2')

        # Start the story
        output = self.engine.start()
        self.display_passage(output)


def main():
    """Run the web server."""
    game = GameUI('story_with_ui.bard')
    game.start()
    ui.run(title='Bardic Adventure', port=8080)


if __name__ == '__main__':
    main()
```

**What's happening here?**

- We create a `GameUI` class that manages the web interface
- `render_inventory()` handles the `@render` directive from Bardic
- `show_input_field()` handles the `@input` directive
- NiceGUI creates a responsive layout with a main content area and inventory sidebar
- The engine processes choices and updates the display

---

## 5. Run Your Web Game

Now you can run your story in a web browser:

```bash
python web_ui.py
```

Open your browser to **<http://localhost:8080>** and play your game!

**What you'll see:**

- A clean, modern web interface
- The player name input field
- Story text with proper formatting
- Clickable choice buttons
- A live inventory sidebar that updates when you buy items
- Gold counter and weight tracking

---

## 6. Understanding the Flow

Here's how everything connects:

1. **Bardic story** (`story_with_ui.bard`) contains your narrative and game logic
2. **`@input` directive** creates input fields that the UI renders
3. **`@render` directive** sends data to Python functions in your UI
4. **NiceGUI** (`web_ui.py`) displays the content and handles player interactions
5. **Bardic engine** manages state and navigation between passages

```
┌─────────────────┐
│  story_with_ui  │
│     .bard       │
│                 │
│  @input name    │───┐
│  @render data   │   │
└─────────────────┘   │
         │            │
         v            v
┌─────────────────────────┐
│   BardEngine (Python)   │
│  - Compiles story       │
│  - Manages state        │
│  - Processes choices    │
└─────────────────────────┘
         │
         v
┌─────────────────────────┐
│  NiceGUI Web Interface  │
│  - Displays content     │
│  - Renders inventory    │
│  - Handles input        │
└─────────────────────────┘
```

---

## 7. Extending Your UI

You can create additional render handlers for other game elements:

```python
def render_character_stats(self, stats):
    """Display character stats."""
    with ui.card().classes('w-full p-4'):
        ui.label('Character Stats').classes('text-xl font-bold')
        for stat_name, value in stats.items():
            ui.linear_progress(value / 100).classes('w-full')
            ui.label(f'{stat_name}: {value}')

def render_map(self, location, connections):
    """Display a map of connected locations."""
    # Your map visualization code here
    pass
```

Then use them in your Bardic story:

```bard
@py:
character_stats = {
    'Health': health,
    'Stamina': stamina,
    'Magic': magic
}
@endpy

@render render_character_stats(character_stats)
```

---

## 🎉 Conclusion

You've successfully transformed your terminal game into a **beautiful web application**! You learned:

- How to use `@input` to collect player data
- How to use `@render` to visualize game state
- How to create a NiceGUI web interface
- How to connect Bardic to a Python web server
- How to handle render directives in your UI code

Your story is now accessible in a browser with a modern, responsive interface. But there's more to learn about managing larger projects...

**Next up:** In Part 5, we'll cover the tools you need to manage a real project: splitting files with `@include`, debugging with visualization tools, and organizing your story as it grows.

[← Back to Part 3](03_python_first.md) | [Continue to Part 5 →](05_finish_polish.md)
