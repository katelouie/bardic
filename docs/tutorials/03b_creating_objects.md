# Part 3B: Creating Your Own Objects (The "Aha!" Moment)

Welcome to the most powerful part of Bardic! In Part 3A, you learned that objects like lists and strings have **superpowers**—they bundle data and behavior together.

Now here's the exciting part: **you can create your own objects** with custom superpowers tailored to your game.

**By the end of this tutorial, you will know how to:**

- Create a simple Python **class** (a blueprint for objects)
- **Import** your class into your Bardic story
- Create **instances** (individual objects) from your class
- Call **methods** on your custom objects
- Store custom objects in lists and dictionaries

---

## 1. What's a Class? (The Blueprint)

Think of a **class** as a blueprint. If you wanted to make many similar items in your game, you'd want a blueprint that says:

> "Every Item has a name, a description, and a weight.
> Every Item knows how to describe itself nicely."

Then you can use that blueprint to create:

- A brass key (name="Brass Key", weight=0.2)
- An iron dagger (name="Iron Dagger", weight=2.5)
- A health potion (name="Health Potion", weight=0.5)

Each is a separate **instance** (an individual object), but they all follow the same **blueprint** (the class).

**Let's build that blueprint.**

---

## 2. Your First Class (The Simplest Possible Version)

We're going to start VERY simple. Create a new file called **`item.py`** in your project folder (next to your `.bard` files):

```python
# item.py

class Item:
    """A simple game item."""

    def __init__(self, name):
        self.name = name
```

**That's it.** This is a complete, working class. Let's break it down:

- `class Item:` - This says "I'm creating a blueprint called Item"
- `def __init__(self, name):` - This is the **initialization method**. It runs when you create a new Item. Think of it as "setup instructions."
- `self.name = name` - This stores the name you provide

**Translation to English:**
> "When someone creates an Item and gives it a name, store that name."

Save this file. We're done with Python for now!

---

## 3. Using Your Class in a Story

Now create a new story file called **`my_first_object.bard`**:

```bard
from item import Item

:: Start
~ key = Item("Brass Key")

You found an item: {key.name}

+ [Continue] -> End

:: End
That was easy!
```

**What's happening here?**

1. `from item import Item` - Bring in the Item blueprint
2. `~ key = Item("Brass Key")` - Create a new Item and name it "Brass Key"
3. `{key.name}` - Display the name we stored

**Compile and run:**

```bash
bardic compile my_first_object.bard
bardic play my_first_object.json
```

Or with Pixi:

```bash
pixi run bardic compile my_first_object.bard
pixi run bardic play my_first_object.json
```

**🎉 Congratulations! You just created and used your first custom object!**

---

## 4. Adding More Data to the Blueprint

That was almost too simple. Let's make our Item more useful by adding description and weight:

**Update `item.py`:**

```python
# item.py

class Item:
    """A game item with a name, description, and weight."""

    def __init__(self, name, description, weight):
        self.name = name
        self.description = description
        self.weight = weight
```

**What changed?**

- Now `__init__` takes THREE pieces of information: name, description, and weight
- We store all three: `self.name`, `self.description`, `self.weight`

**Update your story:**

```bard
from item import Item

:: Start
~ key = Item("Brass Key", "Opens the library", 0.2)
~ dagger = Item("Iron Dagger", "A basic weapon", 2.5)
~ potion = Item("Health Potion", "Restores 50 HP", 0.5)

You have three items:

1. **{key.name}** - {key.description} ({key.weight} lbs)
2. **{dagger.name}** - {dagger.description} ({dagger.weight} lbs)
3. **{potion.name}** - {potion.description} ({potion.weight} lbs)

+ [Continue] -> End

:: End
See how easy that was?
```

**Run it!** You now have three distinct Item objects, each with their own data.

---

## 5. Making Objects "Smart" (Adding Methods)

Right now, our Items just store data. Let's give them a **superpower**—the ability to describe themselves nicely.

**Update `item.py` again:**

```python
# item.py

class Item:
    """A game item with a name, description, and weight."""

    def __init__(self, name, description, weight):
        self.name = name
        self.description = description
        self.weight = weight

    def get_description(self):
        """Return a nicely formatted description."""
        return f"{self.name} - {self.description} ({self.weight} lbs)"
```

**What's new?**

- `def get_description(self):` - This is a **method** (a function that belongs to the Item)
- It uses the data we stored (`self.name`, etc.) to create a nice string
- Notice the `self` parameter? That's how the method knows which Item it's talking about

**Update your story to use the method:**

```bard
from item import Item

:: Start
~ key = Item("Brass Key", "Opens the library", 0.2)
~ dagger = Item("Iron Dagger", "A basic weapon", 2.5)

You have two items:

1. {key.get_description()}
2. {dagger.get_description()}

Much cleaner!

+ [Try something more complex] -> Vendor
```

