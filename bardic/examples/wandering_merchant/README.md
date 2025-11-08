# The Wandering Merchant

A trading sim teaching inventory management and economy systems.

## What This Teaches

- **Inventory management** with weight limits
- **Economy system** with buying/selling
- **Shop mechanics** with different prices per vendor
- **Dice rolls** for skill checks and combat
- **Branching paths** with consequence
- **Resource management** (gold vs. inventory space)

## How to Play

```bash
# Compile
bardic compile merchant.bard

# Play in terminal
bardic play merchant.json

# Or run with NiceGUI
python player.py merchant.json
```

## Modules Used

- `bardic.modules.inventory` - Weight-limited inventory system
- `bardic.modules.economy` - Wallet and shop mechanics
- `bardic.modules.dice` - Random events and skill checks

## Strategy Tips

- **Buy low, sell high**: Farmer sells cheap, noble/wizard buy expensive
- **Manage weight**: Don't fill your pack with junk
- **Fight or flight**: Bandit encounter has risks/rewards
- **Rest bonus**: Paying for tavern room = better capital prices
- **Seed profit**: Wheat Seeds cost 15g, wizard/noble pay 10-15g each

## Encounters

1. **Farmer** - Sells seeds/tools cheap (50% buyback)
2. **Bandit** - Pay toll, fight, or intimidate (dice roll)
3. **Wizard** - Rare goods, better buyback (70%)
4. **Noble** - Luxury items, 20% markup, decent buyback (60%)
5. **Tavern** - Rest for capital bonus (10g)
6. **Capital** - Final tally, best selling prices (80-90%)

## Example Run

Starting: 100g + 2 items (15g value) = **115g total**

Optimal path:

- Buy wheat seeds from farmer (15g each)
- Intimidate bandit (save 20g)
- Sell seeds to wizard (10.5g each @ 70%)
- Buy mana crystals from wizard
- Sell to capital market (90% rate)

Ending: **~200-250g** = 100g profit!
