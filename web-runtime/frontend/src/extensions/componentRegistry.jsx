/**
 * Component Registry for Custom Render Directives
 *
 * Register your custom React components here.
 * They'll be available via @render directives in stories.
 */

import TarotCard from './TarotCard'

/**
 * Default component shown when no specific component is registered
 * Shows the raw data in a debug-friendly format
 */
function DefaultDirective({ data, name, ...props }) {
  return (
    <div style={{
      padding: '20px',
      background: 'rgba(168, 85, 247, 0.1)',
      border: '2px solid rgba(168, 85, 247, 0.3)',
      borderRadius: '12px',
      margin: '20px 0',
      fontFamily: 'monospace'
    }}>
      <div style={{ 
        marginBottom: '15px', 
        color: '#a855f7', 
        fontWeight: 'bold',
        fontSize: '1.1rem'
      }}>
        🎨 Render Directive: {name}
      </div>
      <div style={{ 
        marginBottom: '10px',
        color: '#888',
        fontSize: '0.9rem'
      }}>
        (No component registered - showing raw data)
      </div>
      <pre style={{
        overflow: 'auto',
        fontSize: '0.85rem',
        color: '#e0e0e0',
        background: 'rgba(0,0,0,0.3)',
        padding: '15px',
        borderRadius: '8px',
        maxHeight: '400px'
      }}>
        {JSON.stringify({ name, data, ...props }, null, 2)}
      </pre>
    </div>
  )
}

/**
 * Example: Simple card spread component
 * Shows multiple tarot cards in a row
 */
function CardSpread({ cards, layout = 'simple', ...props }) {
  return (
    <div style={{
      padding: '30px',
      background: 'rgba(37, 37, 37, 0.8)',
      borderRadius: '16px',
      margin: '20px 0',
      border: '1px solid rgba(168, 85, 247, 0.2)'
    }}>
      <h3 style={{ 
        color: '#a855f7', 
        marginBottom: '20px',
        textAlign: 'center'
      }}>
        Card Spread ({layout})
      </h3>
      <div style={{
        display: 'flex',
        gap: '20px',
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        {cards && cards.map((card, i) => (
          <TarotCard key={i} card={card} size="medium" />
        ))}
      </div>
    </div>
  )
}

/**
 * Example: Single card detail view
 * Shows one card with extra information
 */
function CardDetail({ card, position, ...props }) {
  return (
    <div style={{
      padding: '25px',
      background: 'rgba(37, 37, 37, 0.8)',
      borderRadius: '12px',
      margin: '15px 0',
      border: '1px solid rgba(168, 85, 247, 0.2)',
      display: 'flex',
      gap: '20px',
      alignItems: 'center'
    }}>
      <TarotCard card={card} size="small" />
      <div style={{ flex: 1 }}>
        <h4 style={{ color: '#a855f7', marginBottom: '10px' }}>
          {card.name}
        </h4>
        {position && (
          <p style={{ color: '#c084fc', marginBottom: '5px' }}>
            Position: {position}
          </p>
        )}
        {card.is_reversed && (
          <p style={{ color: '#ff6b6b', fontSize: '0.9rem' }}>
            ↓ Reversed
          </p>
        )}
      </div>
    </div>
  )
}

/**
 * Example: Interpretation panel
 * Shows reading interpretation with styling
 */
function InterpretationPanel({ interpretation, confidence, style = 'traditional', ...props }) {
  return (
    <div style={{
      padding: '30px',
      background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%)',
      borderRadius: '16px',
      margin: '20px 0',
      border: '2px solid rgba(168, 85, 247, 0.3)'
    }}>
      <h3 style={{ 
        color: '#a855f7', 
        marginBottom: '15px',
        fontSize: '1.3rem'
      }}>
        ✨ Interpretation ({style})
      </h3>
      {confidence && (
        <div style={{ 
          marginBottom: '15px',
          color: '#c084fc',
          fontSize: '0.9rem'
        }}>
          Confidence: {(confidence * 100).toFixed(0)}%
        </div>
      )}
      <div style={{ 
        color: '#e0e0e0',
        lineHeight: '1.6',
        fontSize: '1.05rem'
      }}>
        {typeof interpretation === 'string' ? interpretation : JSON.stringify(interpretation, null, 2)}
      </div>
    </div>
  )
}

/**
 * Component Registry
 * 
 * Map directive names to React components
 * The key should match the name used in @render directives
 */
const componentRegistry = {
  // Tarot-specific components
  'card_spread': CardSpread,
  'render_spread': CardSpread,  // Alias
  'CardSpread': CardSpread,     // PascalCase version (from React hint)
  
  'card_detail': CardDetail,
  'render_card_detail': CardDetail,  // Alias
  'CardDetail': CardDetail,     // PascalCase version
  
  'tarot_card': TarotCard,
  'render_tarot_card': TarotCard,  // Alias
  'TarotCard': TarotCard,      // PascalCase version
  
  'interpretation_panel': InterpretationPanel,
  'render_interpretation': InterpretationPanel,  // Alias
  'InterpretationPanel': InterpretationPanel,  // PascalCase version

  // Add your custom components here:
  // 'my_component': MyComponent,
  // 'render_my_thing': MyThingComponent,

  // Default fallback (required)
  'default': DefaultDirective
}

export default componentRegistry
