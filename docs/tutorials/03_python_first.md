# Part 3: The Python-First Promise (The "Aha!" Moment)

Welcome to the most powerful part of Bardic. In the last section, you built an item system using simple text and a variable: `~ has_key = True`.

But what if you had 50 keys, each with a name, weight, and description? Managing that with a bunch of `True`/`False` variables would be a nightmare!

Bardic solves this by letting you define and use **real Python objects** in your story. This is the "Aha!" moment where you stop being just a writer and start building a true narrative engine.

**By the end of this tutorial, you will know how to:**

- Create a custom Python class (like `Item` or `Client`)
- Use the standard Python `import` statement in your story file
- Create objects from that class, like `~ brass_key = Item("Brass Key")`
- Call an object's methods (functions) inside your game logic

---

## 1. Create a Custom Python Class

First, we need the "real" Python code that powers our items.

Create a new file in your project directory called **`item.py`** and enter the following content:

```python
class Item:
    """A game item with a name, description, and weight."""

    def __init__(self, name, description="", weight=1.0):
        self.name = name
        self.description = description
        self.weight = weight

    def get_description(self):
        """Returns a formatted description of this item."""
        if self.description:
            return f"{self.name} - {self.description}"
        return self.name

    def __repr__(self):
        return f"Item('{self.name}')"
```

**What's happening here?**

- `__init__` is called when you create a new item: `Item("Brass Key")`
- `get_description()` is a method you can call to get a nice formatted string
- Each item tracks its `name`, `description`, and `weight`

Save and close that file. We won't touch it again, but this single file gives your story incredible power.

---

## 2. Import the Class into Your Story

Now, open a new Bardic file, let's call it **`story_with_objects.bard`**.

To use the `Item` class we just created, we use a **standard Python import statement** at the very top of the file:

```bard
from item import Item

:: Start
@start
You stand in the Merchant's Quarter. A vendor waves you over.

+ [Approach the vendor] -> Vendor_Desk
```

That's it! Just like Python. The `Item` class is now available everywhere in your story.

---

## 3. Create, Use, and Manipulate Objects

In the `Vendor_Desk` passage, we're going to create three distinct objects from our `Item` class and then use their methods.

### 3.1. Creating Objects

We use the standard variable assignment (`~`) syntax to create our objects, just like in Python:

```bard
:: Vendor_Desk
~ brass_key = Item("Brass Key", "Opens the town library", weight=0.2)
~ iron_dagger = Item("Iron Dagger", "A basic weapon for self-defense", weight=2.5)
~ health_potion = Item("Health Potion", "Restores 50 HP", weight=0.5)

The vendor lays out three items on the wooden counter:
- A **{brass_key.name}** ({brass_key.weight} lbs)
- An **{iron_dagger.name}** ({iron_dagger.weight} lbs)
- A **{health_potion.name}** ({health_potion.weight} lbs)

+ [Ask about the dagger] -> Ask_Dagger
+ [Buy the brass key] -> Buy_Key
+ [Leave] -> Start
```

Notice how we can access properties directly: `{brass_key.name}` and `{brass_key.weight}`. These are just Python objects!

---

### 3.2. Displaying Object Properties

Now let's add a passage where we call the custom `get_description()` method:

```bard
:: Ask_Dagger
The vendor picks up the dagger.

"This? {iron_dagger.get_description()}. Standard issue, but reliable."

She sets it back down on the counter.

+ [Ask about its history] -> Dagger_History
+ [Buy the dagger (5 gold)] -> Buy_Dagger
+ [Back to other items] -> Vendor_Desk
```

Notice how we call the custom Python method `get_description()`? Bardic runs that code in the background and inserts the returned string into the story.

---

### 3.3. Adding the Item to the Inventory

Now let's add the core game logic: **buying the dagger and adding it to our list**.

We'll use a Python block (`@py:`) because it lets us run multiple lines of Python logic in a clean way:

```bard
:: Buy_Dagger
@py:
# Initialize inventory if it doesn't exist yet
if 'inventory' not in globals():
    inventory = []

# Check if player has enough gold
if 'gold' not in globals():
    gold = 10  # Starting gold

if gold >= 5:
    # Add the dagger to inventory
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
```

