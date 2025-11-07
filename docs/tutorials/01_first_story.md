# Part 1: Your First Branching Story

Welcome to Bardic! This is the first step on your journey. In this tutorial, we're going to create a small, complete, branching story. We won't use any Python, just Bardic's simple syntax for writing and linking passages.

By the end, you will know how to:

- Create "pages" in your story, called **passages**.
- Link them together with **choices**.
- **Compile** your story into a file the computer can read.
- **Play** your story in the terminal.

## 1. Create Your Story File

First, open your favorite text editor (like VS Code, Sublime Text, or even Notepad). If you use VS Code, you can also install the [VS Code Bardic extension](https://github.com/katelouie/bardic-vscode).

Create a new file and save it as `my_story.bard`. The `.bard` extension is how the compiler knows it's a Bardic story file.

## 2. Write Your First Passage

All Bardic stories are made of **passages**. A passage is just a block of text, like a page in a "Choose Your Own Adventure" book.

You create a passage by typing `::` followed by a space and the passage's name.

Let's create our first passage. In your `my_story.bard` file, type this:

```bard
:: Start
You wake up in a small room. There's a wooden door to the north
and a small window on the east wall.

The air is dusty.
```

This is your starting passage. By default, Bardic looks for a passage named `Start` to begin the game.

## 3. Add Choices

A story isn't very interactive without choices! A **choice** links one passage to another.

You create a choice by starting a line with `+`, followed by the choice text in brackets `[]`, and then an arrow `->` pointing to the passage it leads to.

Let's add two choices to your `Start` passage:

```bard
:: Start
You wake up in a small room. There's a wooden door to the north
and a small window on the east wall.

The air is dusty.

+ [Examine the door] -> Door
+ [Look out the window] -> Window
```

## 4. Write the Other Passages

Great! You've created links to two new passages: `Door` and `Window`. But... we haven't written them yet! If we tried to play the story now, the game would crash because it wouldn't know where to go.

Let's create those passages. Add these to your file, below your `Start` passage:

```bard
:: Door
You walk up to the door. It's made of heavy oak and has a
large, iron lock. It doesn't budge.

+ [Look out the window] -> Window
+ [Go back to the center of the room] -> Start

:: Window
You peer through the dusty glass. Outside, you see a
dense, sunlit forest. It looks peaceful.

+ [Examine the door] -> Door
+ [Go back to the center of the room] -> Start
```

## 5. Your Complete Story File

Your final `my_story.bard` file should look like this:

```bard
:: Start
You wake up in a small room. There's a wooden door to the north
and a small window on the east wall.

The air is dusty.

+ [Examine the door] -> Door
+ [Look out the window] -> Window

:: Door
You walk up to the door. It's made of heavy oak and has a
large, iron lock. It doesn't budge.

+ [Look out the window] -> Window
+ [Go back to the center of the room] -> Start

:: Window
You peer through the dusty glass. Outside, you see a
dense, sunlit forest. It looks peaceful.

+ [Examine the door] -> Door
+ [Go back to the center of the room] -> Start
```

Congratulations! You've written a complete, branching story. Now, let's play it.

## 6. Compile Your Story

Open your computer's terminal (or command prompt). Navigate to the directory where you saved `my_story.bard`.

The Bardic engine can't read `.bard` files directly. We first need to **compile** it into a `.json` file that the engine understands.

Run this command:

```bash
bardic compile my_story.bard
```

Or if you installed with `pixi` you would run:

```bash
pixi run bardic compile my_story.bard
```

You should see a success message. If you look in your folder, you'll now see a new file: `my_story.json`. This is your playable game!

## 7. Play Your Story

It's time to play. In your terminal, run the `play` command:

```bash
bardic play my_story.json
```

Or if you installed with `pixi` you'd run:

```bash
pixi run bardic play my_story.json
```

Your story will start in the terminal. You'll see your `Start` passage text, followed by your choices with numbers next to them:

```sh
▸ Start

  You wake up in a small room. There's a wooden door to the north
  and a small window on the east wall.

  The air is dusty.

----------------------------------------------------------------------

What do you do?

  1. Examine the door
  2. Look out the window

→
```

Type `1` and press Enter to make a choice. You can now navigate through your entire story! To quit, press `Ctrl+C`.

## You Did It

You've successfully created and played your first Bardic story. You learned the core building blocks: passages (`::`) and choices (`+`).

In the next part, we'll explore how to give your story a *memory* using variables and conditional logic.

[Continue to Part 2: Adding State & Memory](02_state_memory.md)
