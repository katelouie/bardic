# Step 0: Installation - Choose Your Path

Welcome! Before you can start building interactive fiction with Bardic, you need to get it installed on your computer.

**We have two installation guides depending on your experience:**

---

## 🎨 Path A: For Writers & Complete Beginners

**Choose this if:**

- ❓ You've never used Python before
- ❓ Terms like "pip", "venv", and "PATH" are confusing
- ❓ You just want to write stories and don't care about Python details
- ❓ You want the simplest possible setup

**What you'll use:** Pixi (handles everything automatically)

**Time:** 10 minutes

**[→ Go to Step 0A: Installation for Beginners](00a_installation_pixi.md)**

---

## 👨‍💻 Path B: For Python Developers

**Choose this if:**

- ✅ You already have Python installed
- ✅ You're comfortable with pip, venv, and the command line
- ✅ You want to use your existing Python workflow
- ✅ You might integrate Bardic with other Python projects

**What you'll use:** Standard pip and virtualenv

**Time:** 5 minutes (if you know what you're doing)

**[→ Go to Step 0B: Installation for Python Users](00b_installation_python.md)**

---

## Still Not Sure?

### "I've used Twine/Ink before, but never Python..."

**→ Choose Path A** (Beginners)

Interactive fiction tools like Twine and Ink don't require Python knowledge. Even though Bardic integrates with Python, we've made Path A so you don't need to understand Python to get started.

### "I've written Python scripts before, but I'm not a professional developer..."

**→ Choose Path A** (Beginners)

If you're not comfortable with virtual environments and package management, Path A will save you headaches. You can always switch to the standard Python workflow later.

### "I maintain Python projects professionally..."

**→ Choose Path B** (Python Users)

You'll want the standard pip/venv workflow that integrates with your existing tools and workflows.

### "I'm teaching Bardic to a class or group..."

**→ Recommend Path A** for everyone

Pixi eliminates the most common installation problems across different operating systems and Python versions. Everyone will get the same setup with minimal troubleshooting.

---

## Can I Switch Later?

**Yes!** Both paths install the same Bardic. Your story files (`.bard`) work exactly the same way regardless of installation method.

- If you start with **Path A (Pixi)** and later want to use standard Python, just:

  ```bash
  pip install bardic
  ```

- If you start with **Path B (pip)** and want the simplicity of Pixi, just:

  ```bash
  curl -fsSL https://pixi.sh/install.sh | bash
  pixi add bardic
  ```

Your story files don't change. Only your installation method changes.

---

## Quick Comparison

| Feature | Path A (Pixi) | Path B (pip) |
|---------|---------------|--------------|
| Ease of setup | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Automatic Python installation | ✅ Yes | ❌ No (BYO Python) |
| Cross-platform consistency | ✅ Yes | ⚠️ Varies |
| Isolated environments | ✅ Automatic | 🔧 Manual (venv) |
| Integration with Python projects | ⚠️ Limited | ✅ Full |
| Community solutions online | ⚠️ Newer tool | ✅ Established |
| Best for | Writers, beginners | Developers |

---

## What About Other Tools?

You might have heard about:

- **Conda/Anaconda** - Good for data science, but overkill for Bardic
- **Poetry** - Great for Python packages, but adds complexity for beginners
- **uv** - Very new and fast, but less documentation available

For simplicity, we recommend **either Path A or Path B** above.

If you have strong preferences for other tools, you can adapt the instructions from Path B.

---

## System Requirements

**Both paths work on:**

- ✅ macOS (10.15+)
- ✅ Windows (10/11)
- ✅ Linux (most distributions)

**You need:**

- Internet connection (for installation)
- ~500MB disk space
- Admin/sudo access (for installation only)

---

## Installation Problems?

**Common issues and solutions:**

### "I don't have admin/sudo access on this computer"

- **Path A (Pixi):** Can install to user directory without admin
- **Path B (pip):** Use `pip install --user bardic`

### "I'm on a corporate computer with restricted internet"

Ask your IT department to whitelist:

- `pypi.org` (for pip)
- `pixi.sh` and `conda-forge.org` (for Pixi)

### "I'm offline most of the time"

Both paths require internet for initial installation, but work offline after setup.

### "I have an older computer"

Bardic is very lightweight. If you can run Python 3.10+, you can run Bardic.

---

## Ready to Install?

Choose your path and let's get started:

**[→ Path A: For Beginners (Pixi)](00a_installation_pixi.md)**

**[→ Path B: For Python Users (pip)](00b_installation_python.md)**

---

Once you're installed, you'll continue to **[Part 1: Your First Branching Story](01_first_story.md)** where the real fun begins!
