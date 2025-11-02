# Part 2.5: Complex State (Lists & Dictionaries)

In Part 2, you gave your story a *memory* with simple variables, like `~ has_key = True`. This is great for simple flags, but what happens when things get more complex?

What if you want to hold *more than one* key? Or track a character's *stats*?

In this tutorial, we'll unlock the next level of Bardic's power by using Python's built-in **lists** and **dictionaries**—all without leaving your `.bard` file.

**By the end, you will know how to:**

- Use a **List** to create a multi-item inventory (`[]`).
- Add and check for items in your list (`.append()`, `in`).
- Loop through your list with `@for:` to display its contents.
- Use a **Dictionary** to create a character sheet (`{}`).
- Access and modify data in your dictionary (`hero["health"]`).

---

## 1. Lists: Your "Shopping Bag"

A **List** is a variable that can hold *multiple* items. Think of it as a shopping bag you can put things into.

Let's re-build our "locked door" puzzle, but this time, we'll use a `list` for our inventory.

```bard
:: Start
# This creates an empty "shopping bag" called inventory
~ inventory = []
~ gold = 10

You are in a dusty room. A hallway leads north.

+ [Go into the hallway] -> Hallway

:: Hallway
A long hallway stretches before you.
To your left, you see a dark corner.
At the end of the hall is a large, locked door.

+ [Look in the dark corner] -> Dark_Corner
+ [Try the locked door] -> Locked_Door
+ [Go back to the start] -> Start
```

## 2. Adding to a List (`.append()`)

Now, let's add the key to our inventory list. We do this by calling the list's built-in `.append()` function.

```bard
:: Dark_Corner
You look in the dark corner and see something
shiny on the floor. It's a small brass key.

# This one-time choice will disappear
* [Pick up the key] -> Get_Key

+ [Leave it for now] -> Hallway

:: Get_Key
# We add the *string* "Brass Key" to our inventory list
~ inventory.append("Brass Key")

You pick up the key and put it in your pocket.

+ [Go back to the hallway] -> Hallway
```

## 3. Checking a List (`in`)

How does the door react? Instead of checking if `has_key == True`, we now check `if "Brass Key" in inventory`. This is much more powerful, as our inventory could hold 100 items!

```bard
:: Locked_Door
You walk up to the heavy door.

# This checks if the string "Brass Key" is *inside* our list
@if "Brass Key" in inventory:
    You find the brass key in your pocket and slide
    it into the lock. *Click*. The door swings open.

    + [Go through the door] -> Victory
@else:
    You try the handle, but it's locked solid.
    You need a key to open it.

    + [Go back to the hallway] -> Hallway
@endif

:: Victory
You've escaped! Congratulations.
```

## 4. Displaying a List (`@for:`)

This is great, but how does the player see what's in their inventory? We can use a **for loop** to show every item in our list, one by one.

Let's add a new choice to the `Hallway` and create an `Inventory` passage.

```bard
:: Hallway
A long hallway stretches before you.
...
+ [Look in the dark corner] -> Dark_Corner
+ [Try the locked door] -> Locked_Door
+ [Check your inventory] -> Inventory  # NEW
+ [Go back to the start] -> Start

:: Inventory
You check your pockets.
You have {gold} gold.

@if len(inventory) > 0:
    You are carrying:
    @for item in inventory:
        - {item}
@else:
    Your pockets are empty.
@endif

+ [Go back to the hallway] -> Hallway
```

**What's happening here?**

- `@if len(inventory) > 0:`: A quick Python check. `len()` gets the "length" (number of items) in our list.
- `@for item in inventory:`: This is the loop. It says, "For every `item` inside the `inventory` list, do the following..."
- `{item}`: This line is run for every single item. `item` is a temporary variable that holds the current item ("Brass Key", etc.).

## 5. Dictionaries: Your "Filing Cabinet"

Lists are great for collections, but what about a character sheet? For that, we use a **Dictionary** (or `dict`). A `dict` is a "filing cabinet" that stores information in pairs (a `key` and a `value`).

Let's create a `hero` variable in our `Start` passage.

```bard
:: Start
~ inventory = []
~ gold = 10

# This is a dictionary!
~ hero = {
    "name": "Aria",
    "health": 100,
    "max_health": 100,
    "strength": 12
}

You are in a dusty room. A hallway leads north.
+ [Go into the hallway] -> Hallway
```

## 6. Accessing & Modifying Dictionary Data

Now we can access this data just like pulling a file from our cabinet, using `[]` brackets with the name of the key.

Let's add a `Stats` page and a `Trap` page to see this in action.

```bard
:: Hallway
A long hallway stretches before you.
...
+ [Try the locked door] -> Locked_Door
+ [Check your inventory] -> Inventory
+ [Check your stats] -> Stats         # NEW
+ [Go back to the start] -> Start
+ [Search the dusty sarcophagus] -> Trap # NEW

:: Stats
You take a moment to assess yourself.

Name: {hero["name"]}
Health: {hero["health"]} / {hero["max_health"]}
Strength: {hero["strength"]}

+ [Go back to the hallway] -> Hallway

:: Trap
You open the heavy sarcophagus... it's a trap!
A spray of poison gas hits you in the face.

# We modify the value *inside* the dictionary
~ hero["health"] -= 10

You feel dizzy and sick.
You lost 10 health!
Your health is now {hero["health"]}.

+ [Stumble back to the hallway] -> Hallway
```

**What's happening here?**

- `{hero["name"]}`: We use quotes *inside* the brackets to get the *value* associated with the "name" *key*.
- `~ hero["health"] -= 10`: This is the coolest part. We aren't just changing `health`; we're changing the "health" value *inside* the `hero` dictionary. This is a powerful way to keep all your stats cleanly organized in one variable.

## Conclusion

You're now using real data structures! You've learned how to:

- ✅ Use **Lists** (`[]`) to create powerful inventories.
- ✅ Add to lists with `.append()` and check them with `in`.
- ✅ **Loop** over lists with `@for:` to display their contents.
- ✅ Use **Dictionaries** (`{}`) to create a character sheet.
- ✅ Access `dict` data with `hero["health"]` and modify it.

This is extremely powerful. You can now build complex RPGs, stat-based adventures, and rich inventories, all from inside your `.bard` file.

But...

What if your hero dictionary could have its own functions? What if, instead of writing `~ hero["health"] -= 10` in your story, you could just write `~ hero.take_damage(10)`?

For that, we need to promote our "filing cabinet" (`dict`) into a "thinking machine" (`class`).

**[Continue to Part 3: The Python-First Promise (Classes!)](./03_python_first.md)**
