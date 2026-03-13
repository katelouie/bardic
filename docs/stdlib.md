# Standard Library Reference

Bardic ships with five pre-built modules for common game mechanics. Import them in your `.bard` files and use them immediately — no extra installation needed.

```bard
from bardic.stdlib.dice import roll, skill_check, weighted_choice, advantage, disadvantage
from bardic.stdlib.inventory import Inventory
from bardic.stdlib.economy import Wallet, Shop
from bardic.stdlib.relationship import Relationship
from bardic.stdlib.quest import Quest, QuestJournal
```

All stdlib classes support **save/load** out of the box via `to_dict()` and `from_dict()` methods. Bardic's engine handles serialization automatically — you don't need to call these yourself unless you're building a custom save system.

---

## Dice

**`from bardic.stdlib.dice import roll, skill_check, weighted_choice, advantage, disadvantage`**

Dice rolling, skill checks, and weighted random choices. Uses standard tabletop notation.

### Usage

```bard
:: CombatRound
@py:
# Standard dice notation
damage = roll('2d6+3')      # 2 six-sided dice + 3
attack_roll = roll('1d20')   # Classic d20

# Skill check: stat + d20 >= difficulty class
passed = skill_check(player_dex, dc=15)

# Advantage/disadvantage (D&D 5e style)
lucky_roll = advantage()      # Roll 2d20, take higher
unlucky_roll = disadvantage() # Roll 2d20, take lower

# Weighted random outcomes
weather = weighted_choice(
    ['sunny', 'cloudy', 'rain', 'storm'],
    [0.4, 0.3, 0.2, 0.1]
)
@endpy

You roll to attack... **{attack_roll}!**

@if passed:
    Your blade strikes true for **{damage} damage!**
@else:
    Your swing goes wide.
@endif

Today's weather: {weather}

+ [Roll again] -> CombatRound
```

### API Reference

| Function | Description |
| -------- | ----------- |
| `roll(notation='1d6')` | Roll dice using standard notation: `'3d6'`, `'1d20+5'`, `'2d10-3'` |
| `skill_check(stat, dc, bonus=0)` | Roll 1d20 + stat + bonus, return `True` if >= dc |
| `weighted_choice(options, weights)` | Pick randomly from a list with given probabilities |
| `advantage()` | Roll 2d20, return the higher result |
| `disadvantage()` | Roll 2d20, return the lower result |

---

## Inventory

**`from bardic.stdlib.inventory import Inventory`**

Weight-limited item management with add, remove, search, and category filtering.

Items are dictionaries with at minimum a `name` key. Optional keys: `weight` (default 0), `value` (for economy integration), `category` (for filtering).

### Usage

```bard
:: Start
@py:
from bardic.stdlib.inventory import Inventory

inv = Inventory(max_weight=50)

# Add items as dicts
inv.add({'name': 'Iron Sword', 'weight': 5, 'value': 100, 'category': 'weapon'})
inv.add({'name': 'Healing Potion', 'weight': 0.5, 'value': 50, 'category': 'consumable'})
inv.add({'name': 'Healing Potion', 'weight': 0.5, 'value': 50, 'category': 'consumable'})
@endpy

**Your Bag** ({inv.current_weight}/{inv.max_weight} weight)

@for item in inv.items:
    - {item['name']} (weight: {item['weight']})
@endfor

Potions: {inv.count('Healing Potion')}
Total value: {inv.total_value} gold

+ {inv.has('Healing Potion')} [Drink a potion] -> DrinkPotion
+ [Continue] -> Next

:: DrinkPotion
@py:
inv.remove('Healing Potion')
@endpy

You drink the potion. {inv.count('Healing Potion')} remaining.

+ [Continue] -> Next
```

### API Reference

| Method / Property | Description |
| ----------------- | ----------- |
| `Inventory(max_weight=100)` | Create inventory with weight limit |
| `.add(item) -> bool` | Add item dict. Returns `False` if over weight limit |
| `.remove(name) -> bool` | Remove first matching item. Returns `False` if not found |
| `.remove_all(name) -> int` | Remove all matching items. Returns count removed |
| `.has(name) -> bool` | Check if item exists |
| `.count(name) -> int` | Count matching items |
| `.get(name) -> dict\|None` | Get first matching item without removing |
| `.get_all(name) -> list` | Get all matching items |
| `.filter_by_category(cat) -> list` | Get all items in a category |
| `.clear()` | Remove all items |
| `.items` | The raw list of item dicts |
| `.current_weight` | Total weight of all items |
| `.max_weight` | Weight capacity |
| `.space_remaining` | Weight capacity left |
| `.is_full` | `True` if at max weight |
| `.is_empty` | `True` if no items |
| `.total_value` | Sum of all item `value` fields |

