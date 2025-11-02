# Part 3A: Objects Have Superpowers (The Gateway)

Welcome back! In Part 2.5, you learned about **lists** and **dictionaries**—Python's built-in data containers. You wrote code like this:

```bard
~ inventory = []
~ inventory.append("Brass Key")
```

And this worked great! But let's pause for a second. What's actually happening when you write `.append("Brass Key")`?

You're calling a **method**. A method is like a special action that an object knows how to do. Lists *know* how to add items. They have built-in superpowers.

In this tutorial, we're going to explore the superpowers that Python objects *already have*, before we learn to create our own.

**By the end of this tutorial, you will know how to:**

- Recognize that lists, dictionaries, and strings are **objects**
- Use **methods** to make objects do things (`.append()`, `.remove()`, `.upper()`)
- Understand the **dot notation** (`object.method()`)
- See why objects are useful for organizing related data and behavior

---

## 1. Your List is Already an Object

You've been using objects this whole time! Every time you create a list, you're creating an **object**—a smart container that knows how to do things.

Let's explore what a list can do. Create a new story file called **`exploring_objects.bard`**:

```bard
:: Start
~ shopping_list = ["bread", "milk", "eggs"]

Your shopping list: {shopping_list}

+ [Let's explore what lists can do] -> List_Methods
```

### List Methods You Already Know

```bard
:: List_Methods
~ shopping_list = ["bread", "milk", "eggs"]

**Original list:** {shopping_list}

Now let's see what this list can do!

+ [Add an item (.append)] -> Add_Item
+ [Remove an item (.remove)] -> Remove_Item
+ [Count items (len)] -> Count_Items
+ [Start over] -> Start
```

### Adding Items

```bard
:: Add_Item
~ shopping_list = ["bread", "milk", "eggs"]
~ shopping_list.append("cheese")

**After adding cheese:** {shopping_list}

The list "knew" how to add an item to itself!

+ [Try removing something] -> Remove_Item
+ [Back to methods] -> List_Methods
```

### Removing Items

```bard
:: Remove_Item
~ shopping_list = ["bread", "milk", "eggs", "cheese"]
~ shopping_list.remove("milk")

**After removing milk:** {shopping_list}

The list "knew" how to remove an item!

+ [Try something else] -> More_List_Powers
+ [Back to methods] -> List_Methods
```

---

## 2. Lists Have Even More Powers

Methods are functions that "belong to" an object. Let's see more of what lists can do:

```bard
:: More_List_Powers
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]

**Original:** {numbers}

Let's try some list superpowers!

+ [Sort the list] -> Sort_List
+ [Reverse the list] -> Reverse_List
+ [Count how many 1s] -> Count_Ones
+ [Find where 4 is] -> Index_Of
```

### Sorting

```bard
:: Sort_List
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]
~ numbers.sort()

**After sorting:** {numbers}

Lists know how to organize themselves!

+ [Back] -> More_List_Powers
```

### Reversing

```bard
:: Reverse_List
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]
~ numbers.reverse()

**After reversing:** {numbers}

Lists can flip themselves around!

+ [Back] -> More_List_Powers
```

### Counting Occurrences

```bard
:: Count_Ones
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]
~ how_many = numbers.count(1)

**How many 1s are there?** {how_many}

Lists can count how many times something appears!

+ [Back] -> More_List_Powers
```

### Finding Position

```bard
:: Index_Of
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]
~ position = numbers.index(4)

**Where is 4?** Position {position} (remember: counting starts at 0!)

Lists can tell you where something is!

+ [Back] -> More_List_Powers
+ [Let's look at strings now] -> String_Methods
```

---

## 3. Strings Are Objects Too

Every piece of text in your game is also an object with superpowers.

```bard
:: String_Methods
~ player_name = "aria the brave"

**Original name:** {player_name}

Strings are objects too! Let's see what they can do.

+ [Make it uppercase] -> Uppercase
+ [Make it title case] -> Title_Case
+ [Count letters] -> Count_Letters
+ [Check what it starts with] -> Starts_With
```

### String Transformations

```bard
:: Uppercase
~ player_name = "aria the brave"
~ loud_name = player_name.upper()

**Original:** {player_name}
**UPPERCASE:** {loud_name}

Strings know how to shout!

+ [Back] -> String_Methods
```

```bard
:: Title_Case
~ player_name = "aria the brave"
~ proper_name = player_name.title()

**Original:** {player_name}
**Title Case:** {proper_name}

Strings know how to be proper!

+ [Back] -> String_Methods
```

### String Inspection

```bard
:: Count_Letters
~ player_name = "aria the brave"
~ letter_count = player_name.count("a")

**How many 'a's?** {letter_count}

Strings can count their own letters!

+ [Back] -> String_Methods
```

