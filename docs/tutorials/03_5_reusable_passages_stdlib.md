# Part 3C: Reusable Passages & The Standard Library

Welcome back! In Part 3B, you learned how to create custom objects with their own data and methods. You built an `Item` class that could describe itself and check if it was heavy.

But there's a problem we haven't solved yet: **what if you want to reuse the same logic in multiple places?**

Imagine you're building a merchant game with 5 different vendors. Do you really want to write 5 separate "Buy Item" passages that all do basically the same thing? That's a lot of copy-paste!

In this tutorial, we'll learn how to write **reusable passages** using **passage parameters**, and we'll explore Bardic's **standard library modules** that give you pre-built systems for common game mechanics.

**By the end of this tutorial, you will know how to:**

- Pass data into passages using **passage parameters**
- Write **generic handler passages** that work with any data
- Import and use **Bardic's standard library modules** (inventory, economy, dice)
- Build a complete **merchant trading game** with shops and currency

---

## 1. The Problem: Repetitive Passages

Let's say you're building a simple shop. Without passage parameters, you'd write something like this:

```bard
:: Shop
+ [Buy Sword (100g)] -> Buy_Sword
+ [Buy Potion (50g)] -> Buy_Potion
+ [Buy Shield (75g)] -> Buy_Shield

:: Buy_Sword
@py:
if player_gold >= 100:
    player_gold -= 100
    inventory.append("Sword")
    success = True
else:
    success = False
@endpy

@if success:
    You bought a sword!
@else:
    Not enough gold!
@endif

+ [Back] -> Shop

:: Buy_Potion
@py:
if player_gold >= 50:
    player_gold -= 50
    inventory.append("Potion")
    success = True
else:
    success = False
@endpy

@if success:
    You bought a potion!
@else:
    Not enough gold!
@endif

+ [Back] -> Shop

:: Buy_Shield
# ... you get the idea - more copy-paste!
```

**See the problem?** The logic is identical—only the item name and price change. We're writing the same code over and over.

---

## 2. The Solution: Passage Parameters

**Passage parameters** let you pass data INTO a passage, making it reusable. Here's the syntax:

```bard
:: PassageName(parameter1, parameter2)
Content using {parameter1} and {parameter2}
```

Let's rewrite our shop example:

```bard
:: Shop
~ player_gold = 200

You have {player_gold} gold.

+ [Buy Sword (100g)] -> BuyItem(item_name="Sword", price=100)
+ [Buy Potion (50g)] -> BuyItem(item_name="Potion", price=50)
+ [Buy Shield (75g)] -> BuyItem(item_name="Shield", price=75)

:: BuyItem(item_name, price)
@py:
if player_gold >= price:
    player_gold -= price
    inventory.append(item_name)
    success = True
else:
    success = False
@endpy

@if success:
    You bought a **{item_name}** for {price} gold!

    Gold remaining: {player_gold}
@else:
    You need {price} gold but only have {player_gold}!
@endif

+ [Back to shop] -> Shop
```

**What changed?**

1. **Choices pass arguments:** `-> BuyItem(item_name="Sword", price=100)`
2. **Passage accepts parameters:** `:: BuyItem(item_name, price)`
3. **Parameters are available as variables:** `{item_name}`, `{price}`
4. **ONE passage handles ALL items!**

---

## 3. Parameters Can Be Variables

You can pass variables (not just literal values) to passages:

```bard
:: Shop
~ sword_price = 100
~ potion_price = 50

+ [Buy Sword] -> BuyItem(item_name="Sword", price=sword_price)
+ [Buy Potion] -> BuyItem(item_name="Potion", price=potion_price)

:: BuyItem(item_name, price)
You bought {item_name} for {price} gold!
```

You can even pass **expressions**:

```bard
+ [Buy Discounted Sword] -> BuyItem(item_name="Sword", price=sword_price * 0.8)
```

---

## 4. Parameters Can Be Objects

Here's where it gets powerful. Remember the `Item` class from Part 3B? You can pass entire objects:

