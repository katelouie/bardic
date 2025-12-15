"""Inventory management for items with weight limits and categories.

Usage:
    from bardic.modules.inventory import Inventory

    # Create inventory
    inv = Inventory(max_weight=50)

    # Add items (dicts with name, weight, value)
    inv.add({'name': 'Sword', 'weight': 5, 'value': 100})

    # Check and remove
    if inv.has('Sword'):
        inv.remove('Sword')

    # Check capacity
    if not inv.is_full:
        inv.add(new_item)
"""

from typing import Optional


class Inventory:
    """Manage items with weight limits and categorization.

    Items are represented as dictionaries with at minimum:
        - 'name': str (required)
        - 'weight': float (required, defaults to 0 if missing)
        - 'value': int (optional, for economy integration)
        - 'category': str (optional, for filtering)

    Example item:
        {
            'name': 'Healing Potion',
            'weight': 0.5,
            'value': 50,
            'category': 'consumable'
        }
    """

    def __init__(self, max_weight: float = 100.0):
        """Create an inventory with weight limit.

        Args:
            max_weight: Maximum weight capacity (default 100)
        """
        self.items: list[dict] = []
        self.max_weight = max_weight

    def add(self, item: dict) -> bool:
        """Add an item if weight allows.

        Args:
            item: Item dict with at least 'name' and 'weight'

        Returns:
            True if added successfully, False if inventory full

        Example:
            >>> inv.add({'name': 'Sword', 'weight': 5, 'value': 100})
            True
        """
        if "name" not in item:
            raise ValueError("Item must have a 'name' field")

        # Default weight to 0 if not specified
        item_weight = item.get("weight", 0)

        if self.current_weight + item_weight <= self.max_weight:
            self.items.append(item)
            return True
        return False

    def remove(self, item_name: str) -> bool:
        """Remove first matching item by name.

        Args:
            item_name: Name of item to remove

        Returns:
            True if removed, False if not found

        Example:
            >>> inv.remove('Sword')
            True
        """
        for item in self.items:
            if item["name"] == item_name:
                self.items.remove(item)
                return True
        return False

    def remove_all(self, item_name: str) -> int:
        """Remove all items matching name.

        Args:
            item_name: Name of items to remove

        Returns:
            Number of items removed
        """
        original_count = len(self.items)
        self.items = [item for item in self.items if item["name"] != item_name]
        return original_count - len(self.items)

    def has(self, item_name: str) -> bool:
        """Check if item exists in inventory.

        Args:
            item_name: Name of item to check

        Returns:
            True if at least one exists

        Example:
            >>> inv.has('Sword')
            True
        """
        return any(item["name"] == item_name for item in self.items)

    def count(self, item_name: str) -> int:
        """Count how many of an item exist.

        Args:
            item_name: Name of item to count

        Returns:
            Number of matching items

        Example:
            >>> inv.count('Potion')
            3
        """
        return sum(1 for item in self.items if item["name"] == item_name)

    def get(self, item_name: str) -> Optional[dict]:
        """Get first matching item (without removing).

        Args:
            item_name: Name of item to find

        Returns:
            Item dict if found, None otherwise
        """
        for item in self.items:
            if item["name"] == item_name:
                return item
        return None

    def get_all(self, item_name: str) -> list[dict]:
        """Get all items matching name.

        Args:
            item_name: Name of items to find

        Returns:
            List of matching item dicts
        """
        return [item for item in self.items if item["name"] == item_name]

    def filter_by_category(self, category: str) -> list[dict]:
        """Get all items in a category.

        Args:
            category: Category to filter by

        Returns:
            List of items in that category

        Example:
            >>> potions = inv.filter_by_category('consumable')
        """
        return [item for item in self.items if item.get("category") == category]

    @property
    def current_weight(self) -> float:
        """Current total weight of all items."""
        return sum(item.get("weight", 0) for item in self.items)

    @property
    def is_full(self) -> bool:
        """Whether inventory is at max weight capacity."""
        return self.current_weight >= self.max_weight

    @property
    def is_empty(self) -> bool:
        """Whether inventory has no items."""
        return len(self.items) == 0

    @property
    def space_remaining(self) -> float:
        """Weight capacity remaining."""
        return max(0, self.max_weight - self.current_weight)

    @property
    def total_value(self) -> int:
        """Sum of all item values (if items have 'value' field)."""
        return sum(item.get("value", 0) for item in self.items)

    def clear(self):
        """Remove all items from inventory."""
        self.items.clear()

    def to_dict(self) -> dict:
        """Serialize for save/load."""
        return {"items": self.items, "max_weight": self.max_weight}

    @classmethod
    def from_dict(cls, data: dict) -> "Inventory":
        """Deserialize from save data."""
        inv = cls(max_weight=data["max_weight"])
        inv.items = data["items"]
        return inv

    def __repr__(self) -> str:
        return f"Inventory({len(self.items)} items, {self.current_weight:.1f}/{self.max_weight} weight)"
