/**
 * TarotCard Component
 * 
 * Displays a single tarot card with styling
 * 
 * Usage in story:
 *   @render tarot_card(card, size='medium')
 *   @render:react tarot_card(card, position='past')
 */
function TarotCard({ card, position, size = 'medium' }) {
  if (!card) {
    return (
      <div style={{ 
        padding: '20px', 
        color: '#ff6b6b',
        background: 'rgba(255, 107, 107, 0.1)',
        borderRadius: '8px'
      }}>
        Error: No card data provided
      </div>
    )
  }

  // Size configurations
  const sizeStyles = {
    small: { width: '120px', height: '180px', fontSize: '0.8rem' },
    medium: { width: '160px', height: '240px', fontSize: '0.9rem' },
    large: { width: '200px', height: '300px', fontSize: '1rem' }
  }

  const currentSize = sizeStyles[size] || sizeStyles.medium

  // Card styling
  const cardStyle = {
    width: currentSize.width,
    height: currentSize.height,
    background: 'linear-gradient(135deg, #2d2d44 0%, #1a1a2e 100%)',
    border: '2px solid #a855f7',
    borderRadius: '12px',
    padding: '15px',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    alignItems: 'center',
    boxShadow: '0 8px 16px rgba(0, 0, 0, 0.4)',
    transition: 'transform 0.3s ease, box-shadow 0.3s ease',
    cursor: 'pointer',
    fontSize: currentSize.fontSize,
    transform: card.is_reversed ? 'rotate(180deg)' : 'none',
    position: 'relative'
  }

  const cardHoverStyle = {
    ':hover': {
      transform: card.is_reversed ? 'rotate(180deg) translateY(-5px)' : 'translateY(-5px)',
      boxShadow: '0 12px 24px rgba(168, 85, 247, 0.4)'
    }
  }

  const nameStyle = {
    color: '#a855f7',
    fontWeight: 'bold',
    fontSize: '1em',
    textAlign: 'center',
    marginBottom: '10px',
    transform: card.is_reversed ? 'rotate(180deg)' : 'none'
  }

  const numberStyle = {
    color: '#c084fc',
    fontSize: '2em',
    fontWeight: 'bold',
    margin: '10px 0'
  }

  const infoStyle = {
    color: '#d8b4fe',
    fontSize: '0.85em',
    textAlign: 'center',
    transform: card.is_reversed ? 'rotate(180deg)' : 'none'
  }

  const reversedBadgeStyle = {
    position: 'absolute',
    top: '10px',
    right: '10px',
    background: 'rgba(255, 107, 107, 0.2)',
    color: '#ff6b6b',
    padding: '3px 8px',
    borderRadius: '4px',
    fontSize: '0.75em',
    fontWeight: 'bold',
    transform: card.is_reversed ? 'rotate(180deg)' : 'none'
  }

  return (
    <div 
      style={cardStyle}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = card.is_reversed 
          ? 'rotate(180deg) translateY(-5px)' 
          : 'translateY(-5px)'
        e.currentTarget.style.boxShadow = '0 12px 24px rgba(168, 85, 247, 0.4)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = card.is_reversed 
          ? 'rotate(180deg)' 
          : 'none'
        e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.4)'
      }}
    >
      {/* Reversed indicator badge */}
      {card.is_reversed && (
        <div style={reversedBadgeStyle}>
          REVERSED
        </div>
      )}

      {/* Card name */}
      <div style={nameStyle}>
        {card.name || 'Unknown Card'}
      </div>

      {/* Card number (if available) */}
      {card.number !== undefined && (
        <div style={numberStyle}>
          {card.number}
        </div>
      )}

      {/* Position (if provided) */}
      {position && (
        <div style={infoStyle}>
          {position}
        </div>
      )}

      {/* Suit (if available) */}
      {card.suit && (
        <div style={infoStyle}>
          {card.suit}
        </div>
      )}
    </div>
  )
}

export default TarotCard