```bard
from item import Item

:: Shop
~ sword = Item("Iron Sword", "A basic weapon", 5.0)
~ potion = Item("Health Potion", "Restores 50 HP", 0.5)

+ [Examine Sword] -> ExamineItem(item=sword)
+ [Examine Potion] -> ExamineItem(item=potion)

:: ExamineItem(item)
**{item.name}**

{item.description}

Weight: {item.weight} lbs

@if item.is_heavy():
    This is a heavy item!
@endif

+ [Back] -> Shop
```

**ONE examine passage works for ANY item!**

---

## 5. Default Parameter Values

You can provide default values for parameters:

```bard
:: BuyItem(item_name, price, discount=0)
@py:
final_price = price * (1 - discount)
@endpy

@if player_gold >= final_price:
    You bought {item_name} for {final_price} gold!
@else:
    Not enough gold!
@endif

+ [Back] -> Shop
```

Now you can call it with or without a discount:

```bard
+ [Buy Sword] -> BuyItem(item_name="Sword", price=100)
+ [Buy Discounted Sword] -> BuyItem(item_name="Sword", price=100, discount=0.2)
```

---

## 6. Introducing Bardic's Standard Library

Now that you understand passage parameters, you're ready for something even more powerful: **Bardic's standard library modules**.

These are pre-built Python modules that handle common game mechanics so you don't have to write them from scratch.

### Available Modules

**`bardic.modules.inventory`** - Item management with weight limits
**`bardic.modules.economy`** - Currency, shops, buying/selling
**`bardic.modules.dice`** - Dice rolls and skill checks
**`bardic.modules.relationship`** - NPC relationship tracking

Here's also the [`stdlib` directory](../../bardic/stdlib/) so you can see the code for all of the modules.

Let's learn how to use them!

---

## 7. The Inventory Module

The inventory module gives you a weight-limited container for items:

```bard
from bardic.modules.inventory import Inventory

:: Start
~ player_inventory = Inventory(max_weight=50)

You have an empty pack that can carry 50 lbs.

+ [Find some items] -> FindItems

:: FindItems
@py:
# Items are simple dictionaries
sword = {'name': 'Iron Sword', 'weight': 5, 'value': 100}
potion = {'name': 'Health Potion', 'weight': 0.5, 'value': 50}

# Try to add them
sword_added = player_inventory.add(sword)
potion_added = player_inventory.add(potion)
@endpy

@if sword_added:
    You picked up an Iron Sword!
@endif

@if potion_added:
    You picked up a Health Potion!
@endif

+ [Check inventory] -> CheckInventory

:: CheckInventory
**Your Inventory:**

@if not player_inventory.is_empty:
    @for item in player_inventory.items:
        - {item['name']} ({item['weight']} lbs, worth {item['value']}g)
    @endfor

    **Total weight:** {player_inventory.current_weight}/{player_inventory.max_weight} lbs
@else:
    Your inventory is empty.
@endif

+ [Continue] -> Start
```

**Key Inventory Methods:**

- `inventory.add(item)` - Add an item (returns True/False)
- `inventory.remove(item_name)` - Remove first matching item
- `inventory.has(item_name)` - Check if item exists
- `inventory.count(item_name)` - Count how many of an item
- `inventory.is_full` - Check if at weight limit
- `inventory.current_weight` - Get total weight

---

## 8. The Economy Module

The economy module gives you currency and shops:

