# The Coffee Shop Encounter

A simple romance story teaching relationship tracking with the `bardic.stdlib.relationship` module.

## What This Teaches

- **Relationship tracking** with trust, comfort, openness
- **Conditional rendering** based on relationship state
- **Inline conditionals** (`{condition ? text | other}`)
- **Topic tracking** for story progression
- **Multiple endings** based on player choices

## How to Play

```bash
# Compile
bardic compile coffee_shop.bard

# Play in terminal
bardic play coffee_shop.json

# Or run with NiceGUI
python player.py coffee_shop.json
```

## Modules Used

- `bardic.stdlib.relationship` - Tracks Alex's trust, comfort, and openness

## Story Structure

3 major paths:

1. **Deep Connection** (high trust) → Kiss or Confess
2. **Slow Build** (medium trust) → Friendship route
3. **Bad Ending** (low trust) → Missed connection

Your choices affect Alex's emotional state, which gates certain story beats.
