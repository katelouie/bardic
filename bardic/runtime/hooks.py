"""
Hook management for the Bardic runtime engine.

Hooks allow passages to be called automatically when game events fire.
For example, a "turn_end" hook runs a passage after every player choice.
"""

import copy


class HookManager:
    """Manages event hooks (passage callbacks triggered by game events).

    Hooks are stored in FIFO order and executed in registration order.
    Registration is idempotent — registering the same passage twice for
    the same event is a no-op.

    Usage:
        hook_manager = HookManager()
        hook_manager.register("turn_end", "CleanupPassage")
        hook_manager.get_handlers("turn_end")  # ["CleanupPassage"]
    """

    def __init__(self):
        self.hooks: dict[str, list[str]] = {}

    def register(self, event: str, passage_id: str) -> None:
        """Register a passage to be called when an event fires.

        Args:
            event: Event name (e.g. "turn_end")
            passage_id: Passage to execute when event fires
        """
        if event not in self.hooks:
            self.hooks[event] = []

        # Prevent dupes
        if passage_id not in self.hooks[event]:
            self.hooks[event].append(passage_id)

    def unregister(self, event: str, passage_id: str) -> None:
        """Remove a passage from an event's hook list.

        Silently succeeds if the passage wasn't hooked (idempotent).

        Args:
            event: Event name
            passage_id: Passage to remove
        """
        if event in self.hooks and passage_id in self.hooks[event]:
            self.hooks[event].remove(passage_id)

    def get_handlers(self, event: str) -> list[str]:
        """Get the list of passage IDs registered for an event.

        Returns a copy to allow safe iteration during trigger_event
        (hooks may unregister themselves during execution).

        Args:
            event: Event name

        Returns:
            List of passage IDs, or empty list if no handlers registered.
        """
        if event not in self.hooks:
            return []
        return list(self.hooks[event])

    def snapshot(self) -> dict[str, list[str]]:
        """Return a deep copy of all hook registrations for undo/redo snapshots."""
        return copy.deepcopy(self.hooks)

    def restore(self, hooks: dict[str, list[str]]) -> None:
        """Restore hook registrations from a snapshot.

        Uses clear() + update() to preserve shared references,
        consistent with state/used_choices/join_section_index restoration.
        """
        self.hooks.clear()
        self.hooks.update(hooks)