```bard
from bardic.modules.economy import Wallet, Shop
from bardic.modules.inventory import Inventory

:: Start
~ player_wallet = Wallet(gold=100)
~ player_inventory = Inventory(max_weight=50)

You have {player_wallet.gold} gold.

+ [Visit the shop] -> ShopMain

:: ShopMain
@py:
# Create a shop with items for sale
shop_items = [
    {'name': 'Iron Sword', 'weight': 5, 'value': 100},
    {'name': 'Health Potion', 'weight': 0.5, 'value': 50},
    {'name': 'Leather Armor', 'weight': 8, 'value': 150}
]
weapon_shop = Shop(shop_items)
@endpy

**Weapon Shop**

Gold: {player_wallet.gold}
Pack: {player_inventory.current_weight}/{player_inventory.max_weight} lbs

+ [Buy Iron Sword (100g)] -> BuyFromShop(item_name="Iron Sword", shop=weapon_shop)
+ [Buy Health Potion (50g)] -> BuyFromShop(item_name="Health Potion", shop=weapon_shop)
+ [Buy Leather Armor (150g)] -> BuyFromShop(item_name="Leather Armor", shop=weapon_shop)
+ [Leave] -> Start

:: BuyFromShop(item_name, shop)
@py:
# The shop handles the entire transaction!
success = shop.buy(item_name, player_wallet, player_inventory)
price = shop.get_buy_price(item_name)
@endpy

@if success:
    You bought **{item_name}** for {price}g!

    Gold: {player_wallet.gold}
@else:
    @py:
    # Figure out why it failed
    if not player_wallet.can_afford(price):
        reason = "not enough gold"
    elif player_inventory.is_full:
        reason = "your pack is too full"
    else:
        reason = "unknown reason"
    @endpy

    Can't buy {item_name} - {reason}!
@endif

+ [Back to shop] -> ShopMain
```

**Key Economy Classes:**

**Wallet:**

- `wallet.gold` - Current gold amount
- `wallet.can_afford(price)` - Check if you can afford something
- `wallet.spend(amount)` - Deduct gold (returns True/False)
- `wallet.earn(amount)` - Add gold

**Shop:**

- `shop.buy(item_name, wallet, inventory)` - Handle purchase transaction
- `shop.sell(item_name, wallet, inventory)` - Sell item back to shop
- `shop.get_buy_price(item_name)` - Get purchase price
- `shop.get_sell_price(item_value)` - Get sell-back price

---

## 9. The Dice Module

The dice module gives you randomness and skill checks:

```bard
from bardic.modules.dice import roll, skill_check

:: Start
You encounter a locked door.

+ [Try to pick the lock] -> PickLock
+ [Bash it down] -> BashDoor

:: PickLock
@py:
# Roll 1d20 + dexterity
player_dex = 14
result = roll('1d20') + player_dex
difficulty = 18
@endpy

You rolled **{result}** (need {difficulty})

@if result >= difficulty:
    **Success!** You pick the lock!
    + [Enter] -> NextRoom
@else:
    **Failure!** The lock holds firm.
    + [Try again] -> PickLock
    + [Try bashing instead] -> BashDoor
@endif

:: BashDoor
@py:
# Use skill_check helper
player_strength = 16
success = skill_check(player_strength, dc=15)
@endpy

@if success:
    **CRASH!** The door splinters open!
    + [Enter] -> NextRoom
@else:
    You bounce off the door. Ouch!
    + [Try again] -> BashDoor
@endif

:: NextRoom
You're through the door!
```

**Key Dice Functions:**

- `roll('1d6')` - Roll dice (supports '3d6+5', '2d10-2', etc.)
- `skill_check(stat, dc)` - Make a d20 check against difficulty
- `weighted_choice(options, weights)` - Random choice with probabilities

---

## 10. Combining It All: A Real Merchant Game

Let's put everything together. Here's a complete merchant trading game that uses:

- Passage parameters for reusable handlers
- Inventory module for item management
- Economy module for shops and currency
- Dice module for random events

Create **`merchant_game.bard`**:

```bard
from bardic.modules.inventory import Inventory
from bardic.modules.economy import Wallet, Shop
from bardic.modules.dice import roll

:: Start
~ player_inventory = Inventory(max_weight=50)
~ player_wallet = Wallet(gold=100)

# Add starting items
@py:
player_inventory.add({'name': 'Travel Rations', 'weight': 2, 'value': 10})
player_inventory.add({'name': 'Waterskin', 'weight': 1, 'value': 5})
@endpy

**THE WANDERING MERCHANT**

You're a traveling merchant heading to the capital.
Goal: Buy low, sell high!

**Starting Status:**
- Gold: {player_wallet.gold}g
- Items: {len(player_inventory.items)}
- Weight: {player_inventory.current_weight}/{player_inventory.max_weight} lbs

+ [Begin your journey] -> Encounter1

:: Encounter1

**Encounter 1: The Farmer**

A farmer sits by his roadside stall.

"Got seeds and tools for sale!"

@py:
# Create the farmer's shop
farmer_items = [
    {'name': 'Wheat Seeds', 'weight': 0.5, 'value': 15},
    {'name': 'Carrot Seeds', 'weight': 0.3, 'value': 12},
    {'name': 'Iron Hoe', 'weight': 3, 'value': 35}
]
farmer_shop = Shop(farmer_items, sell_back_rate=0.5)

# Pre-calculate what we can buy
wheat_price = farmer_shop.get_buy_price('Wheat Seeds')
carrot_price = farmer_shop.get_buy_price('Carrot Seeds')
hoe_price = farmer_shop.get_buy_price('Iron Hoe')

can_buy_wheat = player_wallet.can_afford(wheat_price) and not player_inventory.is_full
can_buy_carrot = player_wallet.can_afford(carrot_price) and not player_inventory.is_full
can_buy_hoe = player_wallet.can_afford(hoe_price) and not player_inventory.is_full
@endpy

**Your Status:**
Gold: {player_wallet.gold}g | Weight: {player_inventory.current_weight}/{player_inventory.max_weight}

+ {can_buy_wheat} [Buy Wheat Seeds - {wheat_price}g] -> BuyFromShop(item_name="Wheat Seeds", shop=farmer_shop)

+ {can_buy_carrot} [Buy Carrot Seeds - {carrot_price}g] -> BuyFromShop(item_name="Carrot Seeds", shop=farmer_shop)

+ {can_buy_hoe} [Buy Iron Hoe - {hoe_price}g] -> BuyFromShop(item_name="Iron Hoe", shop=farmer_shop)

+ [Move on] -> Encounter2

:: BuyFromShop(item_name, shop)
@py:
success = shop.buy(item_name, player_wallet, player_inventory)
price = shop.get_buy_price(item_name)
@endpy

@if success:
    ✓ Bought **{item_name}** for {price}g!

    Gold: {player_wallet.gold}g
@else:
    Can't buy {item_name} - {player_inventory.is_full ? "pack full" | "not enough gold"}!
@endif

+ [Continue] -> Encounter1

:: Encounter2
---
**Encounter 2: The Bandit**

A bandit steps onto the road!

"Your coin or your life, merchant!"

+ [Pay toll (20g)] -> PayBandit
+ [Fight!] -> FightBandit
+ [Try to intimidate] -> IntimidateBandit

:: PayBandit
@py:
if player_wallet.spend(20):
    paid = True
else:
    paid = False
    # Can't pay - lose half your gold!
    player_wallet.gold = player_wallet.gold // 2
@endpy

@if paid:
    You hand over 20 gold. She lets you pass.

    Gold: {player_wallet.gold}g
@else:
    You don't have 20g! She robs you for half your gold instead!

    Gold: {player_wallet.gold}g
@endif

+ [Continue] -> Encounter3

:: FightBandit
@py:
combat_roll = roll('1d20')
@endpy

You attack! Roll: **{combat_roll}**

@if combat_roll >= 15:
    **Critical hit!** She flees, dropping 30 gold!

    @py:
    player_wallet.earn(30)
    @endpy

    Gold: {player_wallet.gold}g (+30g)
@elif combat_roll >= 10:
    You drive her off! She retreats empty-handed.
@else:
    She disarms you and takes half your gold!

    @py:
    player_wallet.gold = player_wallet.gold // 2
    @endpy

    Gold: {player_wallet.gold}g
@endif

+ [Continue] -> Encounter3

:: IntimidateBandit
@py:
# Your gold makes you more intimidating!
intimidation = roll('1d20') + (player_wallet.gold // 10)
@endpy

You puff out your chest. Roll: **{intimidation}** (DC 15)

@if intimidation >= 15:
    "You're not worth the trouble," she mutters, stepping aside.

    **Success!** No toll paid.
@else:
    She laughs. "Nice try!"

    ~ player_wallet.spend(20)

    You pay 20g.

    Gold: {player_wallet.gold}g
@endif

+ [Continue] -> Encounter3

:: Encounter3
---
**Encounter 3: The Capital**

You arrive at the grand market!

@py:
# Capital shop buys things at good prices
final_value = player_inventory.total_value
final_gold = player_wallet.gold
final_total = final_gold + final_value

# Starting value
starting = 115  # 100g + 15g starting items

profit = final_total - starting
@endpy

**FINAL TALLY:**

**Current Gold:** {final_gold}g
**Inventory Value:** {final_value}g
**Total Worth:** {final_total}g

**Profit:** {profit}g

---

@if profit >= 100:
    **MASTER MERCHANT!** Excellent trading!
@elif profit >= 50:
    **SUCCESSFUL TRADER!** Nice work!
@elif profit >= 0:
    **BREAK EVEN.** Not bad for a first run!
@else:
    **BANKRUPT.** Better luck next time!
@endif

**Items in your pack:**
@for item in player_inventory.items:
    - {item['name']} ({item['value']}g value)
@endfor

Try different strategies next time!
```