See what we did? Instead of manually formatting `{key.name} - {key.description}` every time, we just call `{key.get_description()}` and the Item knows how to describe itself!

---

## 6. Optional Parameters (Making It Easier)

Sometimes you want to create an Item but you don't know all the details yet. Let's make some parameters **optional**:

**Update `item.py`:**

```python
# item.py

class Item:
    """A game item with a name, description, and weight."""

    def __init__(self, name, description="", weight=1.0):
        self.name = name
        self.description = description
        self.weight = weight

    def get_description(self):
        """Return a nicely formatted description."""
        if self.description:
            return f"{self.name} - {self.description} ({self.weight} lbs)"
        else:
            return f"{self.name} ({self.weight} lbs)"
```

**What changed?**

- `description=""` and `weight=1.0` are **default values**
- If you don't provide them, these defaults are used
- The `get_description()` method checks if there's a description before using it

**Now you can create Items in different ways:**

```bard
from item import Item

:: Start
~ key = Item("Brass Key", "Opens the library", 0.2)
~ rock = Item("Rock")  # Uses defaults!
~ stick = Item("Stick", weight=0.8)  # Only provide weight

Your items:
1. {key.get_description()}
2. {rock.get_description()}
3. {stick.get_description()}

+ [Continue] -> End

:: End
Default values make life easier!
```

---

## 7. Using Objects in Your Inventory

Here's where it gets really powerful. Let's store our custom Items in a list (your inventory):

```bard
from item import Item

:: Start
~ inventory = []
~ gold = 10

You're at the market. You have {gold} gold.

+ [Visit the vendor] -> Vendor

:: Vendor
~ brass_key = Item("Brass Key", "Opens the library", 0.2)
~ iron_dagger = Item("Iron Dagger", "A basic weapon", 2.5)

The vendor shows you:
1. {brass_key.get_description()} - 3 gold
2. {iron_dagger.get_description()} - 5 gold

+ [Buy the key (3 gold)] -> Buy_Key
+ [Buy the dagger (5 gold)] -> Buy_Dagger
+ [Check inventory] -> Inventory

:: Buy_Key
~ brass_key = Item("Brass Key", "Opens the library", 0.2)

@py:
if gold >= 3:
    inventory.append(brass_key)
    gold -= 3
    success = True
else:
    success = False
@endpy

@if success:
You bought the brass key!

+ [Continue shopping] -> Vendor
+ [Check inventory] -> Inventory
@else:
Not enough gold!

+ [Back] -> Vendor
@endif

:: Buy_Dagger
~ iron_dagger = Item("Iron Dagger", "A basic weapon", 2.5)

@py:
if gold >= 5:
    inventory.append(iron_dagger)
    gold -= 5
    success = True
else:
    success = False
@endpy

@if success:
You bought the dagger!

+ [Continue shopping] -> Vendor
+ [Check inventory] -> Inventory
@else:
Not enough gold!

+ [Back] -> Vendor
@endif

:: Inventory
**Your Inventory:**

@if len(inventory) > 0:
    @for item in inventory:
    - {item.get_description()}
    @endfor

    Total weight: {sum(item.weight for item in inventory):.1f} lbs
@else:
    Empty
@endif

Gold: {gold}

+ [Back to vendor] -> Vendor
```

**What's happening here?**

1. We create Item objects for the key and dagger
2. When purchased, we add them to the `inventory` list
3. In the Inventory passage, we loop through and display each item
4. We can calculate total weight by accessing each `item.weight`

**This is the power of custom objects!** Your inventory isn't just a list of strings—it's a list of smart Item objects that know how to describe themselves and track their own data.

---

## 8. Going Further: Adding More Methods

Let's add one more method to show how flexible this is:

**Update `item.py`:**

```python
# item.py

class Item:
    """A game item with a name, description, and weight."""

    def __init__(self, name, description="", weight=1.0):
        self.name = name
        self.description = description
        self.weight = weight

    def get_description(self):
        """Return a nicely formatted description."""
        if self.description:
            return f"{self.name} - {self.description} ({self.weight} lbs)"
        else:
            return f"{self.name} ({self.weight} lbs)"

    def is_heavy(self):
        """Check if this item is heavy (over 2 lbs)."""
        return self.weight > 2.0
```

**Now use it in your story:**

```bard
:: Inventory
**Your Inventory:**

@if len(inventory) > 0:
    @for item in inventory:
        @if item.is_heavy():
            - {item.name} âš  (Heavy!)
        @else:
            - {item.name}
        @endif
    @endfor
@else:
    Empty
@endif

+ [Back to vendor] -> Vendor
```

The Item objects now **know** if they're heavy! You didn't have to write `if item.weight > 2.0` in your story—the Item object handles that logic.

---

## 9. The Pattern You Just Learned

Here's what you did:

1. **Created a blueprint (class)** in a `.py` file
2. **Imported it** into your story: `from item import Item`
3. **Created instances**: `~ key = Item("Brass Key", ...)`
4. **Called methods**: `{key.get_description()}`
5. **Stored objects in lists**: `inventory.append(key)`
6. **Looped through objects**: `@for item in inventory:`