---

## Economy

**`from bardic.stdlib.economy import Wallet, Shop`**

Currency management and shop transactions. Integrates with `Inventory` for buying and selling.

### Usage

```bard
:: Start
@py:
from bardic.stdlib.inventory import Inventory
from bardic.stdlib.economy import Wallet, Shop

wallet = Wallet(gold=200)
inv = Inventory(max_weight=50)

# Create a shop with items for sale
shop = Shop([
    {'name': 'Steel Sword', 'weight': 5, 'value': 150, 'category': 'weapon'},
    {'name': 'Leather Armor', 'weight': 8, 'value': 120, 'category': 'armor'},
    {'name': 'Health Potion', 'weight': 0.5, 'value': 25, 'category': 'consumable'},
], sell_back_rate=0.5)  # Shop buys items at 50% value
@endpy

Welcome to the shop! You have **{wallet.gold} gold**.

**For Sale:**
@for item in shop.items:
    - {item['name']} — {item['value']} gold
@endfor

+ {wallet.can_afford(150)} [Buy Steel Sword (150g)] -> BuySword
+ {wallet.can_afford(120)} [Buy Leather Armor (120g)] -> BuyArmor
+ {wallet.can_afford(25)} [Buy Health Potion (25g)] -> BuyPotion
+ [Leave] -> Road

:: BuySword
@py:
success = shop.buy('Steel Sword', wallet, inv)
@endpy

@if success:
    You bought the Steel Sword! **{wallet.gold} gold** remaining.
@else:
    Purchase failed — your bag might be too heavy.
@endif

+ [Back to shop] -> Start

:: SellItem
@py:
# Sell an item back at 50% value
sold = shop.sell('Health Potion', wallet, inv)
@endpy

@if sold:
    Sold! You now have **{wallet.gold} gold**.
@else:
    You don't have that item.
@endif

+ [Back to shop] -> Start
```

### Wallet API

| Method / Property | Description |
| ----------------- | ----------- |
| `Wallet(gold=0)` | Create wallet with starting gold |
| `.gold` | Current gold (read/write, clamped to minimum 0) |
| `.can_afford(price) -> bool` | Check if gold >= price |
| `.spend(amount) -> bool` | Deduct gold. Returns `False` if insufficient |
| `.earn(amount)` | Add gold (negative amounts ignored) |

### Shop API

| Method / Property | Description |
| ----------------- | ----------- |
| `Shop(items, sell_back_rate=0.5, discount=1.0)` | Create shop with item list |
| `.buy(name, wallet, inventory) -> bool` | Buy item: deducts gold, adds to inventory. Auto-refunds if bag is full |
| `.sell(name, wallet, inventory) -> bool` | Sell item: removes from inventory, adds gold at sell_back_rate |
| `.find_item(name) -> dict\|None` | Look up item in shop stock |
| `.get_buy_price(name) -> int` | Price with discount applied |
| `.get_sell_price(value) -> int` | What shop pays (value × sell_back_rate) |
| `.set_discount(rate)` | Change price multiplier (0.8 = 20% off) |
| `.items` | The shop's item list |

---

## Relationship

**`from bardic.stdlib.relationship import Relationship`**

Track NPC relationships across three dimensions: **trust** (0–100), **comfort** (0–100), and **openness** (−10 to +10). Includes threshold events, topic tracking, and computed relationship quality.

### Usage

