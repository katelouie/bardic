# The Bardic Guided Tour: From Writer to Python Magician

Welcome! This is the official tutorial series for Bardic, designed to take you from "Hello, World" to a fully-functioning, Python-powered interactive game.

## What's This All About?

You don't need to be a programmer to start, but Bardic's real magic comes from its "Python-first" design. This tutorial series is a single, linear path that gently introduces new concepts.

You'll start as a **Writer**, learning to create simple branching passages. Along the way, you'll become a **Technical Writer**, learning to add logic and memory to your story. By the end, you'll be a **Python Magician**, able to import your own custom classes and build complex narrative systems.

No matter your skill level, start at Part 1. Each lesson builds on the last.

## The Tutorial Series

### Phase 0: Getting Set Up

- **[Part 0: Downloading Bardic (and Python) - Choose Your Path](00_installation_choice.md)**
  - Get set up with Bardic and Python. I promise it's simple and fast!
  - **You'll create:** A Python install with Bardic included

### Phase 1: The Writer (Start Here!)

- **[Part 1: Your First Branching Story](01_first_story.md)**
  - Learn the absolute basics. We'll create "pages" (passages), link them with choices (`+`), and play your first story in the terminal.
  - **You'll create:** A playable branching story

### Phase 2: The Technical Writer

- **[Part 2: Adding State & Memory](02_state_memory.md)**
  - Let's make your story remember things. We'll use variables (`~`), conditional logic (`@if:`), and one-time choices (`*`) to build a classic "locked door and key" puzzle.
  - **You'll create:** A puzzle game with state

- **[Part 2.5: Complex State (Lists and Dictionaries)](02_5_complex_state.md)**
  - Go beyond simple variables. Learn to use lists for inventories and dictionaries for character sheets.
  - **You'll create:** An inventory system and character stats

### Phase 3: The Python Magician

- **[Part 3A: Objects Have Superpowers](03a_objects_superpowers.md)**
  - Discover that lists, strings, and dictionaries are objects with built-in methods. Learn to use `.append()`, `.upper()`, `.keys()` and more.
  - **You'll learn:** What objects are and how to use their methods

- **[Part 3B: Creating Your Own Objects](03b_creating_objects.md)**
  - Now create your OWN objects! Learn to write a simple `Item` class, import it into your story, and give objects custom superpowers.
  - **You'll create:** A custom Item class and shopping system

### Phase 4: The Game Developer

- **[Part 4: Building a "Game" with a Custom UI](04_custom_ui.md)**
  - Let's break out of the terminal. You'll learn how to use the NiceGUI template, ask for the player's name with `@input`, and send game data to your UI with `@render`.
  - **You'll create:** A web-based game with custom UI

- **[Part 5: Finishing & Polishing Your Story](05_finish_polish.md)**
  - Your story is getting big! We'll cover the tools you need to manage a real project, like splitting your files with `@include` and debugging your plot with the `bardic graph` visualizer.
  - **You'll learn:** Project organization and professional workflows

---

## Quick Reference: What You'll Learn When

| Part | What You Can Build After |
|------|--------------------------|
| 1 | Simple branching stories (like Twine) |
| 2 | Stories with memory and puzzles |
| 2.5 | Games with inventories and stats |
| 3A | Stories using built-in object methods |
| 3B | Games with custom Python objects |
| 4 | Web-based games with custom UIs |
| 5 | Large-scale, organized projects |

## Two Paths Through the Tutorial

### 🎨 The Writer's Path (Minimum Code)

If you want to make interactive fiction without diving too deep into programming:

1. **Complete:** Parts 1, 2, 2.5
2. **Skim:** Part 3A (just see what objects can do)
3. **Skip:** Part 3B (unless you get curious!)
4. **Optional:** Part 4 (only if you want custom UI)
5. **Complete:** Part 5 (learn project organization)

**Result:** You can build complete IF games with variables, conditionals, loops, and complex data structures. This is enough for most stories!

### 👨‍💻 The Developer's Path (Full Power)

If you want to leverage Python's full capabilities:

1. **Complete:** All parts in order
2. **Focus on:** Part 3B (this is the game-changer)
3. **Definitely do:** Part 4 (custom UIs are powerful)
4. **Master:** Part 5 (for building large projects)

**Result:** You can build complex narrative systems with custom objects, external APIs, databases, and professional UIs.

---

## 🎯 Start Here

**Ready? Let's get started!**

**[→ Begin with Part 1: Your First Branching Story](01_first_story.md)**

---

## Prerequisites

- **No programming experience needed** for Parts 1-2
- **Basic comfort with text files** (you should know how to create/save a text file)
- **Python 3.8+** installed on your computer
- **A text editor** (VS Code recommended, but Notepad works too!)
- **Bardic installed:** `pip install bardic`

---

## Learning Tips

1. **Type everything yourself.** Don't copy-paste the code examples—typing helps you learn.
2. **Experiment freely.** Try changing values, adding passages, breaking things!
3. **Play your story often.** Compile and test after every few passages.
4. **Don't rush Part 3.** The concept of objects is fundamental—take your time.
5. **Ask for help.** Join our [Discord](https://discord.gg/bardic) if you get stuck!

---

## Bardic Syntax At-a-Glance

- **Passages**: `:: Name`
- **Choices**: `+ [Text] -> Target` (sticky) or `* [Text] -> Target` (one-time)
- **Variables**: `~ variable = value`
- **Display**: `{variable}` or `{expression}`
- **Conditionals**: `@if condition:` ... `@endif`
- **Loops**: `@for item in list:` ... `@endfor`
- **Python**: `@py:` ... `@endpy`

---

## Optional Materials

- **[Custom Classes Deep Dive](custom-classes.md)** - Advanced guide to serialization and best practices
- **[Language Specification](../spec.md)** - Complete syntax reference
- **[Example Games](https://github.com/bardic-lang/examples)** - See Bardic in action

---

## Index of All Parts

1. [Your First Branching Story](01_first_story.md)
2. [Adding State & Memory](02_state_memory.md)
3. [Complex State (Lists & Dictionaries)](02_5_complex_state.md)
4. [Objects Have Superpowers](03A_objects_have_superpowers.md)
5. [Creating Your Own Objects](03B_creating_objects.md)
6. [Building a Custom UI](04_custom_ui.md)
7. [Finishing & Polishing Your Story](05_finish_polish.md)

---

**Ready to begin? [Start with Part 1 →](01_first_story.md)**
