import TarotCard from './TarotCard'

/**
 * Simple card spread component
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

export default CardSpread
