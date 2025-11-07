# Part 5: Finishing & Polishing Your Story

Congratulations! You've built a working web-based game with inventory management, player input, and custom UI components. But as your story grows beyond a few passages, you'll need tools to keep it organized and debuggable.

In this final tutorial, we'll cover the **essential techniques for managing real projects**.

**By the end of this tutorial, you will know how to:**

- Split your story into multiple files using `@include`
- Organize your project with namespaced passages
- Use the `bardic graph` command to visualize your story structure
- Debug common issues efficiently
- Write maintainable, scalable interactive fiction

---

## 1. File Organization with `@include`

As your story grows, keeping everything in one file becomes unwieldy. The `@include` directive lets you split your story into logical modules.

### The Problem: One Giant File

```bard
# story.bard - 500+ lines, getting hard to navigate!

:: Start
...

:: Vendor_Desk
...

:: Market
...

:: Inn
...

:: Tavern_Floor1
...

:: Tavern_Floor2
...

# ... 50 more passages ...
```

### The Solution: Organized Files

Create a project structure like this:

```sh
my_game/
├── main.bard              # Entry point, imports, setup
├── locations/
│   ├── market.bard        # All market-related passages
│   ├── tavern.bard        # All tavern-related passages
│   └── inn.bard           # All inn-related passages
├── characters/
│   ├── vendor.bard        # Vendor interactions
│   └── innkeeper.bard     # Innkeeper dialogue
├── shared/
│   ├── inventory.bard     # Reusable inventory passages
│   └── combat.bard        # Combat mechanics
└── item.py                # Python classes
```

### Create the Main File

**`main.bard`:**

```bard
from item import Item

# Include all your sub-files
@include locations/market.bard
@include locations/tavern.bard
@include locations/inn.bard
@include characters/vendor.bard
@include characters/innkeeper.bard
@include shared/inventory.bard

:: Start
@start
Welcome, traveler! What's your name?

@input name="player_name" label="Enter your name" placeholder="Hero"

+ [Continue] -> Greeting

:: Greeting
~ name = player_name
~ gold = 10
~ inventory = []

Welcome, **{name}**!

You stand at the crossroads of the Merchant's Quarter.

+ [Visit the market] -> Market.Entrance
+ [Enter the tavern] -> Tavern.MainFloor
+ [Check the inn] -> Inn.Lobby
```

### Create Location Files

**`locations/market.bard`:**

```bard
:: Market.Entrance
The market bustles with activity. Vendors call out their wares.

+ [Approach the weapon vendor] -> Market.Vendor_Desk
+ [Browse the food stalls] -> Market.Food_Stalls
+ [Leave] -> Greeting

:: Market.Vendor_Desk
~ brass_key = Item("Brass Key", "Opens the town library", weight=0.2)
~ iron_dagger = Item("Iron Dagger", "A basic weapon", weight=2.5)

The weapon vendor nods at you.

"Looking for something sharp, friend?"

+ [Ask about the dagger] -> Market.Ask_Dagger
+ [Buy the key (3 gold)] -> Market.Buy_Key
+ [Buy the dagger (5 gold)] -> Market.Buy_Dagger
+ [View inventory] -> Inventory.Display
+ [Leave] -> Market.Entrance

:: Market.Ask_Dagger
The vendor picks up the dagger.

"This? {iron_dagger.get_description()}. Standard issue, but reliable."

+ [Buy it (5 gold)] -> Market.Buy_Dagger
+ [Back] -> Market.Vendor_Desk

:: Market.Buy_Dagger
@py:
if gold >= 5:
    inventory.append(iron_dagger)
    gold -= 5
    purchase_success = True
else:
    purchase_success = False
@endpy

@if purchase_success:
"Sold!" The vendor hands you the dagger.

Gold remaining: **{gold}**

+ [View inventory] -> Inventory.Display
+ [Continue shopping] -> Market.Vendor_Desk
@else:
"Not enough gold, friend."

+ [Back] -> Market.Vendor_Desk
@endif

:: Market.Buy_Key
@py:
if gold >= 3:
    inventory.append(brass_key)
    gold -= 3
    purchase_success = True
else:
    purchase_success = False
@endpy

@if purchase_success:
The brass key is yours.

+ [View inventory] -> Inventory.Display
+ [Continue shopping] -> Market.Vendor_Desk
@else:
"Not enough coin."

+ [Back] -> Market.Vendor_Desk
@endif

:: Market.Food_Stalls
The aroma of roasting meat and fresh bread fills the air.

+ [Buy bread (1 gold)] -> Market.Buy_Bread
+ [Back to market] -> Market.Entrance

:: Market.Buy_Bread
@py:
bread = Item("Fresh Bread", "Restores 10 HP", weight=0.3)
if gold >= 1:
    inventory.append(bread)
    gold -= 1
    purchase_success = True
else:
    purchase_success = False
@endpy

@if purchase_success:
You buy warm, fresh bread.

+ [Back to market] -> Market.Entrance
@else:
You can't afford it.

+ [Back] -> Market.Food_Stalls
@endif
```

