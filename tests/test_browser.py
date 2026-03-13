"""Tests for bardic.runtime.browser — BrowserStorageAdapter and environment parameter."""

from unittest.mock import MagicMock, patch

from bardic.runtime.executor import CommandExecutor
from bardic.runtime.hooks import HookManager
from bardic.runtime.browser import BrowserStorageAdapter


def _make_executor(environment="desktop", state=None):
    """Create a CommandExecutor with the given environment."""
    state = state if state is not None else {}
    return CommandExecutor(
        state=state,
        context={},
        local_scope_stack=[],
        hook_manager=HookManager(),
        environment=environment,
    )


class TestEnvironmentParameter:
    """Tests for the environment parameter on CommandExecutor."""

    def test_desktop_includes_import(self):
        ex = _make_executor(environment="desktop")
        builtins = ex.get_safe_builtins()
        assert "__import__" in builtins

    def test_browser_excludes_import(self):
        ex = _make_executor(environment="browser")
        builtins = ex.get_safe_builtins()
        assert "__import__" not in builtins

    def test_browser_includes_safe_builtins(self):
        """Browser mode should still have all safe builtins."""
        ex = _make_executor(environment="browser")
        builtins = ex.get_safe_builtins()
        assert builtins["int"] is int
        assert builtins["str"] is str
        assert builtins["len"] is len
        assert builtins["print"] is print
        assert builtins["sum"] is sum
        assert builtins["range"] is range
        assert builtins["hasattr"] is hasattr
        assert builtins["getattr"] is getattr

    def test_default_environment_is_desktop(self):
        ex = CommandExecutor(state={}, context={}, local_scope_stack=[], hook_manager=HookManager())
        assert ex.environment == "desktop"
        builtins = ex.get_safe_builtins()
        assert "__import__" in builtins


class TestBrowserStorageAdapter:
    """Tests for BrowserStorageAdapter structure (no actual localStorage)."""

    def test_adapter_wraps_state_manager(self):
        mock_sm = MagicMock()
        adapter = BrowserStorageAdapter(mock_sm)
        assert adapter.state_manager is mock_sm

    def test_save_calls_state_manager(self):
        """Verify save delegates to state_manager.save_state()."""
        mock_sm = MagicMock()
        mock_sm.save_state.return_value = {"current_passage_id": "Start", "state": {}}
        adapter = BrowserStorageAdapter(mock_sm)

        # Mock localStorage
        mock_storage = MagicMock()
        with patch("bardic.runtime.browser._get_storage", return_value=mock_storage):
            adapter.save("test_slot")

        mock_sm.save_state.assert_called_once()
        mock_storage.setItem.assert_called_once()
        # Check the key format
        call_args = mock_storage.setItem.call_args
        assert call_args[0][0] == "bardic_save_test_slot"

    def test_load_calls_state_manager(self):
        """Verify load delegates to state_manager.load_state()."""
        mock_sm = MagicMock()
        adapter = BrowserStorageAdapter(mock_sm)

        mock_storage = MagicMock()
        mock_storage.getItem.return_value = '{"current_passage_id": "Start", "state": {}}'
        with patch("bardic.runtime.browser._get_storage", return_value=mock_storage):
            result = adapter.load("test_slot")

        assert result is True
        mock_sm.load_state.assert_called_once()

    def test_load_returns_false_when_no_save(self):
        """Verify load returns False when slot doesn't exist."""
        mock_sm = MagicMock()
        adapter = BrowserStorageAdapter(mock_sm)

        mock_storage = MagicMock()
        mock_storage.getItem.return_value = None
        with patch("bardic.runtime.browser._get_storage", return_value=mock_storage):
            result = adapter.load("nonexistent")

        assert result is False
        mock_sm.load_state.assert_not_called()

    def test_list_saves_filters_prefix(self):
        """Verify list_saves strips the 'bardic_save_' prefix."""
        mock_sm = MagicMock()
        adapter = BrowserStorageAdapter(mock_sm)

        mock_storage = MagicMock()
        mock_storage.length = 3
        mock_storage.key.side_effect = ["bardic_save_auto", "other_key", "bardic_save_slot1"]
        with patch("bardic.runtime.browser._get_storage", return_value=mock_storage):
            saves = adapter.list_saves()

        assert saves == ["auto", "slot1"]

    def test_delete_save_removes_key(self):
        """Verify delete_save calls removeItem with correct key."""
        mock_sm = MagicMock()
        adapter = BrowserStorageAdapter(mock_sm)

        mock_storage = MagicMock()
        with patch("bardic.runtime.browser._get_storage", return_value=mock_storage):
            adapter.delete_save("old_save")

        mock_storage.removeItem.assert_called_once_with("bardic_save_old_save")

    def test_save_default_slot(self):
        """Verify default slot name is 'autosave'."""
        mock_sm = MagicMock()
        mock_sm.save_state.return_value = {"state": {}}
        adapter = BrowserStorageAdapter(mock_sm)

        mock_storage = MagicMock()
        with patch("bardic.runtime.browser._get_storage", return_value=mock_storage):
            adapter.save()

        call_args = mock_storage.setItem.call_args
        assert call_args[0][0] == "bardic_save_autosave"


class TestEngineEnvironmentIntegration:
    """Tests for BardEngine environment parameter."""

    def test_engine_default_environment(self):
        """Default environment should be desktop."""
        from bardic.runtime.engine import BardEngine
        from bardic.compiler.compiler import BardCompiler

        story = BardCompiler().compile_string(":: Start\nHello")
        engine = BardEngine(story)
        assert engine.environment == "desktop"
        assert not hasattr(engine, "save_to_browser")

    def test_engine_browser_environment_attaches_methods(self):
        """Browser environment should attach localStorage methods."""
        from bardic.runtime.engine import BardEngine
        from bardic.compiler.compiler import BardCompiler

        story = BardCompiler().compile_string(":: Start\nHello")
        engine = BardEngine(story, environment="browser")
        assert engine.environment == "browser"
        assert hasattr(engine, "save_to_browser")
        assert hasattr(engine, "load_from_browser")
        assert hasattr(engine, "list_browser_saves")
        assert hasattr(engine, "delete_browser_save")
        assert callable(engine.save_to_browser)

    def test_browser_engine_no_import_in_builtins(self):
        """Browser engine's executor should not have __import__."""
        from bardic.runtime.engine import BardEngine
        from bardic.compiler.compiler import BardCompiler

        story = BardCompiler().compile_string(":: Start\nHello")
        engine = BardEngine(story, environment="browser")
        builtins = engine.executor.get_safe_builtins()
        assert "__import__" not in builtins


class TestImportPaths:
    """Tests for browser module import accessibility."""

    def test_import_from_browser_module(self):
        from bardic.runtime.browser import BrowserStorageAdapter as BSA

        assert BSA is BrowserStorageAdapter

    def test_import_from_runtime_package(self):
        from bardic.runtime import BrowserStorageAdapter as BSA

        assert BSA is BrowserStorageAdapter
