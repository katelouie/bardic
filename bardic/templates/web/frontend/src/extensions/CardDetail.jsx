import TarotCard from './TarotCard'

/**
 * Single card detail view
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

export default CardDetail