```bard
:: Starts_With
~ player_name = "aria the brave"
~ starts_with_a = player_name.startswith("aria")

**Starts with 'aria'?** {starts_with_a}

Strings can check what they begin with!

+ [Back] -> String_Methods
+ [Let's combine what we've learned] -> Combining_Powers
```

---

## 4. Combining Object Powers

Now let's use multiple object methods together to do something useful:

```bard
:: Combining_Powers
~ player_input = "  HELLO WORLD  "

**Raw input:** "{player_input}"

Let's clean this up using string methods:

+ [See the cleaned version] -> Clean_Input
```

```bard
:: Clean_Input
~ player_input = "  HELLO WORLD  "
~ cleaned = player_input.strip().lower().title()

**Before:** "{player_input}"
**After:** "{cleaned}"

We used THREE methods in a row:
1. `.strip()` - remove extra spaces
2. `.lower()` - make it lowercase
3. `.title()` - capitalize each word

This is called "method chaining"!

+ [Another example] -> Parse_Command
+ [Back] -> String_Methods
```

### Practical Example: Command Parsing

```bard
:: Parse_Command
~ command = "  TAKE KEY  "
~ words = command.strip().lower().split()

**Original command:** "{command}"
**Parsed into words:** {words}

Now we can check what the player wants to do!

@py:
action = words[0] if len(words) > 0 else ""
target = words[1] if len(words) > 1 else ""
@endpy

**Action:** {action}
**Target:** {target}

This is how game parsers work!

+ [See how dictionaries work] -> Dict_Methods
+ [Back to start] -> Start
```

---

## 5. Dictionaries Have Methods Too

Remember your character sheet from Part 2.5? Let's explore what dictionaries can do:

```bard
:: Dict_Methods
~ hero = {
    "name": "Aria",
    "health": 100,
    "gold": 50
}

Your hero: {hero}

Dictionaries have their own superpowers!

+ [Get all keys] -> Dict_Keys
+ [Get all values] -> Dict_Values
+ [Get key-value pairs] -> Dict_Items
+ [Check if key exists] -> Check_Key
```

### Dictionary Methods

```bard
:: Dict_Keys
~ hero = {"name": "Aria", "health": 100, "gold": 50}
~ all_keys = list(hero.keys())

**All the keys:** {all_keys}

This shows us what data we're tracking!

+ [Back] -> Dict_Methods
```

```bard
:: Dict_Values
~ hero = {"name": "Aria", "health": 100, "gold": 50}
~ all_values = list(hero.values())

**All the values:** {all_values}

+ [Back] -> Dict_Methods
```

```bard
:: Dict_Items
~ hero = {"name": "Aria", "health": 100, "gold": 50}

Let's loop through all key-value pairs:

@for key, value in hero.items():
**{key}:** {value}
@endfor

This is super useful for displaying character stats!

+ [Back] -> Dict_Methods
```

```bard
:: Check_Key
~ hero = {"name": "Aria", "health": 100, "gold": 50}

@if "mana" in hero:
    You have {hero["mana"]} mana.
@else:
    You don't have a mana stat yet.
@endif

Checking before accessing prevents errors!

+ [Back] -> Dict_Methods
+ [Why does this matter?] -> Why_It_Matters
```

---

## 6. Why Does This All Matter?

Let's step back. You've now seen that **objects have data AND behavior bundled together**.

```bard
:: Why_It_Matters

Think about what you've learned:

**Lists** aren't just containers—they *know* how to:
- Add items (`.append()`)
- Remove items (`.remove()`)
- Sort themselves (`.sort()`)
- Tell you how long they are (`len()`)

**Strings** aren't just text—they *know* how to:
- Change case (`.upper()`, `.lower()`)
- Split into words (`.split()`)
- Check their contents (`.startswith()`, `.count()`)

**Dictionaries** aren't just data—they *know* how to:
- List their keys (`.keys()`)
- List their values (`.values()`)
- Let you check what's inside (`in`)

**This is the power of objects:**
Data + Behavior = Smart, Reusable Code

+ [So... what if I could make my own?] -> The_Big_Question
```

---

## 7. The "Aha!" Moment

```bard
:: The_Big_Question

Here's the thing:

Lists, strings, and dictionaries are **built into Python**.
Someone already wrote them for you.

But what if you want a **custom object** for your game?

What if you want:
- An **Item** object that knows its weight and can describe itself?
- A **Character** object that knows how to take damage and heal?
- A **Card** object that knows its meaning and can flip itself?

**You can make those!**

That's what we're going to learn next.

You already know:
âœ… Objects have data (like `hero["health"]`)
âœ… Objects have methods (like `inventory.append()`)
âœ… You use **dot notation** to call methods

Now we're going to learn:
âš¡ How to create your OWN objects
âš¡ How to give them custom methods
âš¡ How to use them in your stories

+ [I'm ready to create my own objects!] -> Ready_For_3B
+ [Let me practice what I learned] -> Practice
```

