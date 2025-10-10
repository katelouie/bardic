/**
 * Example custom component for rendering tarot cards.
 *
 * Usage in story:
 *   @ render_tarot_card(card, position='center')
 */
function TarotCard({ card, position = "center", size = "medium" }) {
    const sizeClasses = {
        small: "w-32 h-48",
        medium: 'w-48 h-72',
        large: 'w-64 h-96'
    }

    return (
        <div className={`tarot-card ${sizeClasses[size]}`}>
            <div className={`card-inner ${card.reversed ? 'reversed' : ''}`}>
                <div className="card-front">
                    <h3>{card.name}</h3>
                    {card.reversed && <span className="reversed-indicator">↓</span>}
                    <p className="position">{position}</p>
                    <p className="suit">{card.suit}</p>
                </div>
            </div>
        </div>
    )
}

export default TarotCard