```bard
:: Start
@py:
from bardic.stdlib.relationship import Relationship

alex = Relationship(name="Alex", trust=40, comfort=50, openness=0)
@endpy

You sit down across from {alex.name}.
Relationship: **{alex.relationship_quality}** (trust: {alex.trust})

+ [Share something personal] -> SharePersonal
+ [Keep it surface-level] -> SmallTalk
+ [Ask about their past] -> AskPast

:: SharePersonal
@py:
alex.add_trust(15)
alex.add_openness(2)
alex.discuss_topic("vulnerability")
@endpy

Alex looks surprised, then softens. "Thank you for telling me that."

Trust: {alex.trust} | Openness: {alex.openness}

@if alex.is_ready_for_deep_conversation:
    Alex seems ready to open up about something deeper.
    + [Ask what's on their mind] -> DeepTalk
@endif

+ [Continue] -> Next

:: SmallTalk
@py:
alex.add_comfort(5)
@endpy

You chat about the weather. It's nice, but not exactly riveting.

+ [Continue] -> Next

:: DeepTalk
@py:
alex.add_trust(10)
alex.add_openness(3)
alex.discuss_topic("family")
@endpy

@if alex.has_discussed("vulnerability"):
    "Since you were honest with me... I want to tell you about my family."
@endif

+ [Listen] -> Next
```

### API Reference

| Method / Property | Description |
| ----------------- | ----------- |
| `Relationship(name, trust, comfort, openness, topics_discussed=None)` | Create NPC relationship |
| `.trust` | 0–100, auto-clamped |
| `.comfort` | 0–100, auto-clamped |
| `.openness` | −10 to +10, auto-clamped |
| `.add_trust(amount)` | Adjust trust (triggers threshold events at 60 and 80) |
| `.add_comfort(amount)` | Adjust comfort |
| `.add_openness(amount)` | Adjust openness |
| `.discuss_topic(topic)` | Mark a topic as discussed |
| `.has_discussed(topic) -> bool` | Check if topic was covered |
| `.relationship_quality -> str` | One of: `"guarded"`, `"cautious"`, `"professional"`, `"trusted_guide"`, `"close_confidant"` |
| `.is_ready_for_deep_conversation -> bool` | Trust ≥ 60 and openness ≥ 1 |
| `.is_defensive -> bool` | Openness ≤ −3 |
| `.is_vulnerable -> bool` | Openness ≥ 5 |
| `.topics_discussed` | Set of topic strings |

### Trust Thresholds

The `add_trust()` method automatically calls threshold hooks when trust crosses certain levels:

| Threshold | Method Called | Meaning |
| --------- | ----------- | ------- |
| Trust reaches 60 | `on_trust_threshold_60()` | NPC begins to open up |
| Trust reaches 80 | `on_trust_threshold_80()` | NPC trusts you deeply |

Override these methods in a subclass to add custom behavior (e.g., unlocking new dialogue).

---

## Quest

**`from bardic.stdlib.quest import Quest, QuestJournal`**

Quest tracking with custom stages, journal entries, and filtered views. `QuestJournal` is the main interface; `Quest` is the individual quest object.

### Usage

```bard
:: Start
@py:
from bardic.stdlib.quest import QuestJournal

journal = QuestJournal()

# Add a quest
journal.add("find_key", "Find the Brass Key",
            description="The librarian lost her key somewhere in the garden.")

# Log a narrative breadcrumb
journal.log("find_key", "The librarian mentioned she was last in the garden.")
@endpy

**Quest Added:** {journal.get("find_key").title}

Active quests: {journal.count_active}

+ [Search the garden] -> Garden

:: Garden
@py:
journal.set_stage("find_key", "searched_garden")
journal.log("find_key", "Found scratch marks near the fountain.")
@endpy

You notice scratch marks near the fountain...

+ [Look closer] -> FoundKey
+ [Search elsewhere] -> Greenhouse

:: FoundKey
@py:
journal.log("find_key", "Found the key hidden under a loose stone!")
journal.complete("find_key")
@endpy

You found the brass key!

@if journal.is_complete("find_key"):
    **Quest Complete:** {journal.get("find_key").title}
@endif

**Journal Entries:**
@for entry in journal.get_log("find_key"):
    - {entry}
@endfor

+ [Return to the library] -> Library
```

### QuestJournal API

