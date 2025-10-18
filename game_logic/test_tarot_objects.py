"""Mock tarot objects for testing."""

import random


class Card:
    def __init__(self, name, suit, number) -> None:
        self.name = name
        self.suit = suit
        self.number = number
        self.reversed = False
        self.position = None

    def __repr__(self) -> str:
        return f"Card({self.name}, {self.suit})"

    def set_reversed(self, is_reversed) -> None:
        self.reversed = is_reversed

    def in_position(self, position) -> "Card":
        self.position = position
        return self  # Allow chaining

    def get_display_name(self) -> str:
        prefix = "↓ " if self.reversed else ""
        return f"{prefix}{self.name}"

    def is_major_arcana(self) -> None:
        return self.suit == "major"

    def get_position_meaning(self) -> str:
        meanings = {
            "past": "influences from your past",
            "present": "your current situation",
            "future": "potential outcomes",
        }
        return meanings.get(str(self.position), "unknown position")

    def to_save_dict(self) -> dict:
        """
        Serialize a card into a dictionary for saving.

        This method is called automatically by the engine when saving. You can
        customize what gets saved here.
        """
        return {
            "name": self.name,
            "number": self.number,
            "reversed": self.reversed,
            "suit": self.suit,
        }

    @classmethod
    def from_save_dict(cls, data: dict) -> "Card":
        """
        Restore a card from saved data.

        This method is called automatically by the engine when loading.
        It goes through __init__, so validation runs!
        """
        card = cls(
            name=data["name"],
            suit=data["suit"],
            number=data["number"],
        )
        card.set_reversed(data.get("reversed", False))

        return card


class Client:
    def __init__(self, name, age) -> None:
        self.name = name
        self.age = age
        self.trust_level = 50
        self.cards_seen = []
        self.session_count = 0
        self.flavor_text: str = "Client Flavor Text"

    def add_card_seen(self, card) -> None:
        self.cards_seen.append(card.name)

    def modify_trust(self, amount) -> None:
        self.trust_level = max(0, min(100, self.trust_level + amount))

    def get_trust_description(self) -> str:
        if self.trust_level > 75:
            return "deeply trusts you"
        elif self.trust_level > 50:
            return "trusts you"
        elif self.trust_level > 25:
            return "is uncertain"
        else:
            return "is skeptical"

    def start_session(self) -> None:
        self.session_count += 1


class Reader:
    def __init__(self, name) -> None:
        self.name = name
        self.experience = 0
        self.style = "traditional"
        self.specialties = []

    def add_experience(self, points) -> None:
        self.experience += points

    def get_level(self) -> str:
        if self.experience < 100:
            return "Novice"
        elif self.experience < 500:
            return "Apprentice"
        elif self.experience < 1000:
            return "Adept"
        else:
            return "Master"


# Mock service functions
def draw_cards(count=3):
    """Draw random cards"""
    cards_pool = [
        Card("The Fool", "major", 0),
        Card("The Magician", "major", 1),
        Card("The High Priestess", "major", 2),
        Card("The Empress", "major", 3),
        Card("The Emperor", "major", 4),
        Card("Ace of Cups", "cups", 1),
        Card("Two of Cups", "cups", 2),
        Card("Knight of Swords", "swords", 12),
    ]
    drawn = random.sample(cards_pool, min(count, len(cards_pool)))

    # Random reversals:
    for card in drawn:
        if random.random() < 0.3:
            card.set_reversed(True)

    return drawn


if __name__ == "__main__":
    # Test
    cards = draw_cards(3)
    for card in cards:
        print(f"{card.get_display_name()} - {card.suit}")

    client = Client("Aria", 28)
    print(f"{client.name} {client.get_trust_description()}")
