"""Tests for bardic.runtime.hooks — HookManager in isolation."""

import pytest

from bardic.runtime.hooks import HookManager


class TestHookRegistration:
    """Tests for register/unregister operations."""

    def test_register_creates_event_entry(self):
        """Registering a hook creates the event key."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        assert "turn_end" in hm.hooks
        assert hm.hooks["turn_end"] == ["Ticker"]

    def test_register_multiple_handlers(self):
        """Multiple passages can be registered for one event."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.register("turn_end", "Logger")
        assert hm.hooks["turn_end"] == ["Ticker", "Logger"]

    def test_register_is_idempotent(self):
        """Registering the same passage twice is a no-op."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.register("turn_end", "Ticker")
        assert hm.hooks["turn_end"] == ["Ticker"]

    def test_register_fifo_order(self):
        """Handlers are stored in FIFO registration order."""
        hm = HookManager()
        hm.register("turn_end", "First")
        hm.register("turn_end", "Second")
        hm.register("turn_end", "Third")
        assert hm.hooks["turn_end"] == ["First", "Second", "Third"]

    def test_register_different_events(self):
        """Different events maintain separate handler lists."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.register("passage_enter", "Logger")
        assert hm.hooks["turn_end"] == ["Ticker"]
        assert hm.hooks["passage_enter"] == ["Logger"]

    def test_unregister_removes_handler(self):
        """Unregistering removes the passage from the event."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.unregister("turn_end", "Ticker")
        assert "Ticker" not in hm.hooks.get("turn_end", [])

    def test_unregister_is_idempotent(self):
        """Unregistering a non-existent handler doesn't raise."""
        hm = HookManager()
        hm.unregister("nonexistent", "NoSuchPassage")
        # No exception = pass

    def test_unregister_wrong_event(self):
        """Unregistering from wrong event doesn't affect other events."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.unregister("passage_enter", "Ticker")
        assert hm.hooks["turn_end"] == ["Ticker"]

    def test_unregister_preserves_other_handlers(self):
        """Unregistering one handler doesn't affect others on same event."""
        hm = HookManager()
        hm.register("turn_end", "First")
        hm.register("turn_end", "Second")
        hm.register("turn_end", "Third")
        hm.unregister("turn_end", "Second")
        assert hm.hooks["turn_end"] == ["First", "Third"]


class TestGetHandlers:
    """Tests for get_handlers (used by trigger_event)."""

    def test_get_handlers_returns_list(self):
        """get_handlers returns a list of passage IDs."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        assert hm.get_handlers("turn_end") == ["Ticker"]

    def test_get_handlers_empty_event(self):
        """get_handlers returns empty list for unregistered events."""
        hm = HookManager()
        assert hm.get_handlers("nonexistent") == []

    def test_get_handlers_returns_copy(self):
        """get_handlers returns a copy, not the original list."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        handlers = hm.get_handlers("turn_end")
        handlers.append("Injected")
        assert "Injected" not in hm.hooks["turn_end"]


class TestSnapshotRestore:
    """Tests for snapshot/restore (used by undo/redo and save/load)."""

    def test_snapshot_returns_dict(self):
        """snapshot() returns a dict of hook registrations."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        snap = hm.snapshot()
        assert isinstance(snap, dict)
        assert snap["turn_end"] == ["Ticker"]

    def test_snapshot_is_deep_copy(self):
        """Mutating the snapshot doesn't affect the manager."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        snap = hm.snapshot()
        snap["turn_end"].append("Injected")
        assert "Injected" not in hm.hooks["turn_end"]

    def test_snapshot_empty_manager(self):
        """snapshot() on empty manager returns empty dict."""
        hm = HookManager()
        assert hm.snapshot() == {}

    def test_restore_replaces_hooks(self):
        """restore() replaces all hook registrations."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        saved = {"passage_enter": ["Logger"]}
        hm.restore(saved)
        assert "turn_end" not in hm.hooks
        assert hm.hooks["passage_enter"] == ["Logger"]

    def test_restore_empty_clears_hooks(self):
        """Restoring empty dict clears all hooks."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.restore({})
        assert hm.hooks == {}

    def test_snapshot_restore_roundtrip(self):
        """Snapshot followed by mutation followed by restore recovers original state."""
        hm = HookManager()
        hm.register("turn_end", "Ticker")
        hm.register("passage_enter", "Logger")

        snap = hm.snapshot()

        # Mutate
        hm.unregister("turn_end", "Ticker")
        hm.register("combat_start", "BattleMusic")

        # Restore
        hm.restore(snap)
        assert hm.hooks["turn_end"] == ["Ticker"]
        assert hm.hooks["passage_enter"] == ["Logger"]
        assert "combat_start" not in hm.hooks


class TestImportPaths:
    """Tests for HookManager import accessibility."""

    def test_import_from_hooks_module(self):
        """HookManager is importable from bardic.runtime.hooks."""
        from bardic.runtime.hooks import HookManager as HM
        assert HM is HookManager

    def test_import_from_runtime_package(self):
        """HookManager is importable from bardic.runtime."""
        from bardic.runtime import HookManager as HM
        assert HM is HookManager
