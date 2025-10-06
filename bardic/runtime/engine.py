"""
Runtime engine for executing compiled Bardic stories.
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import traceback


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

    def __init__(
        self, story_data: Dict[str, Any], context: Optional[dict[str, Any]] = None
    ):
        """
        Initialize the engine with compiled story data.

        Args:
            story_data: Compiled story dictionary from JSON
        """
        self.story = story_data
        self.passages = story_data["passages"]
        self.current_passage_id = None  # Will be set by goto()
        self.state = {}  # Game state (variables)
        self.context = context or {}
        self._current_output = None  # Cache for current passage output

        # Validate
        initial_passage = story_data["initial_passage"]
        if not initial_passage:
            raise ValueError("Story has no initial passage.")

        if initial_passage not in self.passages:
            raise ValueError(f"Initial passage '{initial_passage}' not found in story.")

        # Navigate to initial passage (executes and caches)
        self.goto(initial_passage)

    def _execute_passage(self, passage_id: str) -> None:
        """
        Execute a passage's commands (side effects only).

        This is called once when entering a passage to run variable
        assignments and other commands.

        Args:
            passage_id: ID of the passage to execute

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError(f"Passage '{passage_id}' not found.")

        passage = self.passages[passage_id]

        # Execute commands (variable assignments, etc.)
        if "execute" in passage:
            self._execute_commands(passage["execute"])

    def _render_passage(self, passage_id: str) -> PassageOutput:
        """
        Render a passage (pure, no side effects).

        This renders content and filters choices based on current state.
        It does NOT execute commands - that's done by _execute_passage.

        Args:
            passage_id: ID of the passage to render

        Returns:
            PassageOutput with content and choices

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError(f"Passage '{passage_id}' not found.")

        passage = self.passages[passage_id]

        # Render content with current state
        if isinstance(passage["content"], list):
            # New format: list of tokens
            content = self._render_content(passage["content"])
        else:
            # Old format: plain string (backwards compatible)
            content = passage["content"]

        # Filter choices based on conditions
        available_choices = []
        for choice in passage["choices"]:
            if self._is_choice_available(choice):
                available_choices.append(choice)

        return PassageOutput(
            content=content,
            choices=available_choices,
            passage_id=passage_id,
        )

    def _is_choice_available(self, choice: dict) -> bool:
        """Check if a choice should be shown based on its condition."""
        condition = choice.get("condition")

        # No condition = always available
        if not condition:
            return True

        # Else, evaluate the condition
        try:
            eval_context = dict(self.state)
            result = eval(condition, {"__builtins__": {}}, eval_context)
            return bool(result)
        except Exception as e:
            # If condition fails to evaluate, hide the choice
            print(f"Warning: Choice condition failed: {condition} - {e}")
            return False

    def goto(self, passage_id: str) -> PassageOutput:
        """
        Navigate to a passage, execute its commands, and cache the output.

        This is the primary navigation method. It:
        1. Changes current_passage_id
        2. Executes passage commands (variables, etc.) - ONCE
        3. Renders and caches the output
        4. Returns the PassageOutput

        Use this for: Story navigation, jumping between passages

        Args:
            passage_id: ID of the passage to navigate to

        Returns:
            PassageOutput for the new passage

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError(f"Cannot navigate to unknown passage: '{passage_id}'")

        # Update current passage
        self.current_passage_id = passage_id

        # Execute commands (side effects happen here, once)
        self._execute_passage(passage_id)

        # Render and cache the output
        self._current_output = self._render_passage(passage_id)

        return self._current_output

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

        Use this for: Player making choices in the story

        Args:
            choice_index: Index of the choice (0-based, from filtered choices)

        Returns:
            PassageOutput for the new passage

        Raises:
            IndexError: If choice_index is out of range
        """
        # Get filtered choices from cached output
        current_output = self.current()
        filtered_choices = current_output.choices

        if choice_index < 0 or choice_index >= len(filtered_choices):
            raise IndexError(
                f"Choice index {choice_index} out of range (0-{len(filtered_choices) - 1})"
            )

        target = filtered_choices[choice_index]["target"]

        # Navigate to target (executes and caches)
        return self.goto(target)

    def _execute_commands(self, commands: list[dict]) -> None:
        """Execute passage commands (variable assignments, python blocks, etc)"""
        for cmd in commands:
            if cmd["type"] == "set_var":
                self._execute_set_var(cmd)
            elif cmd["type"] == "python_block":
                self._execute_python_block(cmd)

    def _execute_set_var(self, cmd: dict) -> None:
        """Execute a variable assignment."""
        var_name = cmd["var"]
        expression = cmd["expression"]

        # Try to evaluate the expression
        try:
            # Create evaluation context with current state
            eval_context = dict(self.state)

            # Evaluate the expression
            # Use a restricted eval for safety (no __builtins__)
            value = eval(expression, {"__builtins__": {}}, eval_context)

            # Store in state
            self.state[var_name] = value

        except NameError as e:
            # Variable doesn't exist
            raise RuntimeError(
                f"Variable assignment failed: {var_name} = {expression}\n"
                f"  Undefined variable in expression: {e}\n"
                f"  Current state: {list(self.state.keys())}"
            )

        except Exception as _e:
            # If evaluation fails, store as literal
            # This handles simple cases like name = "Hero"
            try:
                # Try to parse as literal
                value = self._parse_literal(expression)
                self.state[var_name] = value
            except Exception as e:
                raise RuntimeError(
                    f"Variable assignment failed: {var_name} = {expression}\n"
                    f"  Error: {e}\n"
                    f"  Expression could not be evaluated or parsed as literal"
                )

    def _execute_python_block(self, cmd: dict) -> None:
        """
        Execute a python code block.

        The code block has access to:
        - self.state (current game state)
        - Any context provided at engine initialization

        Args:
            cmd: Command dictionary with 'code' key
        """
        code = cmd["code"]

        try:
            # Create execution context with safe builtins
            safe_builtins = {
                # Allow these builtins
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "any": any,
                "all": all,
                "print": print,  # For debugging
                # Allow safe imports
                "__import__": __import__,
            }
            # Merge state and context for execution
            exec_context = {**self.context, **self.state}

            # Execute the python code
            exec(code, {"__builtins__": safe_builtins}, exec_context)

            # Update state with any new/modified variables
            # Only update variables that were changed or added
            # Update state but not context -- context is read-only!!
            for key, value in exec_context.items():
                if (
                    not key.startswith("_") and key not in self.context
                ):  # Skip internal variables
                    self.state[key] = value

        except SyntaxError as e:
            # Syntax error - show the problematic line
            raise RuntimeError(
                "Syntax error in Python block:\n"
                f"Line {e.lineno}: {e.text}\n"
                f"  {e.msg}\n\n"
                f"Full code:\n{code}"
            )

        except NameError as e:
            # Undefined variable
            raise RuntimeError(
                f"Undefined variable in Python block: {e}\n"
                "Available variables: {list(exec_context.keys())}\n\n"
                f"Code:\n{code}"
            )

        except Exception as e:
            # Other runtime error
            raise RuntimeError(
                f"Error executing Python block:\n"
                f"  {type(e).__name__}: {e}\n\n"
                f"Traceback:\n{traceback.format_exc()}\n"
                f"Code:\n{code}"
            )

    def _parse_literal(self, value_str: str) -> Any:
        """Parse a literal value."""
        value = value_str.strip()

        # Boolean
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # String (remove quotes)
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            return value[1:-1]

        return value

    def _render_content(self, content_tokens: list[dict]) -> str:
        """Render content with variable substitution and format specifiers."""
        result = []

        for token in content_tokens:
            if token["type"] == "text":
                result.append(token["value"])
            elif token["type"] == "expression":
                # Evaluate the expression (with optional format spec)
                try:
                    # Merge context and state for evaluation
                    eval_context = {**self.context, **self.state}
                    code = token["code"]

                    # Check for format specifier (e.g., "average:.1f")
                    if ":" in code and not any(
                        op in code for op in ["==", "!=", "<=", ">=", "::"]
                    ):
                        # Split expression and format spec
                        # Find the first : that's not part of an operator
                        colon_idx = code.find(":")
                        expr = code[:colon_idx].strip()
                        format_spec = code[colon_idx + 1 :].strip()

                        # Evaluate the expression
                        value = eval(expr, {"__builtins__": {}}, eval_context)

                        # Apply format spec
                        result.append(format(value, format_spec))
                    else:
                        # No format spec, just evaluate and convert to string
                        value = eval(code, {"__builtins__": {}}, eval_context)
                        result.append(str(value))
                except NameError:
                    result.append(f"{{ERROR: undefined variable '{token['code']}'}}")
                except Exception as e:
                    # Show error in output for debugging
                    result.append(
                        f"{{ERROR: {token['code']} - {type(e).__name__}: {e}}}"
                    )

        return "".join(result)

    def _split_format_spec(self, code: str) -> tuple[str, str | None]:
        """Split 'expression:format_spec' at the rightmost valid colon."""
        # Your simple version for now
        if ":" in code and not any(op in code for op in ["==", "!=", "<=", ">=", "::"]):
            colon_idx = code.rfind(":")  # Use rfind for rightmost
            expr = code[:colon_idx].strip()
            spec = code[colon_idx + 1 :].strip()
            return expr, spec
        return code, None

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
