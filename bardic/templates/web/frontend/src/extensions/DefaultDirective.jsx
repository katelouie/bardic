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

export default DefaultDirective
