# Testing Render Directives - Step by Step

## Quick Start

1. **Compile the demo story:**
   ```bash
   bardic compile stories/test/test_render_demo.bard -o compiled_stories/test_render_demo.json
   ```

2. **Start the web runtime:**
   ```bash
   bardic serve
   ```

3. **Open browser** (should auto-open to http://localhost:5173)

4. **Select "Test Render Demo"** from the story list

5. **You should see:**
   - Three tarot cards displayed in a row
   - Card detail panels for each card
   - An interpretation panel at the end

---

## What to Check

### ✅ Directives Are Rendering

**Look for:**
- Card spread component showing three cards
- Card detail components with card info
- Interpretation panel with styled content

**If you see raw JSON instead:**
- Component isn't registered properly
- Check browser console for errors
- Verify component names match exactly

### ✅ Console Logs Show Data

**Open browser console (F12)**, you should see:

```javascript
Story started: {...}
Render directives: [
  {
    type: "render_directive",
    name: "card_spread",
    mode: "evaluated",
    data: {
      cards: [...],
      layout: "three_card"
    }
  },
  ...
]
```

**If directives array is empty:**
- Backend didn't process directives
- Check backend console for Python errors
- Verify story compiled correctly

### ✅ Styled Components Appear

**Expected styling:**
- Purple/pink color scheme
- Cards with borders and shadows
- Smooth hover effects
- Proper spacing

**If styling is broken:**
- Check `App.css` is loaded
- Verify inline styles in components
- Check for console CSS errors

---

## Testing Different Directive Types

### Test 1: Simple Directive (No Args)

**Story:**
```bard
@render simple_component()
```

**Expected output:**
```json
{
  "name": "simple_component",
  "data": {}
}
```

### Test 2: Directive with Positional Args

**Story:**
```bard
~ value = 42
@render my_component(value, "hello")
```

**Expected output:**
```json
{
  "name": "my_component",
  "data": {
    "arg_0": 42,
    "arg_1": "hello"
  }
}
```

### Test 3: Directive with Named Args

**Story:**
```bard
@render my_component(x=10, y=20, label="Test")
```

**Expected output:**
```json
{
  "name": "my_component",
  "data": {
    "x": 10,
    "y": 20,
    "label": "Test"
  }
}
```

### Test 4: Directive with Complex Objects

**Story:**
```bard
from game_logic.test_tarot_objects import Card

:: Test
~ card = Card("The Fool", 0, False)
@render card_detail(card, position="center")
```

**Expected:** Card object is serialized and sent to frontend

### Test 5: React Framework Hint

**Story:**
```bard
@render:react card_spread(cards, layout='three_card')
```

**Expected output:**
```json
{
  "name": "card_spread",
  "data": {...},
  "framework": "react",
  "react": {
    "componentName": "CardSpread",
    "key": "card_spread_a4b3c2d1",
    "props": {
      "cards": [...],
      "layout": "three_card"
    }
  }
}
```

---

## Debugging Issues

### Issue: "Component not found" in console

**Check:**
1. Component is imported in `componentRegistry.js`
2. Component is exported with `export default`
3. Name matches exactly (case-sensitive)
4. Component registry has proper mapping

**Fix:**
```javascript
// componentRegistry.js
import MyComponent from './MyComponent'

const componentRegistry = {
  'my_component': MyComponent,  // Add this line
  // ...
}
```

### Issue: Props are undefined/null

**Check:**
1. Directive arguments in story
2. Backend evaluation (check logs)
3. Component prop destructuring

**Fix:**
```jsx
function MyComponent({ data, myProp }) {
  // Handle both patterns
  const actualProp = myProp || data?.myProp || 'default'
  
  if (!actualProp) {
    return <div>Error: Missing required prop</div>
  }
  
  return <div>{actualProp}</div>
}
```

### Issue: Backend error during evaluation

**Check backend console for:**
```
Warning: Failed to evaluate render directive 'card_spread': name 'cards' is not defined
```

**Fix:** Make sure variables are defined before use:
```bard
:: Passage
~ cards = [Card("Fool", 0)]  # Define BEFORE use
@render card_spread(cards)    # Then use
```

### Issue: Directives not appearing at all

**Check:**
1. `render_directives` in API response
2. Component rendering logic in `App.jsx`
3. Console for JavaScript errors

**Debug in browser console:**
```javascript
// Check if directives are in passage data
console.log(passage.render_directives)

// Check component registry
import componentRegistry from './extensions/componentRegistry'
console.log(Object.keys(componentRegistry))
```

### Issue: Wrong data structure

**Check:**
- Are you using React hint vs no hint?
- Component expects `props` or `data.props`?

**Solution - handle both:**
```jsx
function MyComponent({ data, value, label }) {
  const actualValue = value ?? data?.value
  const actualLabel = label ?? data?.label
  
  return <div>{actualLabel}: {actualValue}</div>
}
```

---

## Creating Test Stories

### Template

```bard
from game_logic.test_tarot_objects import Card

:: Start
~ test_data = "Hello World"
~ test_number = 42
~ test_card = Card("The Fool", 0, False)

**Test Render Directives**

Testing simple directive:
@render test_component(message=test_data)

Testing with number:
@render test_component(value=test_number)

Testing with object:
@render card_detail(test_card)

+ [Continue] -> End

:: End
Test complete!
```

### Compile & Test

```bash
# Compile
bardic compile stories/test/my_test.bard -o compiled_stories/my_test.json

# Verify compilation
cat compiled_stories/my_test.json | jq '.passages.Start.content[] | select(.type=="render_directive")'

# Run
bardic serve
```

---

## Performance Tips

### Use React.memo for Static Components

```jsx
import { memo } from 'react'

const TarotCard = memo(function TarotCard({ card }) {
  return <div>{card.name}</div>
})

export default TarotCard
```

### Lazy Load Large Components

```jsx
import { lazy, Suspense } from 'react'

const HeavyComponent = lazy(() => import('./HeavyComponent'))

function MyComponent(props) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HeavyComponent {...props} />
    </Suspense>
  )
}
```

---

## Common Patterns

### Conditional Rendering

```jsx
function CardDetail({ card, showDetails = true }) {
  if (!card) return null
  
  return (
    <div className="card-detail">
      <h3>{card.name}</h3>
      {showDetails && <p>{card.description}</p>}
    </div>
  )
}
```

### List Rendering

```jsx
function CardList({ cards }) {
  return (
    <div className="card-list">
      {cards?.map((card, i) => (
        <TarotCard key={card.id || i} card={card} />
      ))}
    </div>
  )
}
```

### Error Boundaries

```jsx
function SafeComponent({ card }) {
  try {
    return <div>{card.name}</div>
  } catch (error) {
    console.error('Component error:', error)
    return <div className="error">Error rendering card</div>
  }
}
```

---

## Next Steps

1. **Create your own test story**
2. **Build a custom component**
3. **Register it in componentRegistry.js**
4. **Test end-to-end**
5. **Add styling and polish**

Happy building! 🎨
