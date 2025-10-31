# Part 2: Adding State & Memory

In Part 1, we built a simple story where the player could move between passages. But the story had no *memory*. The "locked door" was always locked, and the world never changed.

In this tutorial, we'll fix that. We're going to give your story **state**, or a memory. We'll create a classic "locked door and key" puzzle.

By the end, you will know how to:

- Create **variables** to store information (like `~ has_key = False`).
- Use **one-time choices** that disappear after you click them (`*`).
- Use **conditionals** to make your story react to your variables (`@if...:`).
- **Display** your variable's value directly in your text (like `{gold}`).

-----

## 1. Set Up Your Story with a Variable

Let's start with a new `.bard` file. We'll create a `Start` passage and a `Hallway`.

This time, in our `Start` passage, we'll add something new: a **variable**. A variable is just a box to store a piece of memory.

We create one using the tilde `~` symbol.

```bard
:: Start
# This creates a "memory box" named 'has_key'
# and puts the value 'False' inside it.
~ has_key = False

You are in a dusty room. A hallway leads north.

+ [Go into the hallway] -> Hallway
```

We've just told our story: "At the start of the game, the player does *not* have the key."

-----

## 2. Create the "Key"

Now, let's create the passages for our hallway. We'll add a choice to a `Dark_Corner` and another to the `Locked_Door`.

```bard
:: Hallway
A long hallway stretches before you.
To your left, you see a dark corner.
At the end of the hall is a large, locked door.

+ [Look in the dark corner] -> Dark_Corner
+ [Try the locked door] -> Locked_Door
+ [Go back to the start] -> Start

:: Dark_Corner
You look in the dark corner and see something
shiny on the floor. It's a small brass key.

# This is a one-time choice.
* [Pick up the key] -> Get_Key

+ [Leave it for now] -> Hallway
```

### A New Kind of Choice (`*`)

Notice that `[Pick up the key]` uses a `*` (asterisk) instead of a `+` (plus).

- `+` is a **sticky choice**. It stays there forever.
- `*` is a **one-time choice**. Once the player clicks it, it will disappear and not be shown again. This is perfect for picking up items.

-----

## 3\. Change the Story's Memory

When the player picks up the key, we need to change our `has_key` variable from `False` to `True`. We do this in the `Get_Key` passage.

```bard
:: Get_Key
# We update our variable!
~ has_key = True

You pick up the key and put it in your pocket.

+ [Go back to the hallway] -> Hallway
```

That's it! The story's "memory" is now updated. The player `has_key`.

-----

## 4. Make the Door React (The Payoff!)

Now for the fun part. We need to make the `Locked_Door` passage *react* to whether the player has the key.

We do this with **conditionals**. We can tell Bardic to show different text `@if` a variable is true.

```bard
:: Locked_Door
You walk up to the heavy door.

@if has_key == True:
    You slide the brass key into the lock. It turns
    with a satisfying *click*. The door swings open.

    + [Go through the door] -> Victory
@else:
    You try the handle, but it's locked solid.
    You need a key to open it.

    + [Go back to the hallway] -> Hallway
@endif

:: Victory
You've escaped! Congratulations.
```

Let's break that down:

- `@if has_key == True:`: This checks our "memory box." It asks, "Is the `has_key` variable equal to `True`?".
- `@else:`: If the first check fails (if `has_key` is *not* `True`), the story will show this text instead.
- `@endif`: This closes the conditional block.

Now, if the player visits the `Locked_Door` *before* getting the key, they'll be turned away. If they go back *after* getting the key, the passage will magically change, and they can win!

-----

## 5. Displaying Variables in Text

There's one more thing. What if you want to show the player what's in their "memory"? You can display variables directly in your text using curly braces `{}`.

Let's add some gold to our `Start` passage and display it in the `Hallway`.

- First, add `~ gold = 10` to your `:: Start` passage.
- Then, add `You have {gold} gold.` to your `:: Hallway` passage.

Your file will now look like this.

### Your Complete Story File

```bard
:: Start
# This creates our "memory" for the story
~ has_key = False
~ gold = 10

You are in a dusty room. A hallway leads north.

+ [Go into the hallway] -> Hallway

:: Hallway
A long hallway stretches before you.
To your left, you see a dark corner.
At the end of the hall is a large, locked door.

You check your pockets. You have {gold} gold.

+ [Look in the dark corner] -> Dark_Corner
+ [Try the locked door] -> Locked_Door
+ [Go back to the start] -> Start

:: Dark_Corner
You look in the dark corner and see something
shiny on the floor. It's a small brass key.

# This one-time choice will disappear after being clicked
* [Pick up the key] -> Get_Key

+ [Leave it for now] -> Hallway

:: Get_Key
# We update our variable!
~ has_key = True

You pick up the key and put it in your pocket.
You find 5 gold coins next to it!
~ gold = gold + 5

+ [Go back to the hallway] -> Hallway

:: Locked_Door
You walk up to the heavy door.

# The story checks its memory to show the correct text
@if has_key == True:
    You slide the brass key into the lock. It turns
    with a satisfying *click*. The door swings open.

    + [Go through the door] -> Victory
@else:
    You try the handle, but it's locked solid.
    You need a key to open it.

    + [Go back to the hallway] -> Hallway
@endif

:: Victory
You've escaped! Congratulations.
```

-----

## You've Got the Key

You now have the core skills for interactive fiction! You learned how to:

1. **Create** variables with `~`.
2. **Modify** them with one-time choices (`*`).
3. **Check** them with `@if` blocks.
4. **Display** them with `{}`.

You can build surprisingly complex games with just these tools.

But what if you wanted *more than one* key? What if you wanted an inventory, a list of items, or a character with their own stats?

For that, we need to go one step further. It's time to unlock Bardic's most powerful feature.

**[Continue to Part 3: The Python-First Promise](./03_python_first.md)**
