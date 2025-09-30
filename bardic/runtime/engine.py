"""
Runtime engine for executing compiled Bardic stories.
"""
import json
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PassageOutput:
    """
    Output from rendering a passage.

    Attributes:
        content: The rendered text content
        choices: List of available choices
        passage_id: ID of the current passage
    """
    content: str
    choices: List[Dict[str, str]]
    passage_id: str

class BardEngine:
    """
    Runtime engine for Bard stories.

    Loads compiled story JSON and manages story state, nagivation and rendering.
    """

    def __init__(self, story_data: Dict[str, Any]):
        """
        Initialize the engine with compiled story data.

        Args:
            story_data: Compiled story dictionary from JSON
        """
        self.story = story_data
        self.passages = story_data["passages"]
        self.current_passage_id = story_data["initial_passage"]

        # Validate
        if not self.current_passage_id:
            raise ValueError("Story has no initial passage.")

        if self.current_passage_id not in self.passages:
            raise ValueError(f"Initial passage '{self.current_passage_id}' not found in story.")

    def render_passage(self, passage_id: str) -> PassageOutput:
        """
        Render a specific passage.

        Args:
            passage_id: ID of the passage to render.

        Returns:
            PassageOutput with content and choices

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError("Passage '{passage_id}' not found.")

        passage = self.passages[passage_id]

        return PassageOutput(
            content=passage["content"],
            choices=passage["choices"],
            passage_id=passage_id
        )

    def goto(self, passage_id: str) -> None:
        """
        Navigate to a specific passage.

        Args:
            passage_id: ID of the passage to navigate to

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError("Cannot navigate to unknown passage: '{passage_id}'")

        self.current_passage_id = passage_id

    def current(self) -> PassageOutput:
        """
        Get the current passage output.

        Returns:
            PassageOutput for the current passage
        """
        return self.render_passage(self.current_passage_id)

    def choose(self, choice_index: int) -> PassageOutput:
        """
        Make a choice and navigate to the target passage.

        Args:
            choice_index: Index of the choice (0-based)

        Returns:
            PassageOutput for the new passage

        Raises:
            IndexError: If choice_index is out of range
        """
        current_output = self.current()

        if choice_index < 0 or choice_index >= len(current_output.choices):
            raise IndexError(
                f"Choice index {choice_index} out of range "
                f"(0-{len(current_output.choices) - 1})"
            )

        target = current_output.choices[choice_index]["target"]
        self.goto(target)

        return self.current()

    def get_story_info(self) -> Dict[str, Any]:
        """
        Get metadata about loaded story.

        Returns:
            Dictionary with story information
        """
        return {
            "version": self.story.get("version"),
            "passage_count": len(self.passages),
            "initial_passage": self.story["initial_passage"],
            "current_passage": self.current_passage_id
        }

    def has_choices(self) -> bool:
        """
        Check if the current passage has any choices.

        Returns:
            True if there are choices available.
        """
        return len(self.current().choices) > 0

    def is_end(self) -> bool:
        """
        Check if we've reached an ending (no choices).

        Returns:
            True if current passage has no choices.
        """
        return not self.has_choices()

    def get_choice_texts(self) -> list[str]:
        """
        Get just the text of available choices.

        Returns:
            List of choice text strings
        """
        return [choice['text'] for choice in self.current().choices]

    def get_choice_targets(self) -> list[str]:
        """
        Get the target passages for the available choices.

        Returns:
            List of target passage IDs
        """
        return [choice['target'] for choice in self.current().choices]

    @classmethod
    def from_file(cls, filepath: str) -> 'BardEngine':
        """
        Create an engine by loading a compiled story file.

        Args:
            filepath: Path to compiled JSON story file

        Returns:
            Initialized BardEngine instance
        """
        with open(filepath, 'r', encoding="utf-8") as f:
            story_data = json.load(f)

        return cls(story_data)