| Method / Property | Description |
| ----------------- | ----------- |
| `QuestJournal()` | Create an empty journal |
| `.add(quest_id, title, description='', stage='active') -> Quest` | Add a new quest |
| `.get(quest_id) -> Quest\|None` | Get quest by ID |
| `.has(quest_id) -> bool` | Check if quest exists |
| `.is_active(quest_id) -> bool` | Quest is in progress |
| `.is_complete(quest_id) -> bool` | Quest is finished |
| `.is_failed(quest_id) -> bool` | Quest has failed |
| `.stage_of(quest_id) -> str\|None` | Get current stage string |
| `.set_stage(quest_id, stage)` | Set quest to any custom stage |
| `.complete(quest_id)` | Mark quest as complete |
| `.fail(quest_id)` | Mark quest as failed |
| `.log(quest_id, entry)` | Add a journal entry |
| `.get_log(quest_id) -> list[str]` | Get all journal entries in order |
| `.active_quests -> list[Quest]` | All in-progress quests |
| `.completed_quests -> list[Quest]` | All finished quests |
| `.failed_quests -> list[Quest]` | All failed quests |
| `.all_quests -> list[Quest]` | Every quest in the journal |
| `.count_active -> int` | Number of active quests |
| `.count_complete -> int` | Number of completed quests |

### Quest Object

| Field / Property | Description |
| --------------- | ----------- |
| `.quest_id` | Unique identifier |
| `.title` | Display name |
| `.description` | Longer description text |
| `.stage` | Current stage string |
| `.log` | List of journal entries |
| `.is_active -> bool` | Not complete or failed |
| `.is_complete -> bool` | Stage is `"complete"` |
| `.is_failed -> bool` | Stage is `"failed"` |

### Custom Stages

Stages can be any string — use them to track quest progression:

```bard
@py:
journal.set_stage("mystery", "found_clue")
journal.set_stage("mystery", "interrogated_suspect")
journal.set_stage("mystery", "confronted_villain")
journal.complete("mystery")
@endpy

@if journal.stage_of("mystery") == "found_clue":
    You have a lead...
@elif journal.stage_of("mystery") == "interrogated_suspect":
    The suspect was nervous. You're getting closer.
@endif
```

---

## Save/Load

All stdlib classes serialize automatically with Bardic's save system. If you're building a custom save/load solution, each class provides:

| Method | Description |
|--------|-------------|
| `.to_dict() -> dict` | Serialize to a plain dict (JSON-safe) |
| `ClassName.from_dict(data) -> instance` | Reconstruct from saved dict |

```python
# Manual serialization (usually not needed — the engine handles this)
saved = inv.to_dict()       # {'items': [...], 'max_weight': 50}
loaded = Inventory.from_dict(saved)
```

---

## Combining Modules

The stdlib modules are designed to work together. Here's a pattern for a complete game system:

```bard
:: GameSetup
@py:
from bardic.stdlib.inventory import Inventory
from bardic.stdlib.economy import Wallet, Shop
from bardic.stdlib.quest import QuestJournal
from bardic.stdlib.relationship import Relationship
from bardic.stdlib.dice import roll, skill_check

# Player systems
inv = Inventory(max_weight=40)
wallet = Wallet(gold=100)
journal = QuestJournal()

# NPCs
merchant = Relationship(name="Merchant Greta", trust=30, comfort=40, openness=-2)

# Shop
shop = Shop([
    {'name': 'Rope', 'weight': 3, 'value': 10},
    {'name': 'Lantern', 'weight': 2, 'value': 25},
    {'name': 'Lockpick', 'weight': 0.1, 'value': 50},
])

# Quest
journal.add("explore_ruins", "Explore the Old Ruins",
            description="Greta mentioned something valuable in the ruins north of town.")
@endpy

+ [Visit Greta's shop] -> Shop
+ [Head to the ruins] -> Ruins

:: Shop
@if merchant.relationship_quality == "guarded":
    Greta eyes you suspiciously. "What do you want?"
@elif merchant.relationship_quality == "professional":
    "Welcome back. Looking to buy?"
@else:
    Greta smiles warmly. "Good to see you, friend. I set aside something special."
    @py:
    shop.set_discount(0.8)  # 20% off for trusted customers
    @endpy
@endif

+ [Browse wares] -> BrowseShop
+ [Chat with Greta] -> ChatGreta
+ [Leave] -> Town

:: Ruins
@py:
check = skill_check(10, dc=12)  # Generic perception check
@endpy

@if check:
    You spot a hidden passage behind the rubble.
    @py:
    journal.log("explore_ruins", "Found a hidden passage in the ruins.")
    @endpy
    + [Enter the passage] -> HiddenRoom
@else:
    The ruins seem empty. Maybe you missed something.
@endif

+ [Search again] -> Ruins
+ [Return to town] -> Town
```