```bard
:: Practice

Good idea! Before moving on, try modifying this story:

1. Add more items to the shopping list
2. Try different string methods on player names
3. Add more stats to the hero dictionary
4. Experiment with method chaining

When you're ready, come back and continue to Part 3B!

+ [I'm ready now] -> Ready_For_3B
```

```bard
:: Ready_For_3B

Perfect! You now understand:

1. **What objects are** (data + behavior together)
2. **How to use methods** (the `.method()` syntax)
3. **Why objects are useful** (they know how to do things!)

In Part 3B, we'll take this understanding and learn how to create our own custom Item class from scratch.

[**Continue to Part 3B: Creating Your Own Objects →**](03B_creating_objects.md)
```

---

## Your Complete Story File

Here's the full code for this exploration:

```bard
:: Start
~ shopping_list = ["bread", "milk", "eggs"]

Your shopping list: {shopping_list}

+ [Let's explore what lists can do] -> List_Methods

:: List_Methods
~ shopping_list = ["bread", "milk", "eggs"]

**Original list:** {shopping_list}

Now let's see what this list can do!

+ [Add an item (.append)] -> Add_Item
+ [Remove an item (.remove)] -> Remove_Item
+ [Try more powers] -> More_List_Powers

:: Add_Item
~ shopping_list = ["bread", "milk", "eggs"]
~ shopping_list.append("cheese")

**After adding cheese:** {shopping_list}

The list "knew" how to add an item to itself!

+ [Back to methods] -> List_Methods

:: More_List_Powers
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]

**Original:** {numbers}

+ [Sort the list] -> Sort_List
+ [Reverse the list] -> Reverse_List
+ [Try strings] -> String_Methods

:: Sort_List
~ numbers = [3, 1, 4, 1, 5, 9, 2, 6]
~ numbers.sort()

**After sorting:** {numbers}

+ [Back] -> More_List_Powers

:: String_Methods
~ player_name = "aria the brave"

**Original name:** {player_name}

+ [Make it uppercase] -> Uppercase
+ [Make it title case] -> Title_Case
+ [Combine methods] -> Combining_Powers

:: Uppercase
~ player_name = "aria the brave"
~ loud_name = player_name.upper()

**Original:** {player_name}
**UPPERCASE:** {loud_name}

+ [Back] -> String_Methods

:: Title_Case
~ player_name = "aria the brave"
~ proper_name = player_name.title()

**Original:** {player_name}
**Title Case:** {proper_name}

+ [Back] -> String_Methods

:: Combining_Powers
~ player_input = "  HELLO WORLD  "
~ cleaned = player_input.strip().lower().title()

**Before:** "{player_input}"
**After:** "{cleaned}"

We used THREE methods: .strip(), .lower(), .title()

+ [See dictionaries] -> Dict_Methods

:: Dict_Methods
~ hero = {"name": "Aria", "health": 100, "gold": 50}

@for key, value in hero.items():
**{key}:** {value}
@endfor

+ [Why does this matter?] -> Why_It_Matters

:: Why_It_Matters

**Objects = Data + Behavior**

Lists, strings, and dictionaries all have built-in methods.

What if you could make your OWN objects?

+ [I'm ready!] -> Ready_For_3B

:: Ready_For_3B

Perfect! You understand:
- What objects are
- How to use methods
- Why objects are useful

[**Continue to Part 3B →**](03B_creating_objects.md)
```

---

## Compile and Play

```bash
bardic compile exploring_objects.bard
bardic play exploring_objects.json
```

Play through and explore all the object methods! When you're comfortable with the concept of "objects have superpowers," you're ready for Part 3B.

---

## Key Takeaways

You learned that:

✅ **Everything in Python is an object** (lists, strings, dictionaries)
✅ **Objects bundle data and behavior together**
✅ **Methods are functions that objects know how to do**
✅ **Dot notation** (`object.method()`) is how you call methods
✅ **You can chain methods** (`.strip().lower().title()`)

Most importantly: **You've been using objects this whole time!** Now you're just making that knowledge explicit.

---

## 🎓 Congratulations! You're a Bardic Writer

You've completed the core tutorial. At this point, you can:

- ✅ Build complex branching narratives
- ✅ Track inventory and character stats
- ✅ Use conditionals and loops
- ✅ Create full interactive fiction games

**You don't need to continue.** The remaining parts are optional
advanced features for power users.

### Ready to Build Your Game?

Stop here and start your project! Or...

### Want More Power?

Continue to Part 3B to learn about custom Python objects.
This unlocks even more possibilities but isn't required
for most stories.

---

Ready to create your own objects? Let's go!

**[Continue to Part 3B: Creating Your Own Objects →](03b_creating_objects.md)**
