/**
 * Component Registry for Custom Render Directives
 *
 * Register your custom React components here.
 * They'll be available via @ render directives in stories.
 */

// Import your custom components
// import TarotCard from '../components/TarotCard'
// import TarotSpread from '../components/TarotSpread'
// import ClientProfile from '../components/ClientProfile'

const componentRegistry = {
    // Register components by name
    // The name matches the @ render directive

    // Example:
    // 'render_tarot_card': TarotCard
    // 'render_spread': TarotSpread
    // 'render_client': ClientProfile

    // Default fallback component
    'default': ({ data }) => (
        <div style={{
            padding: '20px',
            background: 'rgba(255,255,255,0.1)',
            borderRadius: '8px',
            margin: '10px 0',
            fontFamily: 'monospace'
        }}>
            <div style={{ marginBottom: '10px', color: '#4a9eff', fontWeight: 'bold' }}>
                Render Directive (no component registered)
            </div>
            <pre style={{
                overflow: 'auto',
                fontSize: '0.9em',
                color: '#e0e0e0'
            }}>
                {JSON.stringify({ data, ...props }, null, 2)}
            </pre>
        </div>
    )
}

export default componentRegistry