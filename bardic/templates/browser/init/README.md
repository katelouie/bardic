# Bardic Browser Bundle Template

A self-contained browser game built with [Bardic](https://github.com/katelouie/bardic). Bundle it and upload to itch.io or any static hosting.

## Quick Start

### 1. Bundle your game

```bash
bardic bundle example.bard
```

This creates a `dist/` directory with everything needed to run in a browser.

### 2. Test locally

Open `dist/index.html` in your browser, or use a local server:

```bash
python -m http.server -d dist 8000
```

Then open http://localhost:8000.

### 3. Deploy

Upload the `dist/` directory to itch.io (mark as "playable in browser") or any static hosting platform.

To create a zip for upload:

```bash
bardic bundle example.bard --zip
```

## Project Structure

```
your-game/
├── example.bard           # Your story (edit this!)
├── custom.css             # Override theme colors, fonts, layout
├── custom.js              # Sidebar, directive renderers, hooks
├── assets/                # Images, fonts, audio (auto-bundled)
├── game_logic/            # Custom Python modules for your story
├── linter/                # Custom lint checks
└── README.md              # This file
```

## Customization

- **`custom.css`** — Override CSS variables to change colors, fonts, and layout
- **`custom.js`** — Use the `Bardic` API to register sidebar, directive renderers, and hooks
- **`assets/`** — Put images, fonts, and audio here. Reference them as `/assets/...` in your story

See the [Browser Customization Guide](https://github.com/katelouie/bardic/blob/main/docs/browser-customization.md) for full API documentation.

## Writing Stories

See the [Bardic tutorials](https://github.com/katelouie/bardic/blob/main/docs/tutorials/README.md) and [language spec](https://github.com/katelouie/bardic/blob/main/docs/spec.md).

## Need Help?

- [Bardic Documentation](https://github.com/katelouie/bardic)
- [Report Issues](https://github.com/katelouie/bardic/issues)
