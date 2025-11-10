class Character:
    def __init__(self, name: str) -> None:
        self.name = name
        self.stats = Stats()
        self.inventory = []
        self.weapon = ""

    def equip_weapon(self, item: str) -> None:
        self.weapon = item


class Stats:
    def __init__(self) -> None:
        self.health = 0
        self.mana = 0


class Player:
    def __init__(self, name: str) -> None:
        self.name = name
        self.inventory = []
        self.health = 100

    def add_item(self, item: str) -> None:
        self.inventory.append(item)

    def get_status(self):
        if self.health > 0:
            return "Alive"
        return "Dead"
