"""Shared test fixtures for Bardic tests."""

import pytest
import json
import sys
from pathlib import Path
from bardic.compiler.compiler import BardCompiler
from bardic.compiler.parser import parse
from bardic.runtime.engine import BardEngine

# Add fixtures directory to Python path
# This allows test .bard files to do: from game_logic.test_tarot_objects import Card
fixtures_dir = Path(__file__).parent / "fixtures"
if str(fixtures_dir) not in sys.path:
    sys.path.insert(0, str(fixtures_dir))


@pytest.fixture
def simple_story():
    """
    A minimal story for testing basic navigation.

    Returns a compiled story dict (not JSON).
    """
    return {
        "version": "0.1.0",
        "initial_passage": "Start",
        "passages": {
            "Start": {
                "id": "Start",
                "content": [{"type": "text", "value": "You are at the start."}],
                "choices": [{"text": "Go to second passage", "target": "Second"}],
                "execute": [],
            },
            "Second": {
                "id": "Second",
                "content": [
                    {"type": "text", "value": "You reached the second passage!"}
                ],
                "choices": [],
                "execute": [],
            },
        },
    }


@pytest.fixture
def compiler():
    """Return a BardCompiler instance."""
    return BardCompiler()


@pytest.fixture
def compile_string(compiler):
    """
    Fixture that compiles a .bard string to a dict.

    Usage:
        def test_something(compile_string):
            story = compile_string(":: Start\\nHello!")
            assert "Start" in story["passages"]
    """

    def _compile(source: str):
        return compiler.compile_string(source)

    return _compile