**`shared/inventory.bard`:**

```bard
:: Inventory.Display
@py:
# Prepare inventory for rendering
inventory_data = []
total_weight = 0

for item in inventory:
    inventory_data.append({
        'name': item.name,
        'description': item.description,
        'weight': item.weight
    })
    total_weight += item.weight
@endpy

@render render_inventory(inventory_data, total_weight, gold)

You check your inventory.

@if len(inventory) > 0:
You're carrying {len(inventory)} item<>
@if len(inventory) != 1:
s<>
@endif
, weighing {total_weight:.1f} lbs.

@else:
Your inventory is empty.
@endif

+ [Back] -> Market.Vendor_Desk
```

**What's happening here?**

- Each location has its own file
- Passage names use namespaces: `Market.Vendor_Desk`, `Tavern.MainFloor`
- `@include` pulls everything together
- Shared functionality (like inventory) lives in `shared/`

---

## 2. Namespaced Passages

Notice how we name passages: `Market.Vendor_Desk`, not just `Vendor_Desk`. This creates clear organization:

```bard
# Good: Clear hierarchy
:: Market.Vendor_Desk
:: Market.Food_Stalls
:: Tavern.MainFloor
:: Tavern.Upstairs
:: Inn.Lobby
:: Inn.Room_3

# Bad: Confusing names
:: Vendor_Desk           // Which vendor?
:: Food                  // Where?
:: Floor1                // Of what building?
```

### Benefits of Namespaces

1. **Clarity** - You instantly know where a passage belongs
2. **No collisions** - `Market.Exit` and `Tavern.Exit` are different passages
3. **Organization** - Related passages group together
4. **Navigation** - Easier to find passages in large projects

---

## 3. Visualizing Your Story with `bardic graph`

As your story grows, it becomes hard to track all the connections. Bardic includes a built-in graph visualizer.

### Generate a Story Graph

```bash
bardic graph main.bard --output story_graph.html
```

This creates an interactive HTML visualization showing:

- All passages as nodes
- Choices as edges (arrows)
- Namespaces as colors
- Dead ends (passages with no choices) highlighted
- Unreachable passages (never linked to) highlighted

### Open and Explore

```bash
open story_graph.html
```

**What you'll see:**

- Visual representation of your story structure
- Click nodes to see passage details
- Identify dead ends (passages that need more choices)
- Find orphaned passages (passages never reached)
- Trace player paths through your story

### Example Graph Output

```sh
                Start
                  │
                  v
              Greeting
           ╱      │      ╲
          v       v       v
    Market.─   Tavern.─  Inn.─
    Entrance   MainFloor Lobby
       │          │
       v          v
   Market.     Tavern.
   Vendor_Desk Barkeep
```

---

## 4. Debugging Common Issues

### Problem: "Passage not found"

**Error:**

```sh
RuntimeError: Target passage 'Markeet.Entrance' not found
```

**Solution:**

- Check spelling in your `->` targets
- Ensure all passages are defined or included
- Use the graph to verify connections

**Pro tip:** Use your editor's "Find All" to search for passage names.

---

### Problem: Variable not defined

**Error:**

```sh
NameError: name 'gold' is not defined
```

**Solution:**

- Initialize variables before using them
- Use `@py:` blocks to set up state at the start

```bard
:: Start
@py:
# Always initialize your game state
gold = 10
inventory = []
health = 100
@endpy
```

---

### Problem: Infinite loops with `@for:`

**Symptom:** Story hangs or crashes

**Bad code:**

```bard
@for item in inventory:
~ inventory.append(new_item)  // Don't modify the list you're iterating!
@endfor
```

**Good code:**

```bard
@py:
# Build a new list if you need to modify during iteration
new_inventory = []
for item in inventory:
    new_inventory.append(item)
    if item.name == "Key":
        new_inventory.append(related_item)
inventory = new_inventory
@endpy
```

---

### Problem: Choices not appearing

**Symptom:** Player is stuck with no options

**Debug checklist:**

1. ✅ Are the choices inside the right passage?
2. ✅ Are conditional choices (`+ {condition}`) checking the right variables?
3. ✅ Are one-time choices (`*`) already used?
4. ✅ Does the passage end with choices or a `->` jump?

**Test your conditions:**

```bard
:: Debug_Passage
// Temporarily show your state for debugging
Gold: {gold}
Inventory: {len(inventory)} items
Has key: {brass_key in inventory if 'brass_key' in globals() else False}

+ [Test choice] -> NextPassage
```

---

### Problem: Render directive not working

**Symptom:** `@render` doesn't display anything

**Checklist:**

1. ✅ Is the function name spelled correctly? (`render_inventory` not `render_Inventory`)
2. ✅ Does your UI code have a handler for this directive?
3. ✅ Are you passing the right arguments?
4. ✅ Check the browser console for JavaScript errors

**Debug in your UI:**

