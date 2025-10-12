# Frontend Extensions

This directory contains custom React components for render directives.

## How It Works

1. **Write `@render` directives in your `.bard` stories**
2. **Backend evaluates and sends structured data**
3. **Frontend maps directive names to React components**
4. **Components render with the provided data**

---

## Adding a New Component

### Step 1: Create Your Component

Create a new file in `src/extensions/`:

```jsx
// src/extensions/MyComponent.jsx
function MyComponent({ data1, data2, ...props }) {
  return (
    <div className="my-component">
      <h3>{data1}</h3>
      <p>{data2}</p>
    </div>
  )
}

export default MyComponent
```

### Step 2: Register in componentRegistry.js

```javascript
// src/extensions/componentRegistry.js
import MyComponent from './MyComponent'

const componentRegistry = {
  // ... existing components ...
  
  // Add your component
  'my_component': MyComponent,
  'MyComponent': MyComponent,  // PascalCase (for React hint)
  
  'default': DefaultDirective
}
```

### Step 3: Use in Stories

```bard
:: MyPassage
~ my_data = "Hello World"

@render my_component(data1=my_data, data2="More info")

Some text after the component.
```

---

## Component Props

Components receive props based on how directives are compiled:

### With React Hint (`@render:react`)

```bard
@render:react my_component(arg1=value1, arg2=value2)
```

**Your component receives:**

```jsx
{
  arg1: evaluatedValue1,
  arg2: evaluatedValue2
}
```

### Without React Hint (`@render`)

```bard
@render my_component(arg1=value1, arg2=value2)
```

**Your component receives:**

```jsx
{
  data: {
    arg1: evaluatedValue1,
    arg2: evaluatedValue2
  },
  name: "my_component"
}
```

**Recommendation:** Support both patterns:

```jsx
function MyComponent({ data, arg1, arg2, ...props }) {
  // Handle both patterns
  const actualArg1 = arg1 || data?.arg1
  const actualArg2 = arg2 || data?.arg2
  
  return <div>{actualArg1} - {actualArg2}</div>
}
```

---

## Examples

### Simple Display Component

```jsx
function AlertBox({ message, type = 'info' }) {
  const colors = {
    info: '#4a9eff',
    warning: '#ffb84d',
    error: '#ff6b6b',
    success: '#51cf66'
  }
  
  return (
    <div style={{
      padding: '20px',
      background: `${colors[type]}22`,
      border: `2px solid ${colors[type]}`,
      borderRadius: '8px',
      color: colors[type]
    }}>
      {message}
    </div>
  )
}
```

**Usage:**

```bard
@render alert_box(message="Watch out!", type="warning")
```

### Data Visualization Component

```jsx
function ProgressBar({ label, value, max = 100 }) {
  const percentage = (value / max) * 100
  
  return (
    <div style={{ margin: '20px 0' }}>
      <div style={{ marginBottom: '8px', color: '#a855f7' }}>
        {label}: {value} / {max}
      </div>
      <div style={{
        width: '100%',
        height: '30px',
        background: 'rgba(168, 85, 247, 0.2)',
        borderRadius: '15px',
        overflow: 'hidden'
      }}>
        <div style={{
          width: `${percentage}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #a855f7, #c084fc)',
          transition: 'width 0.5s ease'
        }} />
      </div>
    </div>
  )
}
```

**Usage:**

```bard
@render progress_bar(label="Health", value=health, max=100)
@render progress_bar(label="Trust", value=trust, max=50)
```

### Interactive Component

```jsx
import { useState } from 'react'

function DiceRoller({ num_dice = 1, sides = 6 }) {
  const [results, setResults] = useState([])
  
  const roll = () => {
    const newResults = Array.from(
      { length: num_dice },
      () => Math.floor(Math.random() * sides) + 1
    )
    setResults(newResults)
  }
  
  return (
    <div style={{
      padding: '30px',
      background: 'rgba(37, 37, 37, 0.8)',
      borderRadius: '12px',
      textAlign: 'center'
    }}>
      <button 
        onClick={roll}
        style={{
          padding: '15px 30px',
          background: 'linear-gradient(135deg, #a855f7, #9333ea)',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '1.1rem',
          cursor: 'pointer'
        }}
      >
        Roll {num_dice}d{sides}
      </button>
      
      {results.length > 0 && (
        <div style={{ 
          marginTop: '20px',
          fontSize: '2rem',
          color: '#a855f7'
        }}>
          {results.join(' + ')} = {results.reduce((a, b) => a + b, 0)}
        </div>
      )}
    </div>
  )
}
```

**Usage:**

```bard
@render dice_roller(num_dice=3, sides=6)
```

---

## Styling Tips

### Use Inline Styles

Since components are in isolated files, inline styles are easiest:

```jsx
const cardStyle = {
  padding: '20px',
  background: 'rgba(37, 37, 37, 0.8)',
  borderRadius: '12px',
  border: '1px solid rgba(168, 85, 247, 0.2)'
}

return <div style={cardStyle}>...</div>
```

### Match the Theme

Use colors from `App.css`:

- Primary: `#a855f7` (purple)
- Secondary: `#c084fc` (light purple)
- Background: `rgba(37, 37, 37, 0.8)`
- Text: `#e0e0e0`
- Error: `#ff6b6b`
- Success: `#51cf66`

### Responsive Design

```jsx
const isMobile = window.innerWidth < 768

const containerStyle = {
  padding: isMobile ? '15px' : '30px',
  fontSize: isMobile ? '0.9rem' : '1.1rem'
}
```

---

## Debugging

### Check Console Logs

The app logs directive data:

```javascript
console.log('Render directives:', data.render_directives)
```

### Use Default Component

If your component isn't showing, check:

1. Is it registered in `componentRegistry.js`?
2. Does the name match exactly? (case-sensitive)
3. Check browser console for errors

### Test with Simple Component

```jsx
function TestComponent(props) {
  return <pre>{JSON.stringify(props, null, 2)}</pre>
}
```

Register it and see exactly what props your component receives.

---

## Best Practices

### ✅ Do

- Handle missing/undefined props gracefully
- Provide default values for optional props
- Use TypeScript or PropTypes for type checking (optional)
- Keep components focused on presentation
- Use semantic HTML

### ❌ Don't

- Make API calls directly from components (use backend)
- Mutate game state (read-only from directives)
- Use external CSS files (hard to manage)
- Assume specific data structures without checking

---

## Testing Your Components

### Test Story

Create a test story in `stories/test/`:

```bard
:: TestMyComponent
~ test_value = 42

Testing my component:

@render my_component(value=test_value, label="Test")

+ [Continue] -> End

:: End
Done!
```

### Compile and Run

```bash
bardic compile stories/test/test_my_component.bard
bardic serve
```

---

## Examples in This Directory

- **`TarotCard.jsx`** - Single card display
- **`componentRegistry.js`** - Registry with CardSpread, CardDetail, InterpretationPanel examples

Study these for patterns and styling!