**What's happening here?**

- We create an `inventory` list (if it doesn't exist yet)
- We check if the player has enough gold
- If yes, we add the actual `iron_dagger` object to the inventory
- We set a flag `purchase_success` to control the branching narrative

---

### 3.4. Looping Through the Inventory

Let's create an **Inventory** passage to prove our complex objects are stored correctly. We use the `@for` loop syntax:

```bard
:: Inventory
You check your inventory.

@if len(inventory) > 0:
**Your items:**

@for item in inventory:
- **{item.name}** - {item.description} (Weight: {item.weight} lbs)
@endfor

Total weight: {sum(item.weight for item in inventory):.1f} lbs

@else:
Your inventory is empty.
@endif

+ [Back to vendor] -> Vendor_Desk
+ [Leave the market] -> Start
```

**What's happening here?**

- `@for item in inventory:` loops through each object
- We access each item's properties: `item.name`, `item.description`, `item.weight`
- We use a Python expression to calculate total weight: `sum(item.weight for item in inventory)`
- The `.1f` formatter displays the weight with 1 decimal place

---

## Your Complete Story File

Here is the entire content of **`story_with_objects.bard`**:

```bard
from item import Item

:: Start
You stand in the Merchant's Quarter. A vendor waves you over.

+ [Approach the vendor] -> Vendor_Desk

:: Vendor_Desk
~ brass_key = Item("Brass Key", "Opens the town library", weight=0.2)
~ iron_dagger = Item("Iron Dagger", "A basic weapon for self-defense", weight=2.5)
~ health_potion = Item("Health Potion", "Restores 50 HP", weight=0.5)

The vendor lays out three items on the wooden counter:
- A **{brass_key.name}** ({brass_key.weight} lbs)
- An **{iron_dagger.name}** ({iron_dagger.weight} lbs)
- A **{health_potion.name}** ({health_potion.weight} lbs)

+ [Ask about the dagger] -> Ask_Dagger
+ [Buy the brass key] -> Buy_Key
+ [Leave] -> Start

:: Ask_Dagger
The vendor picks up the dagger.

"This? {iron_dagger.get_description()}. Standard issue, but reliable."

She sets it back down on the counter.

+ [Ask about its history] -> Dagger_History
+ [Buy the dagger (5 gold)] -> Buy_Dagger
+ [Back to other items] -> Vendor_Desk

:: Dagger_History
"Found it in a bandit camp up north. Probably stolen from some poor traveler."

She shrugs. "But it's yours if you want it."

+ [Buy the dagger (5 gold)] -> Buy_Dagger
+ [Back to other items] -> Vendor_Desk

:: Buy_Dagger
@py:
# Initialize inventory if it doesn't exist yet
if 'inventory' not in globals():
    inventory = []

# Check if player has enough gold
if 'gold' not in globals():
    gold = 10  # Starting gold

if gold >= 5:
    # Add the dagger to inventory
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
You check your inventory.

@if len(inventory) > 0:
**Your items:**

@for item in inventory:
- **{item.name}** - {item.description} (Weight: {item.weight} lbs)
@endfor

Total weight: {sum(item.weight for item in inventory):.1f} lbs

@else:
Your inventory is empty.
@endif

+ [Back to vendor] -> Vendor_Desk
+ [Leave the market] -> Start
```

---

## Run Your Story

Now test it! Run from your terminal:

```bash
bardic play story_with_objects.bard
```

Try buying items and checking your inventory. Notice how the **objects persist** across passages, and you can call their methods and access their properties naturally.

---

## 🎉 Conclusion

You have successfully connected the narrative logic of Bardic to the **full programming power of Python**! You learned how to:

✅ Define custom Python classes
✅ Import them into your Bardic story
✅ Create and manipulate objects
✅ Call methods on those objects
✅ Store complex objects in lists
✅ Loop through object collections

This is what makes Bardic different from other interactive fiction tools. You're not limited to simple variables—you have the entire Python ecosystem at your fingertips.

**Next up:** In Part 4, we'll stop using the terminal and learn how to build a **custom web-based user interface** for your game using NiceGUI and the `@render` directive.

[← Back to Part 2](02_state_memory.md) | [Continue to Part 4 →](04_custom_ui.md)
