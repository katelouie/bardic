"""
Shared data structures for the Bardic runtime engine.

Contains PassageOutput (the primary output type for rendered passages)
and GameSnapshot (used by the undo/redo system).
"""

import copy
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bardic.runtime.engine import BardEngine


@dataclass
class PassageOutput:
    """
    Output from rendering a passage.

    Attributes:
        content: The rendered text content
        choices: List of available choices
        passage_id: ID of the current passage
        render_directives: List of render directives for frontend
        input_directives: List of input directives requesting user input
        jump_target: Target passage ID if a jump is encountered, None otherwise
    """

    content: str
    choices: List[Dict[str, str]]
    passage_id: str
    render_directives: Optional[List[Dict[str, Any]]] = None
    input_directives: Optional[List[Dict[str, Any]]] = None
    jump_target: Optional[str] = None

    def __post_init__(self):
        if self.render_directives is None:
            self.render_directives = []
        if self.input_directives is None:
            self.input_directives = []


@dataclass
class GameSnapshot:
    """
    Complete snapshot of game state at a point in time.

    Used by the undo/redo system to capture and restore game state.
    We store full copies (not diffs) for simplicity and reliability.

    Attributes:
        current_passage: The passage ID at the time of snapshot
        previous_passage: The passage we came from (for @prev target)
        state: Deep copy of all game variables
        used_choices: Set of one-time choices that have been used
        hooks: Hook registrations at this point
        join_section_index: @join section tracking
    """

    current_passage: str | None
    previous_passage: str | None
    state: dict[str, Any]
    used_choices: set
    hooks: dict[str, list[str]]
    join_section_index: dict[str, int]

    @classmethod
    def from_engine(cls, engine: "BardEngine") -> "GameSnapshot":
        """Create a snapshot from the current game engine."""
        return cls(
            current_passage=engine.current_passage_id,
            previous_passage=engine._previous_passage_id,
            state=copy.deepcopy(engine.state),
            used_choices=engine.used_choices.copy(),
            hooks=engine.hook_manager.snapshot(),
            join_section_index=copy.deepcopy(engine._join_section_index),
        )

    def restore_to(self, engine: "BardEngine") -> None:
        """Restore this snapshot to the engine."""
        engine.current_passage_id = self.current_passage
        engine._previous_passage_id = self.previous_passage
        engine.state = self.state
        engine.used_choices = self.used_choices
        engine.hook_manager.restore(self.hooks)
        engine._join_section_index = self.join_section_index
