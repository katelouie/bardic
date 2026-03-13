# Browser Template Customization

This guide covers how to customize your Bardic browser bundle using `custom.css`, `custom.js`, and the `Bardic` JavaScript API.

## Overview

When you run `bardic bundle story.bard`, the bundler automatically includes three customization files if they exist next to your story file:

| File | Purpose |
|------|---------|
| `custom.css` | Override theme variables, add game-specific styles |
| `custom.js` | Register directive renderers, sidebar, hooks |
| `assets/` | Images, fonts, audio — copied into the bundle |

```
my-game/
├── story.bard
├── custom.css          ← Auto-included
├── custom.js           ← Auto-included
└── assets/             ← Auto-copied
    ├── backgrounds/
    ├── cards/
    └── fonts/
```

---

## The `Bardic` JavaScript API

All browser-side customization goes through the global `Bardic` object. This is available in `custom.js` — no imports needed.

### `Bardic.directive(name, renderFn)`

Register a custom renderer for an `@render` directive.

Your `.bard` story uses `@render` to send structured data to the browser:

```bard
@py:
card_data = {"name": "The Fool", "src": "/assets/cards/00-fool.png"}
@endpy

@render tarot_card(card_data)
```

In `custom.js`, you tell the browser how to display it:

```javascript
Bardic.directive('tarot_card', (data) => {
    const img = document.createElement('img');
    img.src = data.card_data.src;
    img.alt = data.card_data.name;
    img.className = 'tarot-card';
    return img;  // Return a DOM element
});
```

**How it works:**
- The render function receives the directive's data as its argument
- Return a DOM element to add it to the passage content
- Return `null` to handle rendering elsewhere (e.g., into the sidebar or a modal)
- If no renderer is registered for a directive, a fallback debug display shows the directive name and data

**Built-in directives** (already registered, no custom.js needed):

| Name | What it does |
|------|-------------|
| `image` | Displays an image (`data.src`, `data.alt`, `data.width`, `data.pixel`) |
| `html` | Injects raw HTML (`data.content`) |
| `text_block` | Styled text block with optional inline style (`data.content`, `data.style`) |
| `sidebar` | Renders content into the sidebar panel (`data.content`) |
| `modal` | Opens content in a modal overlay (`data.content`) |

---

### `Bardic.sidebar(renderFn)`

Register a function that renders the sidebar after every passage change. The function receives the current game state as a plain object.

```javascript
Bardic.sidebar((state) => `
    <h3>Stats</h3>
    <p>HP: ${state.hp || 100}</p>
    <p>Gold: ${state.gold || 0}</p>
    <p>Location: ${state.location || 'Unknown'}</p>
`);
```

The sidebar is collapsed by default. It automatically opens when your renderer returns HTML content. Players can toggle it with the hamburger menu button.

---

### `Bardic.backgrounds(mapping)`

Set background images for specific passages. Keys are passage IDs (the name after `::` in your `.bard` file), values are image paths.

```javascript
Bardic.backgrounds({
    'ReadingRoom': '/assets/backgrounds/reading-room.png',
    'CardReveal': '/assets/backgrounds/table.png',
    'Forest': '/assets/backgrounds/forest.png',
});
```

When the player navigates to a mapped passage, the background image is applied to the page. When they navigate to an unmapped passage, the background is removed.

---

### `Bardic.on(event, handler)`

Register a lifecycle hook. You can register multiple handlers for the same event.

```javascript
Bardic.on('start', () => {
    console.log('Game started!');
});

Bardic.on('passageRender', (passageId, output) => {
    console.log(`Rendered: ${passageId}`);
});

Bardic.on('beforeChoice', (choiceIndex) => {
    // Play a click sound, animate the button, etc.
});
```

**Available events:**

| Event | Arguments | When it fires |
|-------|-----------|---------------|
| `start` | *(none)* | After the engine initializes and the first passage renders |
| `passageRender` | `(passageId, output)` | After each passage renders (content, directives, sidebar all done) |
| `beforeChoice` | `(choiceIndex)` | Just before a player's choice is sent to the engine |

**Typo protection:** If you register an unknown event name, the console will warn you and suggest the closest valid event. For example, `Bardic.on('strat', fn)` will warn: *"unknown event 'strat'. Did you mean 'start'?"*

