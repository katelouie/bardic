"""
Runtime engine for executing compiled Bardic stories.
"""

import json
from typing import Any, Dict, Optional

from bardic.runtime.types import PassageOutput
from bardic.runtime.hooks import HookManager
from bardic.runtime.state import StateManager
from bardic.runtime.directives import DirectiveProcessor
from bardic.runtime.executor import CommandExecutor
from bardic.runtime.renderer import ContentRenderer


class BardEngine:
    """
    Runtime engine for Bard stories.

    Loads compiled story JSON and manages story state, navigation and rendering.
    """

    def __init__(
        self,
        story_data: Dict[str, Any],
        context: Optional[dict[str, Any]] = None,
        evaluate_directives: bool = True,
        environment: str = "desktop",
    ):
        """
        Initialize the engine with compiled story data.

        Args:
            story_data: Compiled story dictionary from JSON
            context: Optional dict of user-provided classes/functions
            evaluate_directives: Whether to evaluate render directives
            environment: "desktop" (default) or "browser" — controls
                builtins (__import__ excluded in browser) and enables
                localStorage save/load methods
        """
        self.story = story_data
        self.passages = story_data["passages"]
        self.current_passage_id = None  # Will be set by goto()
        self._previous_passage_id = None  # Tracks the passage we came from (for @prev)
        self.state = {}  # Game state (variables)
        self.hook_manager = HookManager()  # Event hooks (passage callbacks)
        self.state["_inputs"] = {}  # Initialize empty inputs dict (always available)
        self.state["_visits"] = {}  # Track how many times each passage has been visited
        self.state["_turns"] = 0  # Track total number of player choices made
        self._local_scope_stack = []  # Stack of local parameter scopes (NEW for passage params)
        self.used_choices = set()  # Track which one-time choices have been used
        self.context = context or {}
        self.evaluate_directives = evaluate_directives
        self.environment = environment
        self._current_output = None  # Cache for current passage output
        # Key: passage_id, Val: current section 0-index
        self._join_section_index: dict[str, int] = {}  # @join section tracking (which one we're in)

        # State management (undo/redo, save/load, serialization)
        self.state_manager = StateManager(self, max_undo=50)

        # Command execution (variable assignment, Python blocks, imports)
        self.executor = CommandExecutor(
            state=self.state,
            context=self.context,
            local_scope_stack=self._local_scope_stack,
            hook_manager=self.hook_manager,
            environment=self.environment,
        )

        # Directive processing (render directives, arg binding, framework output)
        self.directive_processor = DirectiveProcessor(
            eval_context_provider=self.executor.get_eval_context,
            builtins_provider=self.executor.get_safe_builtins,
            state_provider=lambda: self.state,
            framework_processors={"react": DirectiveProcessor.process_for_react},
        )
        # Backwards compat — some code references self.framework_processors
        self.framework_processors = self.directive_processor.framework_processors

        # Content rendering (expressions, loops, conditionals, choice filtering)
        self.renderer = ContentRenderer(
            eval_context_provider=self.executor.get_eval_context,
            builtins_provider=self.executor.get_safe_builtins,
            state=self.state,
            local_scope_stack=self._local_scope_stack,
            executor=self.executor,
            directive_processor=self.directive_processor,
            passages=self.passages,
            used_choices=self.used_choices,
            join_section_index=self._join_section_index,
            evaluate_directives=self.evaluate_directives,
        )

        # Browser-specific: attach localStorage adapter
        if self.environment == "browser":
            from bardic.runtime.browser import BrowserStorageAdapter

            self._browser_storage = BrowserStorageAdapter(self.state_manager)
            self.save_to_browser = self._browser_storage.save
            self.load_from_browser = self._browser_storage.load
            self.list_browser_saves = self._browser_storage.list_saves
            self.delete_browser_save = self._browser_storage.delete_save

        # Execute Imports first
        self.executor.execute_imports(self.story)

        # Validate
        initial_passage = story_data["initial_passage"]
        if not initial_passage:
            raise ValueError("Story has no initial passage.")

        if initial_passage not in self.passages:
            raise ValueError(f"Initial passage '{initial_passage}' not found in story.")

        # Navigate to initial passage (executes and caches)
        self.goto(initial_passage)

    def _execute_passage(self, passage_id: str) -> Optional[str]:
        """
        Execute a passage's commands (side effects only).

        This is called once when entering a passage to run variable
        assignments and other commands.

        Args:
            passage_id: ID of the passage to execute

        Returns:
            Jump spec if immediate jump found, None otherwise

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError(f"Passage '{passage_id}' not found.")

        passage = self.passages[passage_id]

        # Execute commands (variable assignments, etc.)
        if "execute" in passage:
            self.executor.execute_commands(passage["execute"])

        # Check for immediate jumps in content
        for item in passage.get("content", []):
            if isinstance(item, dict) and item.get("type") == "jump":
                target = item["target"]
                args_str = item.get("args", "")

                # Build passage spec
                if args_str:
                    jump_spec = f"{target}({args_str})"
                else:
                    jump_spec = target

                return jump_spec

        return None

    def _render_passage(self, passage_id: str) -> PassageOutput:
        """Render a passage — delegates to ContentRenderer."""
        return self.renderer.render_passage(passage_id, self.current_passage_id)

    def _render_choice_text(self, choice: dict) -> dict:
        """Render a choice with interpolated text — delegates to ContentRenderer."""
        return self.renderer.render_choice_text(choice)

    def _is_choice_available(self, choice: dict) -> bool:
        """Check if a choice should be shown — delegates to ContentRenderer."""
        return self.renderer.is_choice_available(choice, self.current_passage_id)

    def goto(self, passage_spec: str) -> PassageOutput:
        """
        Navigate to a passage, execute its commands, and cache the output.

        Automatically follows any jumps, combining content and directives from all passages in the
        jump chain. Includes jump loop detection.

        This is the primary navigation method. It:
        1. Changes current_passage_id
        2. Executes passage commands (variables, etc.) - ONCE per passage
        3. Renders the passage
        4. If jump found, follows it (recursively)
        5. Combines content and directives from all jumped passages
        6. Caches the final output
        7. Returns the PassageOutput

        Use this for: Story navigation, jumping between passages

        Args:
            passage_spec: Passage specification - either "PassageName" or "PassageName(args)"

        Returns:
            PassageOutput for the final passage (after following any jumps)

        Raises:
            ValueError: If passage doesn't exist or arguments are invalid
            RuntimeError: If a jump loop is detected
        """
        # Parse passage_spec to extract passage_id and args
        if "(" in passage_spec:
            paren_start = passage_spec.index("(")
            passage_id = passage_spec[:paren_start]

            # Find matching closing paren
            depth = 0
            paren_end = -1
            for i in range(paren_start, len(passage_spec)):
                if passage_spec[i] == "(":
                    depth += 1
                elif passage_spec[i] == ")":
                    depth -= 1
                    if depth == 0:
                        paren_end = i
                        break

            if paren_end == -1:
                raise ValueError(f"Unclosed parenthesis in passage spec: {passage_spec}")

            args_str = passage_spec[paren_start + 1 : paren_end]
        else:
            passage_id = passage_spec
            args_str = ""

        # Resolve @prev to the previous passage ID
        if passage_id == "@prev":
            if self._previous_passage_id is None:
                raise ValueError(
                    "Cannot navigate to @prev: no previous passage exists. "
                    "This typically happens at the start of a story."
                )
            passage_id = self._previous_passage_id

        if passage_id not in self.passages:
            raise ValueError(f"Cannot navigate to unknown passage: '{passage_id}'")

        # Get passage and check for parameters
        passage = self.passages[passage_id]
        params = passage.get("params", [])

        # Handle parameters if present
        if params or args_str:
            # Parse arguments
            eval_context = self._get_eval_context()
            if self._local_scope_stack:
                eval_context.update(self._local_scope_stack[-1])

            safe_builtins = self._get_safe_builtins()

            if args_str:
                arg_dict = self.directive_processor.parse_directive_args(
                    args_str, eval_context, safe_builtins
                )
            else:
                arg_dict = {}

            # Bind arguments to parameters
            try:
                param_values = self.directive_processor.bind_arguments(params, arg_dict)
            except ValueError as e:
                raise ValueError(f"Error calling passage '{passage_id}': {e}")

            # Push local scope
            self._local_scope_stack.append(param_values)

        try:
            accumulated_content = []
            accumulated_directives = []
            visited = set()

            # Reset join section index when visiting a new passage
            self._join_section_index[passage_id] = 0

            # Track passage visit count
            visits = self.state.get("_visits", {})
            visits[passage_id] = visits.get(passage_id, 0) + 1
            self.state["_visits"] = visits

            # Start with the requested passage
            current_id = passage_id

            # Follow jump chain
            while True:
                # Check for jump loops
                if current_id in visited:
                    jump_chain = " -> ".join(visited) + f" -> {current_id}"
                    raise RuntimeError(f"Jump loop detected: {jump_chain}")

                visited.add(current_id)

                # Track previous passage before updating current (for @prev target)
                self._previous_passage_id = self.current_passage_id

                # Update current passage
                self.current_passage_id = current_id

                # Execute commands (side effects happen here, once per passage)
                jump_spec = self._execute_passage(current_id)

                # If there's an immediate jump, handle it (may have args)
                if jump_spec:
                    # Immediate jump found - recursively goto (which may push new scope)
                    jump_output = self.goto(jump_spec)

                    # Combine accumulated content with jump result
                    if accumulated_content:
                        combined = "\n\n".join(accumulated_content + [jump_output.content])
                        jump_output = PassageOutput(
                            content=combined,
                            choices=jump_output.choices,
                            passage_id=jump_output.passage_id,
                            jump_target=None,
                            render_directives=accumulated_directives
                            + jump_output.render_directives,
                            input_directives=jump_output.input_directives,
                        )

                    return jump_output

                # Render the passage
                output = self._render_passage(current_id)

                # Accumulate content
                if output.content:
                    accumulated_content.append(output.content)

                # Accumulate directives
                if output.render_directives:
                    accumulated_directives.extend(output.render_directives)

                # Check for jump (from rendered content, not immediate)
                if output.jump_target:
                    # There's a jump - follow it
                    current_id = output.jump_target
                else:
                    # No jump - we're done
                    break

            # Combine all content from jump chain
            combined_content = "\n\n".join(accumulated_content)

            # Create final output with combined content
            final_output = PassageOutput(
                content=combined_content,
                choices=output.choices,  # Choices from final passage
                passage_id=output.passage_id,  # Final passage ID
                jump_target=None,  # No more jumps
                render_directives=accumulated_directives,
                input_directives=output.input_directives,  # Input directives from final passage
            )

            # Cache the final output
            self._current_output = final_output

            return self._current_output

        finally:
            # Pop local scope if we pushed one
            if params or args_str:
                self._local_scope_stack.pop()

    def current(self) -> PassageOutput:
        """
        Get the current passage output from cache.

        This is a read-only operation that returns the cached output.
        It will never re-execute commands or cause side effects.

        Use this for: Reading current state, displaying passage content

        Returns:
            PassageOutput for the current passage
        """
        assert self._current_output is not None
        return self._current_output

    def choose(self, choice_index: int) -> PassageOutput:
        """
        Make a choice and navigate to the target passage.

        This uses the FILTERED choices from the cached output, ensuring
        the choice index matches what the user actually sees.

        Use this for: Player making choices in the story.

        Tracks one-time choices so they don't appear again.
        Creates an undo snapshot before navigating.
        Clears the redo stack (new choice = new timeline).

        Args:
            choice_index: Index of the choice (0-based, from filtered choices)

        Returns:
            PassageOutput for the new passage

        Raises:
            IndexError: If choice_index is out of range
        """
        # SNAPSHOT before any changes (for undo)
        self.snapshot()

        # Clear the redo stack -- making a new choice creates a new timeline
        self.state_manager.redo_stack.clear()

        # Increment turn counter
        self.state["_turns"] = self.state.get("_turns", 0) + 1

        # Get filtered choices from cached output
        current_output = self.current()
        filtered_choices = current_output.choices

        if choice_index < 0 or choice_index >= len(filtered_choices):
            raise IndexError(
                f"Choice index {choice_index} out of range (0-{len(filtered_choices) - 1})"
            )

        chosen_choice = filtered_choices[choice_index]
        target = chosen_choice["target"]

        # Track this choice if it's one-time (not sticky)
        # Must happen BEFORE @join check so one-time @join choices are tracked too
        if not chosen_choice.get("sticky", True):  # Default to True for backwards compatability
            # Create a unique ID for this choice based on passage + choice index + target
            choice_id = f"{current_output.passage_id}:{chosen_choice['text']}:{target}"
            self.used_choices.add(choice_id)

        # Handle @join choice differently
        if target == "@join":
            return self._execute_join_choice(chosen_choice)

        args_str = chosen_choice.get("args", "")

        # Build passage spec with arguments
        if args_str:
            passage_spec = f"{target}({args_str})"
        else:
            passage_spec = target

        # Navigate to target (executes and caches)
        result = self.goto(passage_spec)

        # Trigger turn end hooks and append any output
        hook_output = self.trigger_event("turn_end")

        if hook_output:
            # Append hook output to the passage content
            result = PassageOutput(
                content=result.content + "\n\n" + hook_output if result.content else hook_output,
                choices=result.choices,
                passage_id=result.passage_id,
                render_directives=result.render_directives,
                input_directives=result.input_directives,
                jump_target=result.jump_target,
            )
            # Update cache with combined output
            self._current_output = result

        return result

    def _execute_join_choice(self, choice: dict) -> PassageOutput:
        """
        Execute a @join choice: run its block, then continue from later @join marker.

        Unlike regular choices which navigate to a new passage, @join choices:

        1. Execute the block's block_execute commands
        2. Render the choice's block_content
        3. Continue from the @join marker in the same passage
        4. Incremement section index for next @join group
        """
        passage_id = self.current_passage_id

        # Block commands are already executed in _render_content

        # Render block content
        block_content_str = ""
        block_directives = []
        block_content = choice.get("block_content", [])
        if block_content:
            block_content_str, _, block_directives = self._render_content(block_content)

        # Get the current section index and find @join marker
        section_idx = self._join_section_index.get(passage_id, 0)
        # Render from the marker onwards
        post_join_output = self._render_from_join_marker(section_idx)
        # Increment section counter for next time
        self._join_section_index[passage_id] = section_idx + 1

        # Combine outputs
        combined_content = block_content_str
        if post_join_output.content:
            if combined_content and not combined_content.endswith("\n"):
                combined_content += "\n"
            combined_content += post_join_output.content

        result = PassageOutput(
            content=combined_content,
            choices=post_join_output.choices,
            passage_id=passage_id,
            render_directives=block_directives + post_join_output.render_directives,
            input_directives=post_join_output.input_directives,
            jump_target=post_join_output.jump_target,
        )

        # Update cache
        self._current_output = result

        # Trigger turn_end hooks
        hook_output = self.trigger_event("turn_end")
        if hook_output:
            result = PassageOutput(
                content=result.content + "\n\n" + hook_output if result.content else hook_output,
                choices=result.choices,
                passage_id=result.passage_id,
                render_directives=result.render_directives,
                input_directives=result.input_directives,
                jump_target=result.jump_target,
            )
            self._current_output = result

        return result

    def _render_from_join_marker(self, section_idx: int) -> PassageOutput:
        """Render from a @join marker — delegates to ContentRenderer."""
        return self.renderer.render_from_join_marker(section_idx, self.current_passage_id)

    def submit_inputs(self, input_data: dict) -> None:
        """
        Submit user input data and store in state.

        Inputs are stored in the special '_inputs' dictionary in state,
        which persists across passage transitions. New inputs with the
        same name overwrite previous values.

        Use this for: Collecting text input from players.

        Args:
            input_data: Dict mapping input names to values (e.g., {"reader_name": "Alice"})
        """
        if "_inputs" not in self.state:
            self.state["_inputs"] = {}

        # Merge new inputs (overwrites duplicates)
        self.state["_inputs"].update(input_data)

    # ── Execution (delegated to CommandExecutor) ──

    def _get_safe_builtins(self) -> dict[str, Any]:
        """Get safe builtins for code execution."""
        return self.executor.get_safe_builtins()

    def _get_eval_context(self) -> dict[str, Any]:
        """Build evaluation context with state, local scope, and special variables."""
        return self.executor.get_eval_context()

    def _render_content(self, content_tokens: list[dict]) -> tuple[str, Optional[str], list[dict]]:
        """Render content tokens — delegates to ContentRenderer."""
        return self.renderer.render_content(content_tokens)

    def _render_loop(self, loop: dict) -> tuple[str, Optional[str], list[dict]]:
        """Render a for-loop — delegates to ContentRenderer."""
        return self.renderer.render_loop(loop)

    def _render_conditional(self, conditional: dict) -> tuple[str, Optional[str], list[dict]]:
        """Render a conditional block — delegates to ContentRenderer."""
        return self.renderer.render_conditional(conditional)

    def _split_format_spec(self, code: str) -> tuple[str, str | None]:
        """Split 'expression:format_spec' — delegates to ContentRenderer."""
        return ContentRenderer.split_format_spec(code)

    # ── Undo/Redo (delegated to StateManager) ──

    @property
    def undo_stack(self):
        """Access undo stack via state manager."""
        return self.state_manager.undo_stack

    @property
    def redo_stack(self):
        """Access redo stack via state manager."""
        return self.state_manager.redo_stack

    def snapshot(self) -> None:
        """Capture current state to the undo stack."""
        self.state_manager.snapshot()

    def undo(self) -> bool:
        """Restore previous state from undo stack."""
        return self.state_manager.undo()

    def redo(self) -> bool:
        """Restore next state from redo stack."""
        return self.state_manager.redo()

    def can_undo(self) -> bool:
        """Check if undo is available (for UI button state)."""
        return self.state_manager.can_undo()

    def can_redo(self) -> bool:
        """Check if redo is available (for UI button state)."""
        return self.state_manager.can_redo()

    def register_hook(self, event: str, passage_id: str) -> None:
        """Register a passage to be called when an event fires.

        Hooks are stored in FIFO order and executed in registration order.
        Duplicate regs are ignored (idempotent)

        Args:
            event: Event name (eg "turn_end")
            passage_id: Passage to execute when event fires
        """
        self.hook_manager.register(event, passage_id)

    def unregister_hook(self, event: str, passage_id: str) -> None:
        """
        Remove a passage from an event's hook list.

        Silently succeeds if the passage wasn't hooked (idempotent).

        Args:
            event: Event name
            passage_id: Passage to remove
        """
        self.hook_manager.unregister(event, passage_id)

    def trigger_event(self, event: str) -> str:
        """
        Execute all passages hooked to an event.

        Passages are executed in FIFO order (first registered, first run).
        Uses a copy of the hook list to safely allow hooks to unregister themselves.

        Args:
            event: Event name to trigger

        Returns:
            Combined text output from all hook passages (for appending to current output)
        """
        # get_handlers returns a copy — safe if hooks unregister during execution
        active_hooks = self.hook_manager.get_handlers(event)
        if not active_hooks:
            return ""

        combined_output = []

        for passage_id in active_hooks:
            if passage_id not in self.passages:
                print(f"Warning: Hooked passage '{passage_id}' not found, skipping")
                continue

            # Execute the passage (runs commands, modifies state)
            self._execute_passage(passage_id)

            # Render the passage (gets text output)
            hook_output = self._render_passage(passage_id)

            # Only append non-empty output
            if hook_output.content.strip():
                combined_output.append(hook_output.content)

        return "\n".join(combined_output)

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
            "current_passage": self.current_passage_id,
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
        return [choice["text"] for choice in self.current().choices]

    def get_choice_targets(self) -> list[str]:
        """
        Get the target passages for the available choices.

        Returns:
            List of target passage IDs
        """
        return [choice["target"] for choice in self.current().choices]

    @classmethod
    def from_file(cls, filepath: str) -> "BardEngine":
        """
        Create an engine by loading a compiled story file.

        Args:
            filepath: Path to compiled JSON story file

        Returns:
            Initialized BardEngine instance
        """
        with open(filepath, "r", encoding="utf-8") as f:
            story_data = json.load(f)

        return cls(story_data)

    def reset_one_time_choices(self) -> None:
        """
        Reset all one-time choices, making them available again.

        Useful for:
        - Restarting the story
        - Implementing a "new game" feature
        - Testing/debugging
        """
        self.used_choices.clear()

    # ── Save/Load (delegated to StateManager) ──

    def save_state(self) -> dict[str, Any]:
        """Serialize engine state to a JSON-compatible dictionary."""
        return self.state_manager.save_state()

    def load_state(self, save_data: dict[str, Any]) -> None:
        """Restore engine state from a saved dictionary."""
        self.state_manager.load_state(save_data)

    def get_save_metadata(self) -> dict[str, Any]:
        """Get metadata about the current save state without full serialization."""
        return self.state_manager.get_save_metadata()
