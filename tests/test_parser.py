"""Test the Bardic parser with basic stories."""

import pytest
from bardic.compiler.parser import parse


def test_simple_two_passage_story():
    """Test parsing a simple story with two passages and one choice."""
    # Given: A simple .bard story
    test_story = """
:: Start
Hello world!
This is the first passage.

+ [Go next] -> Next

:: Next
This is the second passage.
"""

    # When: We parse it
    result = parse(test_story)

    # Then: The structure should be correct
    assert result["version"] == "0.1.0"
    assert result["initial_passage"] == "Start"
    assert "Start" in result["passages"]
    assert "Next" in result["passages"]

    # And: The Start passage should have the choice
    start_passage = result["passages"]["Start"]
    assert len(start_passage["choices"]) == 1
    assert start_passage["choices"][0]["text"][0]["value"] == "Go next"
    assert start_passage["choices"][0]["target"] == "Next"

    # And: The content should be tokenized
    assert isinstance(start_passage["content"], list)