```python
def handle_render_directive(self, directive):
    print(f"Received directive: {directive}")  # Debug print
    component_name = directive['component']
    # ... rest of code
```

---

## 5. Performance Tips for Large Stories

### Keep Python Blocks Small

**Slow:**

```bard
@py:
// 100 lines of complex calculations
// Every time this passage loads
@endpy
```

**Fast:**

```bard
@py:
# Call a function from your Python code
result = calculate_complex_stuff(game_state)
@endpy
```

Move heavy logic to Python files, not `.bard` files.

---

### Use One-Time Choices Wisely

One-time choices (`*`) are tracked per session. In a large story with hundreds of one-time choices, this state can grow.

**Best practice:**

- Use `*` for genuine one-time events (picking up an item)
- Use `+` with conditions for repeatable but gated choices
- Reset one-time choice state when starting new story sections

---

### Cache Expensive Calculations

**Bad:**

```bard
@if calculate_complex_score() > 50:  // Called every passage
...
@endif
```

**Good:**

```bard
@py:
# Calculate once, store result
if 'cached_score' not in globals():
    cached_score = calculate_complex_score()
@endpy

@if cached_score > 50:
...
@endif
```

---

## 6. Writing Maintainable Stories

### Use Comments Liberally

```bard
:: Market.Vendor_Desk
# This passage is the hub for weapon purchases
# Variables used: gold, inventory, brass_key, iron_dagger
# Connects to: Market.Buy_Dagger, Market.Buy_Key, Inventory.Display

The vendor waves you over.

+ [Ask about weapons] -> Market.Ask_Dagger
```

---

### Create Helper Passages

**Instead of this:**

```bard
:: Every_Single_Passage
// Same inventory display code copy-pasted 20 times
You have {len(inventory)} items.
...
```

**Do this:**

```bard
:: Shared.Show_Inventory
You have {len(inventory)} items.
-> Return_Target  // Jump back to where you came from

:: Some_Passage
...
-> Shared.Show_Inventory(return_target='Some_Passage')
```

---

### Test Early, Test Often

Don't write 50 passages before playing through your story!

**Development workflow:**

1. Write 3-5 passages
2. Test with `bardic play main.bard`
3. Fix issues
4. Repeat

**Testing checklist:**

- [ ] Can I reach every passage?
- [ ] Do all choices work?
- [ ] Are variables initializing correctly?
- [ ] Does the inventory work as expected?
- [ ] Are there any dead ends?

---

## 7. Publishing Your Story

### Create a Standalone Web App

Once your game is complete, you can deploy it as a web app:

1. **Package your story:**

```bash
bardic compile main.bard --output story.json
```

2. **Deploy with NiceGUI:**

```python
# production.py
from nicegui import ui
from web_ui import GameUI

game = GameUI('story.json')
game.start()
ui.run(host='0.0.0.0', port=8080, show=False)
```

3. **Deploy to cloud:**
   - Heroku
   - Railway.app
   - Google Cloud Run
   - Your own VPS

---

## 8. Going Further

You now have all the tools to build professional-quality interactive fiction in Bardic! Here are some advanced topics to explore:

### Procedural Generation

```bard
@py:
# Generate random events
import random
event = random.choice(['bandits', 'merchant', 'storm'])
@endpy

@if event == 'bandits':
-> Combat.Bandits
@elif event == 'merchant':
-> Encounter.Traveling_Merchant
@else:
-> Weather.Storm
@endif
```

### Save/Load System

Implement save states in your Python backend:

```python
def save_game(engine):
    return {
        'state': engine.state,
        'current_passage': engine.current_passage,
        'one_time_choices': engine.one_time_choices_used
    }

def load_game(engine, save_data):
    engine.state = save_data['state']
    engine.current_passage = save_data['current_passage']
    # ... restore state
```

### Analytics & Telemetry

Track player choices to improve your story:

```python
def log_choice(passage, choice_text):
    # Send to analytics service
    analytics.track('choice_made', {
        'passage': passage,
        'choice': choice_text
    })
```

---

## 🎉 Conclusion

Congratulations! You've completed the Bardic Guided Tour!

**You learned how to:**

- Create branching narratives with passages and choices
- Manage state with variables and conditionals
- Use Python objects for complex game logic
- Build custom web UIs with NiceGUI
- Organize large projects with `@include` and namespaces
- Debug and visualize your story structure
- Write maintainable, scalable interactive fiction

**You're now ready to:**

- Build complete interactive fiction games
- Integrate with Python backends and APIs
- Create custom UI components
- Manage complex narrative state
- Deploy your stories to the web

---

## Next Steps

**Advanced Topics:**

- State management patterns
- Complex branching narratives
- Integration with databases
- Procedural content generation

**Build Something Amazing:**

The best way to master Bardic is to build something you're excited about. Start with a small project—maybe a character conversation system, a simple puzzle game, or a short story.

Then expand from there. Good luck, and happy writing! 🎭

[← Back to Part 4](04_custom_ui.md) | [Back to Tutorial Index](README.md)
