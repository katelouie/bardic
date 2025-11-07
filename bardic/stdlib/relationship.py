"""Relationship tracking for NPCs in interactive fiction.

Tracks trust, comfort, and openness with threshold events and
computed properties for relationship quality.

Usage:
    from bardic.stdlib.relationship import Relationship

    # In your @py: block
    alex = Relationship(name="Alex", trust=50, comfort=50)
    alex.add_trust(10)  # Increases to 60, may trigger threshold

    if alex.is_ready_for_deep_conversation:
        # Alex trusts you enough for vulnerable topics
        pass
"""

from typing import Optional, Set


class Relationship:
    """Track relationship progression with an NPC.

    Attributes:
        name: NPC's name
        trust: 0-100, how much they trust you
        comfort: 0-100, how comfortable they feel with you
        openness: -10 to +10, defensive vs vulnerable
        topics_discussed: Set of topic tags discussed
    """

    def __init__(
        self,
        name: str,
        trust: int,
        comfort: int,
        openness: int,
        topics_discussed: Optional[Set[str]] = None,
    ):
        self.name: str
        self.topics_discussed = topics_discussed if topics_discussed else set()
        self._trust = 50
        self._comfort = 50
        self._openness = 0
        self.trust = trust  # Triggers setter
        self.comfort = comfort  # Triggers setter
        self.openness = openness  # Triggers setter

    # === TRUST (0-100) ===
    @property
    def trust(self) -> int:
        return self._trust

    @trust.setter
    def trust(self, value: int):
        self.trust = max(0, min(100, value))

    def add_trust(self, amount: int):
        """Add trust with automatic threshold checks."""
        old_trust = self.trust
        self.trust += amount  # Uses setter, auto-clamps

        # Threshold events
        if old_trust < 60 <= self.trust:
            self.on_trust_threshold_60()
        if old_trust < 80 <= self.trust:
            self.on_trust_threshold_80()

    # === COMFORT (0-100) ===
    @property
    def comfort(self) -> int:
        return self._comfort

    @comfort.setter
    def comfort(self, value: int):
        self._comfort = max(0, min(100, value))

    def add_comfort(self, amount: int):
        """Add comfort with bounds checking."""
        self.comfort += amount  # Uses setter

    # === OPENNESS (-10 to +10) ===
    @property
    def openness(self) -> int:
        return self._openness

    @openness.setter
    def openness(self, value: int):
        self._openness = max(-10, min(10, value))

    def add_openness(self, amount: int):
        """Add openness with bounds checking."""
        self.openness += amount  # Uses setter

    # Threshold hooks (override in subclasses)
    def on_trust_threshold_60(self):
        """Called when trust reaches 60."""
        pass

    def on_trust_threshold_80(self):
        """Called when trust reaches 80."""
        pass

    # Discussing topics in conversation
    def discuss_topic(self, topic: str):
        """Mark a topic as discussed."""
        self.topics_discussed.add(topic)

    def has_discussed(self, topic: str) -> bool:
        """Check if topic was covered."""
        return topic in self.topics_discussed

    # Computed properties
    @property
    def is_ready_for_deep_conversation(self) -> bool:
        """Has sufficient trust/openness for vulnerable topics."""
        return self.trust >= 60 and self.openness >= 1

    @property
    def relationship_quality(self) -> str:
        """Qualitative assessment of relationship."""
        if self.trust >= 80:
            return "close_confidant"
        elif self.trust >= 60:
            return "trusted_guide"
        elif self.trust >= 40:
            return "professional"
        elif self.trust >= 20:
            return "cautious"
        else:
            return "guarded"

    @property
    def is_defensive(self) -> bool:
        """NPC is guarded and closed off."""
        return self.openness <= -3

    @property
    def is_vulnerable(self) -> bool:
        """NPC is open and sharing deeply."""
        return self.openness >= 5

    def to_dict(self) -> dict:
        """Serialize for save/load."""
        return {
            "name": self.name,
            "trust": self.trust,
            "comfort": self.comfort,
            "openness": self.openness,
            "topics_discussed": list(self.topics_discussed),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        """Deserialize from save data."""
        return cls(
            name=data["name"],
            trust=data["trust"],
            comfort=data["comfort"],
            openness=data["openness"],
            topics_discussed=set(data["topics_discussed"]),
        )