## 10.5 Generating choices from `for`-loops

See the [code here](https://github.com/katelouie/bardic/blob/main/bardic/examples/wandering_merchant/merchant.bard#L78) used in the "Wandering Merchant" story for an example of how to programmatically generate choices via iterating over a list or collection, rather than having to manually type up choices and pre-choice calculated values yourself (as shown in the above story).

---

## 11. The Power of Reusable Passages

Notice how we only wrote **ONE** `BuyFromShop` passage, but used it for:

- Multiple items at the farmer
- Multiple items at other vendors
- Different return points

This is the power of passage parameters! Instead of writing:

- `Buy_Wheat_Seeds`
- `Buy_Carrot_Seeds`
- `Buy_Iron_Hoe`
- ...20 more passages

We wrote ONE reusable passage that works for everything.

---

## 12. Key Takeaways

**Passage Parameters:**

- Pass data into passages: `-> PassageName(param=value)`
- Define parameters: `:: PassageName(param1, param2="default")`
- Parameters become variables inside the passage
- Can pass literals, variables, expressions, or objects

**Standard Library Modules:**

- `bardic.modules.inventory` - Item management
- `bardic.modules.economy` - Shops and currency
- `bardic.modules.dice` - Randomness and checks
- `bardic.modules.relationship` - NPC relationships

**The Pattern:**

1. Import the module: `from bardic.modules.economy import Shop`
2. Create objects: `~ shop = Shop(items)`
3. Use in reusable passages: `-> BuyFromShop(shop=shop)`

---

## 13. Your Turn: Extend the Game

Try adding:

1. **More vendors** - Wizard, noble, tavern keeper
2. **Selling items** - Create a `SellToShop` passage
3. **Weight management** - Drop items if pack is full
4. **Item categories** - Filter by type (food, tools, weapons)
5. **Dynamic prices** - Items cost more/less at different vendors

The modules give you the building blocks. Passage parameters let you reuse logic. Together, they let you build complex systems with clean code!

---

## 🎉 Congratulations

You've mastered:

- Passage parameters for reusable logic
- Bardic's standard library modules
- Building complete game systems (shops, inventory, currency)
- Combining everything into a playable game

You're now ready to build serious interactive fiction with sophisticated mechanics!

---

## Next Steps

**Want custom UI?** Continue to Part 4 to learn about NiceGUI and `@render` directives.

**Want to organize large projects?** Skip to Part 5 to learn about `@include` and modular story files.

**Ready to build?** You have everything you need. Go make something awesome!

---

[← Back to Part 3B](03b_creating_objects.md) | [Continue to Part 4 →](04_custom_ui.md)
