/**
 * Component Registry for Custom Render Directives
 *
 * Register your custom React components here.
 * They'll be available via @render directives in stories.
 */

import TarotCard from './TarotCard'
import DefaultDirective from './DefaultDirective'
import CardSpread from './CardSpread'
import CardDetail from './CardDetail'
import InterpretationPanel from './InterpretationPanel'

/**
 * Component Registry
 *
 * Map directive names to React components.
 * The key should match the name used in @render directives in your .bard files.
 *
 * Example usage in .bard file:
 *   @render:react card_spread(cards=my_cards, layout='three_card')
 *
 * This will look up 'card_spread' in the registry and render the CardSpread component.
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
