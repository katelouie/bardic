/*
 * Custom JavaScript for your Bardic browser game.
 *
 * Use the Bardic API to register directive renderers, sidebar content,
 * lifecycle hooks, and more. This file loads before the game engine,
 * so everything you register here is ready when the game starts.
 *
 * Full API reference:
 * https://github.com/katelouie/bardic/blob/main/docs/browser-customization.md
 */


// ── Sidebar ──
// Show game stats in the sidebar panel.
// The function receives the full game state as a plain object.
// Return an HTML string to display. The sidebar opens automatically.

Bardic.sidebar((state) => {
    // Only show sidebar once the game has started (gold exists)
    if (state.gold === undefined) return null;

    return `
        <h3>Traveler</h3>
        <p>HP: ${state.hp || 0}</p>
        <p>Gold: ${state.gold || 0}</p>
        <p>Items: ${state.items_bought || 0}</p>
        ${state.has_map ? '<p>Map: Yes</p>' : ''}
    `;
});


// ── Custom Directive Renderers ──
// Register renderers for @render directives in your .bard story.
// Each function receives the directive data and returns a DOM element
// (or null to handle rendering elsewhere, like in a modal).

Bardic.directive('item_display', (data) => {
    const el = document.createElement('div');
    el.style.cssText = 'padding: 1rem; margin: 1rem 0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;';
    el.innerHTML = `
        <p style="color: var(--accent-color); margin: 0 0 0.5rem;">
            <strong>Merchant's Wares</strong>
        </p>
        <p style="margin: 0; font-size: 0.9rem; color: var(--text-muted);">
            ${data.items_bought > 0
                ? `You've purchased ${data.items_bought} item${data.items_bought > 1 ? 's' : ''} so far.`
                : 'Browse the selection below.'}
        </p>
    `;
    return el;
});


// ── Per-Passage Backgrounds ──
// Map passage IDs to background images from your assets/ folder.
// Uncomment and customize:

// Bardic.backgrounds({
//     'Start': '/assets/backgrounds/crossroads.png',
//     'BrowseWares': '/assets/backgrounds/market.png',
//     'Leave': '/assets/backgrounds/road.png',
// });


// ── Lifecycle Hooks ──

// Fires after the engine initializes and the first passage renders
Bardic.on('start', () => {
    console.log('Game started!');
});

// Fires after every passage render
// Bardic.on('passageRender', (passageId, output) => {
//     console.log(`Rendered passage: ${passageId}`);
// });

// Fires just before a choice is sent to the engine
// Bardic.on('beforeChoice', (choiceIndex) => {
//     console.log(`Player chose option ${choiceIndex}`);
// });


// ── Modal Example ──
// You can open modals from directive renderers:
//
// Bardic.directive('item_detail', (data) => {
//     Bardic.openModal(`
//         <h2>${data.name}</h2>
//         <p>${data.description}</p>
//         <button onclick="Bardic.closeModal()">Close</button>
//     `);
//     return null;  // Don't add to passage content
// });
