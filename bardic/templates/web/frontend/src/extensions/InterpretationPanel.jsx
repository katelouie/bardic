/**
 * Interpretation panel
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

export default InterpretationPanel
