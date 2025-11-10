"""
Test tarot objects for Bardic test stories.

These classes are used by test .bard files to verify that Bardic can correctly
handle custom Python objects with methods and state.
"""

import random


class Card:
    """A tarot card with name, suit, position, and reversal status."""

    # Major arcana cards (no suit)
    MAJOR_ARCANA = [
        "The Fool",
        "The Magician",
        "The High Priestess",
        "The Empress",
        "The Emperor",
        "The Hierophant",
        "The Lovers",
        "The Chariot",
        "Strength",
        "The Hermit",
        "Wheel of Fortune",
        "Justice",
        "The Hanged Man",
        "Death",
        "Temperance",
        "The Devil",
        "The Tower",
        "The Star",
        "The Moon",
        "The Sun",
        "Judgement",
        "The World",
    ]

    # Minor arcana suits
    SUITS = ["Cups", "Wands", "Swords", "Pentacles"]
    RANKS = [
        "Ace",
        "Two",
        "Three",
        "Four",
        "Five",
        "Six",
        "Seven",
        "Eight",
        "Nine",
        "Ten",
        "Page",
        "Knight",
        "Queen",
        "King",
    ]

    def __init__(self, name, number=0, reversed=False):
        """
        Create a tarot card.

        Args:
            name: Card name (e.g., "The Fool" or "Ace of Cups")
            number: Card number (0-21 for major arcana, used for ordering)
            reversed: Whether the card is reversed
        """
        self.name = name
        self.number = number
        self.reversed = reversed
        self.position = None  # Set via in_position()

        # Determine suit (None for major arcana)
        if name in self.MAJOR_ARCANA:
            self.suit = None
        else:
            # Parse suit from name like "Ace of Cups"
            for suit in self.SUITS:
                if suit in name:
                    self.suit = suit
                    break
            else:
                self.suit = "Unknown"

    def in_position(self, position):
        """Set the position of this card in a spread."""
        self.position = position
        return self  # Allow chaining

    def is_major_arcana(self):
        """Check if this is a major arcana card."""
        return self.suit is None

    def get_display_name(self):
        """Get the display name including reversal status."""
        if self.reversed:
            return f"{self.name} (Reversed)"
        return self.name

    def get_position_meaning(self):
        """Get a generic interpretation based on position."""
        meanings = {
            "past": "What has shaped you",
            "present": "Where you are now",
            "future": "What approaches",
            "challenge": "The obstacle or lesson",
            "outcome": "The potential resolution",
            "advice": "Guidance for moving forward",
        }
        return meanings.get(self.position, "Unknown position")

    def set_reversed(self, is_reversed: bool) -> None:
        self.reversed = is_reversed


class Client:
    """A client receiving a tarot reading."""

    def __init__(self, name, age):
        """
        Create a client.

        Args:
            name: Client's name
            age: Client's age
        """
        self.name = name
        self.age = age
        self.trust_level = 50  # Default trust (0-100)
        self.cards_seen = []  # Track cards shown to this client
        self.session_count = 0

    def modify_trust(self, amount):
        """
        Modify trust level by the given amount.

        Args:
            amount: Amount to add (positive) or subtract (negative)
        """
        self.trust_level = max(0, min(100, self.trust_level + amount))

    def add_card_seen(self, card):
        """Track that this client has seen a card."""
        self.cards_seen.append(card)

    def get_trust_description(self):
        """Get a text description of the current trust level."""
        if self.trust_level >= 90:
            return "I trust you completely. This reading changed everything."
        elif self.trust_level >= 75:
            return "I really appreciate your insight. Thank you."
        elif self.trust_level >= 50:
            return "That was interesting. I'll think about it."
        elif self.trust_level >= 25:
            return "I'm not sure what to make of this..."
        else:
            return "This doesn't resonate with me at all."

    def start_session(self):
        self.session_count += 1


class Reader:
    """A tarot reader with experience and level."""

    def __init__(self, name):
        """
        Create a reader.

        Args:
            name: Reader's name
        """
        self.name = name
        self.experience = 0

    def add_experience(self, amount):
        """Add experience points."""
        self.experience += amount

    def get_level(self):
        """Calculate level based on experience."""
        # Simple leveling: 100 exp per level
        return self.experience // 100


def draw_cards(count):
    """
    Draw random tarot cards.

    Args:
        count: Number of cards to draw

    Returns:
        List of Card objects
    """
    # Create a simple deck (just major arcana + some minor for testing)
    deck = []

    # Add all major arcana
    for i, name in enumerate(Card.MAJOR_ARCANA):
        deck.append(Card(name, i, random.choice([True, False])))

    # Add some minor arcana
    for suit in Card.SUITS:
        for rank in Card.RANKS[:5]:  # Just first 5 ranks for testing
            name = f"{rank} of {suit}"
            deck.append(Card(name, 0, random.choice([True, False])))

    # Shuffle and draw
    random.shuffle(deck)
    return deck[:count]
