"""Quest and journal tracking for interactive fiction.

Track objectives, stages, completion, and journal entries
for any number of quests or tasks.

Usage:
    from bardic.stdlib.quest import QuestJournal

    # Create a journal
    journal = QuestJournal()

    # Add quests
    journal.add("find_key", "Find the Brass Key",
                description="The librarian lost her key somewhere in the garden.")

    # Update stages
    journal.set_stage("find_key", "searched_garden")
    journal.complete("find_key")

    # Check status
    if journal.is_complete("find_key"):
        print("You found it!")

    # Add journal entries (narrative log)
    journal.log("find_key", "Found scratch marks near the fountain.")

    # Get all active quests
    for q in journal.active_quests:
        print(f"{q.title} - {q.stage}")
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Quest:
    """A single quest or objective.

    Attributes:
        quest_id: Unique identifier (used in code)
        title: Display name (shown to player)
        description: Optional longer description
        stage: Current stage string ("active", "complete", "failed", or custom)
        log: List of journal entries (narrative breadcrumbs)
    """

    quest_id: str
    title: str
    description: str = ""
    stage: str = "active"
    log: list[str] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        """Quest is in progress (not complete or failed)."""
        return self.stage not in ("complete", "failed")

    @property
    def is_complete(self) -> bool:
        return self.stage == "complete"

    @property
    def is_failed(self) -> bool:
        return self.stage == "failed"

    def to_dict(self) -> dict:
        """Serialize for save/load."""
        return {
            "quest_id": self.quest_id,
            "title": self.title,
            "description": self.description,
            "stage": self.stage,
            "log": list(self.log),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        """Deserialize from save data."""
        return cls(
            quest_id=data["quest_id"],
            title=data["title"],
            description=data.get("description", ""),
            stage=data.get("stage", "active"),
            log=data.get("log", []),
        )


class QuestJournal:
    """Track multiple quests with stages and journal entries.

    The journal is the central hub for all quest tracking. Quests are
    identified by a unique string ID and can be in any stage you define.

    Built-in stages:
        "active"   — quest is in progress (default when added)
        "complete" — quest is finished successfully
        "failed"   — quest failed or was abandoned

    Custom stages (any string you want):
        "searched_garden", "talked_to_witness", "found_clue", etc.
    """

    def __init__(self):
        self._quests: dict[str, Quest] = {}

    def add(self, quest_id: str, title: str, description: str = "", stage: str = "active") -> Quest:
        """Add a new quest to the journal.

        Args:
            quest_id: Unique identifier for the quest
            title: Display title
            description: Optional longer description
            stage: Starting stage (default "active")

        Returns:
            The created Quest object

        Raises:
            ValueError: If quest_id already exists
        """
        if quest_id in self._quests:
            raise ValueError(f"Quest '{quest_id}' already exists in journal")
        quest = Quest(quest_id=quest_id, title=title, description=description, stage=stage)
        self._quests[quest_id] = quest
        return quest

    def get(self, quest_id: str) -> Optional[Quest]:
        """Get a quest by ID, or None if not found."""
        return self._quests.get(quest_id)

    def has(self, quest_id: str) -> bool:
        """Check if a quest exists in the journal."""
        return quest_id in self._quests

    # ── Status checks ──

    def is_active(self, quest_id: str) -> bool:
        """Check if quest is in progress."""
        quest = self._quests.get(quest_id)
        return quest.is_active if quest else False

    def is_complete(self, quest_id: str) -> bool:
        """Check if quest is complete."""
        quest = self._quests.get(quest_id)
        return quest.is_complete if quest else False

    def is_failed(self, quest_id: str) -> bool:
        """Check if quest has failed."""
        quest = self._quests.get(quest_id)
        return quest.is_failed if quest else False

    def stage_of(self, quest_id: str) -> Optional[str]:
        """Get current stage of a quest, or None if not found."""
        quest = self._quests.get(quest_id)
        return quest.stage if quest else None

    # ── Stage transitions ──

    def set_stage(self, quest_id: str, stage: str) -> None:
        """Set a quest to a custom stage.

        Args:
            quest_id: Quest to update
            stage: New stage string (any value you want)

        Raises:
            KeyError: If quest doesn't exist
        """
        quest = self._quests.get(quest_id)
        if not quest:
            raise KeyError(f"Quest '{quest_id}' not found in journal")
        quest.stage = stage

    def complete(self, quest_id: str) -> None:
        """Mark a quest as complete.

        Args:
            quest_id: Quest to complete

        Raises:
            KeyError: If quest doesn't exist
        """
        self.set_stage(quest_id, "complete")

    def fail(self, quest_id: str) -> None:
        """Mark a quest as failed.

        Args:
            quest_id: Quest to fail

        Raises:
            KeyError: If quest doesn't exist
        """
        self.set_stage(quest_id, "failed")

    # ── Journal entries ──

    def log(self, quest_id: str, entry: str) -> None:
        """Add a journal entry to a quest.

        Journal entries are narrative breadcrumbs — short notes about
        what happened, clues found, people talked to. They're stored
        in order and can be displayed as a quest log.

        Args:
            quest_id: Quest to add entry to
            entry: The journal text

        Raises:
            KeyError: If quest doesn't exist
        """
        quest = self._quests.get(quest_id)
        if not quest:
            raise KeyError(f"Quest '{quest_id}' not found in journal")
        quest.log.append(entry)

    def get_log(self, quest_id: str) -> list[str]:
        """Get all journal entries for a quest.

        Returns:
            List of entries in chronological order, or empty list if quest not found
        """
        quest = self._quests.get(quest_id)
        return list(quest.log) if quest else []

    # ── Filtered views ──

    @property
    def active_quests(self) -> list[Quest]:
        """All quests currently in progress."""
        return [q for q in self._quests.values() if q.is_active]

    @property
    def completed_quests(self) -> list[Quest]:
        """All completed quests."""
        return [q for q in self._quests.values() if q.is_complete]

    @property
    def failed_quests(self) -> list[Quest]:
        """All failed quests."""
        return [q for q in self._quests.values() if q.is_failed]

    @property
    def all_quests(self) -> list[Quest]:
        """All quests in the journal."""
        return list(self._quests.values())

    @property
    def count_active(self) -> int:
        """Number of active quests."""
        return len(self.active_quests)

    @property
    def count_complete(self) -> int:
        """Number of completed quests."""
        return len(self.completed_quests)

    # ── Serialization ──

    def to_dict(self) -> dict:
        """Serialize for save/load."""
        return {"quests": {qid: q.to_dict() for qid, q in self._quests.items()}}

    @classmethod
    def from_dict(cls, data: dict) -> "QuestJournal":
        """Deserialize from save data."""
        journal = cls()
        for qid, qdata in data.get("quests", {}).items():
            journal._quests[qid] = Quest.from_dict(qdata)
        return journal

    def __repr__(self) -> str:
        active = self.count_active
        done = self.count_complete
        return f"QuestJournal({active} active, {done} complete)"
