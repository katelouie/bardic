# Step 0: Getting Started (For Complete Beginners)

**Welcome!** Before we can start building your story, we need to set up Bardic on your computer. Don't worry—we're going to make this as simple as possible.

## 🎯 What We're Installing

You need two things:

1. **Pixi** - A tool that handles Python and packages (think of it as a smart assistant)
2. **Bardic** - The interactive fiction engine

**The good news?** Pixi will handle Python for you automatically. You don't need to install Python separately or worry about versions.

---

## Step 1: Install Pixi

Pixi is a modern package manager that makes Python projects simple. It handles everything in one place.

### On Mac or Linux

Open your **Terminal** app and paste this command:

```bash
curl -fsSL https://pixi.sh/install.sh | bash
```

Press Enter and wait for it to finish. You'll see some text scroll by—that's normal!

**After it finishes**, close and reopen your Terminal.

### On Windows

Open **PowerShell** (search for it in the Start menu) and paste this:

```powershell
iwr -useb https://pixi.sh/install.ps1 | iex
```

Press Enter and wait. After it finishes, close and reopen PowerShell.

Or you can [download the official Pixi installer](https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-pc-windows-msvc.msi).

### Verify It Worked

In your Terminal or PowerShell, type:

```bash
pixi --version
```

You should see something like `pixi 0.x.x`. If you do, great! Move to Step 2.

**If you see an error**, try closing and reopening your Terminal/PowerShell again.

---

## Step 2: Create Your First Bardic Project

Now we'll create a new folder for your game with Bardic already set up.

### In Terminal or PowerShell, type these commands

```bash
# Create a new folder called "my-first-story"
pixi init my-first-story

# Go into that folder
cd my-first-story

# Add Bardic and Python to the project
pixi add bardic python
```

**What just happened?**

- Pixi created a new project folder
- It set up Python and Bardic automatically
- Everything is isolated - it won't mess with anything else on your computer

---

## Step 3: Create Your First Story File

Let's create a simple story to make sure everything works.

### Create a file called `hello.bard`

Using your text editor (Notepad, TextEdit, VS Code, whatever you have), create a new file with this content:

```bard
:: Start
Welcome to your first Bardic story!

This is your starting passage.

+ [Continue] -> Next

:: Next
You clicked the button! Congratulations!

This is interactive fiction.

+ [Start over] -> Start
```

**Save this file** as `hello.bard` in your `my-first-story` folder.

---

## Step 4: Play Your Story

Time to see it in action!

### In Terminal or PowerShell (make sure you're still in the `my-first-story` folder)

```bash
pixi run bardic play hello.bard
```

**What you should see:**

- Your story text appears
- Numbered choices are shown
- You can type a number and press Enter to make choices

**Try it!** Play through your story a few times.

To quit, press `Ctrl+C` (hold Control and press C).

---

## 🎉 You Did It

You've successfully:

- ✅ Installed Pixi
- ✅ Created a Bardic project
- ✅ Written a story file
- ✅ Played your first interactive story

---

## Next Steps

Now that everything is working, you're ready for the actual tutorial!

**[→ Continue to Part 1: Your First Branching Story](01_first_story.md)**

---

## Common Questions

### "Do I need to 'activate' anything?"

**No!** That's the beauty of pixi. When you run `pixi run bardic`, it automatically uses the right Python and the right packages. You never have to think about activation.

### "Where is Python installed?"

Pixi installs Python in your project folder (in a hidden `.pixi` directory). It's completely isolated from anything else on your computer.

### "Can I use my existing Python?"

If you already have Python and know what you're doing, you can skip pixi and use regular pip. But if you're new, pixi will save you a lot of headaches!

### "What if I want to use VS Code?"

Great choice! VS Code works perfectly with pixi projects. Just:

1. Open VS Code
2. File → Open Folder
3. Select your `my-first-story` folder
4. Install the "Bardic" extension (search in Extensions tab)

VS Code will automatically detect the pixi environment.

### "I'm getting an error!"

Common fixes:

1. **Close and reopen** your Terminal/PowerShell
2. Make sure you're **in the project folder** (`cd my-first-story`)
3. Run `pixi install` to make sure everything is installed

---

## The Commands You'll Use

Here's a quick reference of the pixi commands you'll use most:

```bash
# Create a new project
pixi init my-story

# Go into the project folder
cd my-story

# Add Bardic and Python to the project (first time only)
pixi add bardic python

# Play a story
pixi run bardic play story.bard

# Compile a story to JSON
pixi run bardic compile story.bard

# Generate a story graph
pixi run bardic graph story.bard

# See all available commands
pixi run bardic --help
```

**Pro tip:** You can shorten `pixi run` by creating an alias. But for now, just use `pixi run bardic`.

---

## Alternative: Traditional Python Installation

If you prefer the standard Python approach or already have Python installed, see [Step 0B: Installation for Python Users](00b_installation_python.md) instead.

---

**Ready to start building stories?**

**[→ Continue to Part 1: Your First Branching Story](01_first_story.md)**