This same pattern works for ANY custom object you want to create:

- A `Character` class for tracking stats and combat
- A `Quest` class for tracking objectives
- A `Card` class for a tarot reading game
- A `Room` class for dungeon exploration

---

## 10. Your Complete Example

Here's the full working example:

**`item.py`:**

```python
class Item:
    """A game item with a name, description, and weight."""

    def __init__(self, name, description="", weight=1.0):
        self.name = name
        self.description = description
        self.weight = weight

    def get_description(self):
        """Return a nicely formatted description."""
        if self.description:
            return f"{self.name} - {self.description} ({self.weight} lbs)"
        return f"{self.name} ({self.weight} lbs)"

    def is_heavy(self):
        """Check if this item is heavy."""
        return self.weight > 2.0
```

**`shopping_game.bard`:**

```bard
from item import Item

:: Start
~ inventory = []
~ gold = 10

You're at the market with {gold} gold.

+ [Visit vendor] -> Vendor

:: Vendor
~ key = Item("Brass Key", "Opens the library", 0.2)
~ dagger = Item("Iron Dagger", "A basic weapon", 2.5)
~ potion = Item("Health Potion", "Restores 50 HP", 0.5)

**For Sale:**
1. {key.get_description()} - 3 gold
2. {dagger.get_description()} - 5 gold
3. {potion.get_description()} - 2 gold

+ [Buy key] -> Buy_Key
+ [Buy dagger] -> Buy_Dagger
+ [Buy potion] -> Buy_Potion
+ [Check inventory] -> Inventory

:: Buy_Key
~ key = Item("Brass Key", "Opens the library", 0.2)

@py:
if gold >= 3:
    inventory.append(key)
    gold -= 3
    success = True
else:
    success = False
@endpy

@if success:
Bought!
+ [Shop more] -> Vendor
@else:
Too expensive!
+ [Back] -> Vendor
@endif

:: Buy_Dagger
~ dagger = Item("Iron Dagger", "A basic weapon", 2.5)

@py:
if gold >= 5:
    inventory.append(dagger)
    gold -= 5
    success = True
else:
    success = False
@endpy

@if success:
Bought!
+ [Shop more] -> Vendor
@else:
Too expensive!
+ [Back] -> Vendor
@endif

:: Buy_Potion
~ potion = Item("Health Potion", "Restores 50 HP", 0.5)

@py:
if gold >= 2:
    inventory.append(potion)
    gold -= 2
    success = True
else:
    success = False
@endpy

@if success:
Bought!
+ [Shop more] -> Vendor
@else:
Too expensive!
+ [Back] -> Vendor
@endif

:: Inventory
**Your Inventory:**

@if len(inventory) > 0:
    @for item in inventory:
        @if item.is_heavy():
            - {item.name} âš  (Heavy!)
        @else:
            - {item.name}
        @endif
    @endfor

    Total weight: {sum(item.weight for item in inventory):.1f} lbs
@else:
    Empty
@endif

Gold: {gold}

+ [Back] -> Vendor
```

**Run it:**

```bash
bardic compile shopping_game.bard
bardic play shopping_game.json
```

Or with Pixi:

```bash
pixi run bardic compile shopping_game.bard
pixi run bardic play shopping_game.json
```

---

## 🎉 Congratulations

You've just learned the most powerful feature of Bardic: **creating and using custom objects**.

**What you learned:**

- Classes are **blueprints** for creating objects
- `__init__` is the **setup method** that runs when creating an object
- Methods like `get_description()` give objects **superpowers**
- You **import** classes into your story like any Python module
- Objects can be stored in **lists and dictionaries**
- You can **loop through** and manipulate custom objects

**This is what makes Bardic different.** Other interactive fiction tools stop at simple variables. Bardic gives you the full power of Python to model your game world exactly how you want.

---

## Next Steps

Now that you understand custom objects, you can:

1. **Create a Character class** for tracking player/NPC stats
2. **Create a Quest class** for tracking objectives
3. **Create a Location class** for building a game world
4. **Combine objects** (Characters can have Item inventories!)

**Want to build a custom UI?** Continue to Part 4 to learn about NiceGUI and the `@render` directive.

**Want to organize large projects?** Skip to Part 5 to learn about `@include` and project structure.

---

## Compare Where You Started vs Where You Are Now

**Part 1:** You made passages and choices
**Part 2:** You added variables and conditionals
**Part 2.5:** You used lists and dictionaries
**Part 3A:** You learned objects have superpowers
**Part 3B:** **You created your own object blueprints!**

You've gone from complete beginner to someone who can write object-oriented Python for game logic. That's incredible!

[← Back to Part 3A](03a_objects_superpowers.md) | [Continue to Part 3C →](03_5_reusable_passages_stdlib.md)
