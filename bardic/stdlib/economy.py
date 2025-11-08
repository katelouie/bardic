"""Economy system for currency, shops, and trading.

Usage:
    from bardic.modules.economy import Wallet, Shop
    from bardic.modules.inventory import Inventory

    # Create wallet and inventory
    wallet = Wallet(gold=100)
    inv = Inventory()

    # Create shop with items for sale
    shop = Shop([
        {'name': 'Sword', 'weight': 5, 'value': 100},
        {'name': 'Potion', 'weight': 0.5, 'value': 50}
    ])

    # Buy from shop
    if shop.buy('Sword', wallet, inv):
        print("Purchase successful!")

    # Sell to shop (at 50% value)
    if shop.sell('Potion', wallet, inv):
        print("Sold!")
"""

from typing import Optional
from bardic.stdlib.inventory import Inventory


class Wallet:
    """Manage player currency.

    Simple gold tracking with spend/earn methods.
    """

    def __init__(self, gold: int = 0) -> None:
        """Create a wallet with starting gold.

        Args:
            gold: Starting amount (default 0)
        """
        self._gold = max(0, gold)  # Never less than 0

    @property
    def gold(self) -> int:
        """Current gold amount."""
        return self._gold

    @gold.setter
    def gold(self, value: int):
        """Set gold amount (clamped to minimum 0)."""
        self._gold = max(0, value)

    def can_afford(self, price: int) -> bool:
        """Check if wallet has enough gold.

        Args:
            price: Cost to check

        Returns:
            True if gold >= price
        """
        return self.gold >= price

    def spend(self, amount: int) -> bool:
        """Spend gold if possible.

        Args:
            amount: Gold to spend

        Returns:
            True if spent successfully, False if insufficient funds
        """
        if self.can_afford(amount):
            self._gold -= amount
            return True
        return False

    def earn(self, amount: int):
        """Add gold to wallet.

        Args:
            amount: Gold to add
        """
        self._gold += max(0, amount)  # Can't earn negative

    def to_dict(self) -> dict:
        """Serialize for save/load."""
        return {"gold": self.gold}

    @classmethod
    def from_dict(cls, data: dict) -> "Wallet":
        """Deserialize from save data."""
        return cls(gold=data["gold"])

    def __repr__(self) -> str:
        return f"Wallet({self.gold} gold)"


class Shop:
    """A shop that sells items and buys them back.

    Integrates with Wallet and Inventory for transactions.
    """

    def __init__(
        self, items: list[dict], sell_back_rate: float = 0.5, discount: float = 1.0
    ):
        """Create a shop with inventory.

        Args:
            items: List of item dicts available for sale
            sell_back_rate: Multiplier for selling items back (default 0.5 = 50%)
            discount: Price mutliplier for buying (default 1.0 = full price)
        """
        self.items = items
        self.sell_back_rate = sell_back_rate
        self.discount = discount

    def find_item(self, item_name: str) -> Optional[dict]:
        """Find an item in shop inventory.

        Args:
            item_name: Name of item to find

        Returns:
            First item dict if found, None otherwise
        """
        for item in self.items:
            if item["name"] == item_name:
                return item
        return None

    def get_buy_price(self, item_name: str) -> int:
        """Get the price to buy an item from shop.

        Args:
            item_name: Name of item

        Returns:
            Price in gold (with discount applied)
        """
        item = self.find_item(item_name)
        if item and "value" in item:
            return int(item["value"] * self.discount)
        return 0

    def get_sell_price(self, item_value: int) -> int:
        """Get the price shop will pay for an item.

        Args:
            item_value: Base value of item

        Returns:
            Price shop will pay (with sell_back_rate applied)
        """
        return int(item_value * self.sell_back_rate)

    def buy(self, item_name: str, wallet: "Wallet", inventory: Inventory) -> bool:
        """Buy an item from the shop.

        Deducts gold from wallet and adds item to inventory.
        If inventory is full, refunds the gold.

        Args:
            item_name: Name of item to buy
            wallet: Player's wallet
            inventory: Player's inventory

        Returns:
            True if purchase successful, False otherwise

        Example:
            >>> if shop.buy('Sword', my_wallet, my_inventory):
            ...     print("Bought a sword!")
        """
        item = self.find_item(item_name)
        if not item:
            return False  # Item not in shop

        price = self.get_buy_price(item_name)

        # Try to spend gold
        if not wallet.spend(price):
            return False  # Can't afford

        # Try to add to inventory
        if inventory.add(item.copy()):  # Copy so shop inventory isn't modified
            return True
        else:
            # Inventory full - refund
            wallet.earn(price)
            return False

    def sell(self, item_name: str, wallet: "Wallet", inventory: Inventory) -> bool:
        """Sell an item to the shop.

        Removes item from inventory and adds gold to wallet.

        Args:
            item_name: Name of item to sell
            wallet: Player's wallet
            inventory: Player's inventory

        Returns:
            True if sale successful, False if item not in inventory

        Example:
            >>> if shop.sell('Potion', my_wallet, my_inventory):
            ...     print("Sold a potion!")
        """
        # Find the item in player inventory
        item = inventory.get(item_name)
        if not item:
            return False  # Don't have it

        # Calculate sell price
        item_value = item.get("value", 0)
        sell_price = self.get_sell_price(item_value)

        # Remove from inventory
        if inventory.remove(item_name):
            wallet.earn(sell_price)
            return True
        return False

    def set_discount(self, discount: float):
        """Change shop's price multiplier.

        Args:
            discount: New multiplier (0.8 = 20% off, 1.2 = 20% markup)
        """
        self.discount = max(0.0, discount)

    def to_dict(self) -> dict:
        """Serialize for save/load."""
        return {
            "items": self.items,
            "sell_back_rate": self.sell_back_rate,
            "discount": self.discount,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Shop":
        """Deserialize from save data."""
        return cls(
            items=data["items"],
            sell_back_rate=data["sell_back_rate"],
            discount=data["discount"],
        )

    def __repr__(self) -> str:
        return f"Shop({len(self.items)} items for sale)"