---

### `Bardic.openModal(html)` / `Bardic.closeModal()`

Open or close the modal overlay. Useful from inside directive renderers for inventory screens, book views, card details, etc.

```javascript
Bardic.directive('view_book', (data) => {
    Bardic.openModal(`
        <h2>${data.title}</h2>
        <p>${data.content}</p>
        <button onclick="Bardic.closeModal()">Close</button>
    `);
    return null;  // Don't add anything to passage content
});
```

The modal can also be dismissed by:
- Pressing **Escape**
- Clicking the dark backdrop outside the modal content

---

## Custom CSS

`custom.css` loads after the base theme, so your styles override the defaults. The easiest way to customize is by overriding CSS variables:

```css
/* custom.css */
:root {
    --bg-color: #1a0a2e;
    --bg-secondary: #2d1b4e;
    --accent-color: #c084fc;
    --text-color: #f0e6ff;
    --font-main: 'Pixel Font', monospace;
    --image-rendering: pixelated;
    --border-radius: 0px;
}

/* Custom font */
@font-face {
    font-family: 'Pixel Font';
    src: url('/assets/fonts/pixel.woff2') format('woff2');
}

/* Custom choice buttons */
.choice-btn {
    background-image: url('/assets/ui/button.png');
    background-size: 100% 100%;
    image-rendering: pixelated;
    border: none;
}

.choice-btn:hover {
    background-image: url('/assets/ui/button-hover.png');
}
```

**Available CSS variables:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `--bg-color` | `#1a1a2e` | Page background |
| `--bg-secondary` | `#16213e` | Header, sidebar, cards |
| `--text-color` | `#eaeaea` | Main text |
| `--text-muted` | `#a0a0a0` | Secondary text |
| `--accent-color` | `#e94560` | Headings, highlights |
| `--accent-hover` | `#ff6b6b` | Hover state for accent |
| `--link-color` | `#4ecdc4` | Links |
| `--font-main` | Georgia, serif | Story text |
| `--font-ui` | System sans-serif | Buttons, headers |
| `--font-size-base` | `18px` | Base text size |
| `--line-height` | `1.7` | Line spacing |
| `--max-width` | `720px` | Content column width |
| `--border-radius` | `8px` | Corner rounding |
| `--image-rendering` | `auto` | Set to `pixelated` for pixel art |

---

## Complete Example: Pixel Art RPG

**custom.css:**
```css
:root {
    --bg-color: #0a0a1a;
    --accent-color: #ffd700;
    --font-main: 'Press Start 2P', monospace;
    --image-rendering: pixelated;
    --border-radius: 0px;
}
```

**custom.js:**
```javascript
// Show HP/Gold/XP in the sidebar
Bardic.sidebar((state) => `
    <h3>Hero</h3>
    <p>HP: ${state.hp || 100} / ${state.max_hp || 100}</p>
    <p>Gold: ${state.gold || 0}</p>
    <p>XP: ${state.xp || 0}</p>
`);

// Set scene backgrounds
Bardic.backgrounds({
    'Village': '/assets/bg/village.png',
    'Forest': '/assets/bg/forest.png',
    'Dungeon': '/assets/bg/dungeon.png',
});

// Custom component: enemy encounter
Bardic.directive('enemy', (data) => {
    const el = document.createElement('div');
    el.className = 'enemy-display';
    el.innerHTML = `
        <img src="/assets/enemies/${data.id}.png" class="pixel" alt="${data.name}">
        <p><strong>${data.name}</strong> — HP: ${data.hp}</p>
    `;
    return el;
});

// Play a sound on game start
Bardic.on('start', () => {
    const music = new Audio('/assets/audio/theme.mp3');
    music.loop = true;
    music.volume = 0.3;
    music.play().catch(() => {});  // Browsers block autoplay until interaction
});
```

**story.bard:**
```bard
:: Village
The village square is quiet this morning.

+ [Enter the forest] -> Forest

:: Forest
@py:
enemy_data = {"id": "goblin", "name": "Forest Goblin", "hp": 30}
@endpy

A goblin leaps from the bushes!

@render enemy(enemy_data)

+ [Fight!] -> Combat
+ [Run back to village] -> Village
```
