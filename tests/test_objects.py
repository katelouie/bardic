"""Simple object for testing"""


class Card:
    def __init__(self, name, suit):
        self.name = name
        self.suit = suit
        self.reversed = False

    def get_display_name(self):
        suffix = " (Reversed)" if self.reversed else ""
        return f"{self.name}{suffix}"

    def is_major_arcana(self):
        return self.suit == "major"

    def __str__(self):
        return self.get_display_name()


class Stats:
    def __init__(self):
        self.health = 100
        self.mana = 50
        self.stamina = 75

    def get_total(self):
        return self.health + self.mana + self.stamina


class Player:
    def __init__(self, name):
        self.name = name
        self.stats = Stats()
        self.inventory = []

    def add_item(self, item):
        self.inventory.append(item)

    def get_status(self):
        return f"{self.name}: {self.stats.health} HP, {len(self.inventory)} items"


class Character:
    def __init__(self, name):
        self.name = name
        self.stats = Stats()
        self.inventory = []
        self.equipped = {"weapon": None, "armor": None}

    def equip_weapon(self, weapon):
        self.equipped["weapon"] = weapon

    def get_info(self):
        return f"{self.name}: {self.stats.health} HP"


if __name__ == "__main__":
    # Test the classes
    card = Card("The Fool", "major")
    print(card.name)
    print(card.get_display_name())
    print(card.is_major_arcana())

    player = Player("Hero")
    player.add_item("sword")
    print(player.get_status())
