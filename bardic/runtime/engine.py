"""
Runtime engine for executing compiled Bardic stories.
"""

import sys
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import traceback
import uuid
import ast


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
    render_directives: Optional[List[Dict[str, Any]]] = None

    def __post_init__(self):
        if self.render_directives is None:
            self.render_directives = []


class BardEngine:
    """
    Runtime engine for Bard stories.

    Loads compiled story JSON and manages story state, nagivation and rendering.
    """

    def __init__(
        self,
        story_data: Dict[str, Any],
        context: Optional[dict[str, Any]] = None,
        evaluate_directives: bool = True,
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
        self.evaluate_directives = evaluate_directives
        self._current_output = None  # Cache for current passage output

        # Add more frameworks as needed (eg for unity)
        self.framework_processors = {"react": self._process_for_react}

        # Execute Imports first
        self._execute_imports()

        # Validate
        initial_passage = story_data["initial_passage"]
        if not initial_passage:
            raise ValueError("Story has no initial passage.")

        if initial_passage not in self.passages:
            raise ValueError(f"Initial passage '{initial_passage}' not found in story.")

        # Navigate to initial passage (executes and caches)
        self.goto(initial_passage)

    def _execute_imports(self) -> None:
        """
        Execute import statements from the story.

        Imports are executed in a temporary namespace and then added to the state,
        making them available to all passages.
        """
        import_statements = self.story.get("imports", [])

        if not import_statements:
            return

        # Join all import statemenets
        import_code = "\n".join(import_statements)

        if not import_code.strip():
            return

        try:
            # Add current directory to path for imports
            if "." not in sys.path:
                sys.path.insert(0, ".")
            # Execute imports with safe builtins
            safe_builtins = self._get_safe_builtins()
            import_namespace = {}

            exec(import_code, {"__builtins__": safe_builtins}, import_namespace)

            # Add imported modules/objects to state
            for key, value in import_namespace.items():
                if not key.startswith("_"):
                    self.state[key] = value
        except ImportError as e:
            raise RuntimeError(
                "Failed to import modules:\n"
                f"{import_code}\n\n"
                f"Error: {e}\n\n"
                "Make sure the modules are installed and accessible"
            )
        except Exception as e:
            raise RuntimeError(f"Error executing imports:\n{import_code}\n\nError: {e}")

    def _process_for_react(self, component_name: str, args: dict) -> dict:
        """
        Format directive data for React convenience.

        Converts generic data into React-friendly format:
        - Suggests component name (PascalCase)
        - Generates unique key for list rendering
        - Organizes props cleanly

        Args:
            component_name: The directive name (ex: 'card_detail')
            args: Evaluated arguments dictionary

        Returns:
            React-optimized data structure
        """
        # Convert snake_case to PascalCase for component name
        suggested_component = "".join(
            word.capitalize() for word in component_name.split("_")
        )

        # Clean up props - convert arg_0, arg_1 to more meaningful names if possible
        props = {}
        for key, value in args.items():
            # Keep named arguments as-is
            if not key.startswith("arg_"):
                props[key] = value
            else:  # For positional args, keep them but that's less ideal
                props[key] = value

        return {
            "componentName": suggested_component,
            "key": f"{component_name}_{uuid.uuid4().hex[:8]}",
            "props": props,
        }

    def _parse_directive_args(
        self, args_str: str, eval_context: dict, safe_builtins: dict
    ) -> dict:
        """
        Parse directive arguments into a dictionary.

        Supports both positional and keyword arguments:
        - f(a, b , c) becomes {"arg_0": a, "arg_1": b, "arg_2": c}
        - f(x=1, y=2) becomes {"x": 1, "y": 2}
        - f(a, x=1) becomes {"arg_0": a, "x": 1}

        Args:
            args_str: Argument string from directive
            eval_context: Evaluation context (state + context)
            safe_builtins: Safe builtin functions

        Returns:
            Dictionary of evaluated arguments
        """
        if not args_str.strip():
            return {}

        try:
            # Create a fake function call to parse arguments properly
            # This is part of why this parse function lives in engine, not parser
            fake_call = f"__directive__({args_str})"
            tree = ast.parse(fake_call, mode="eval")
            call_node = tree.body

            result = {}

            # Process positional arguments
            for i, arg in enumerate(call_node.args):
                # Compile and evaluate each argument
                arg_code = compile(ast.Expression(arg), "<directive>", "eval")
                value = eval(arg_code, {"__builtins__": safe_builtins}, eval_context)
                result["arg_{i}"] = value

            # Process keyword arguments
            for keyword in call_node.keywords:
                arg_code = compile(ast.Expression(keyword.value), "<directive>", "eval")
                value = eval(arg_code, {"__builtins__": safe_builtins}, eval_context)
                result[keyword.arg] = value

            return result

        except Exception as e:
            raise ValueError(f"Could not parse directive arguments: {args_str}") from e

    def process_render_directive(self, directive: dict[str, Any]) -> dict[str, Any]:
        """
        Process a render directive based on configuration.

        Creates structured data that frontends can use.

        Two modes:
        1. evaluate_directives=True: Evaluate Python expressions, return data
        2. evaluate_directives=False: Return raw expression, let frontend eval

        Args:
            directive: Parsed directive from content tokens

        Returns:
            Processed directive ready for frontend
        """
        name: str = directive.get("name", "")
        args_str = directive.get("args", "")
        framework_hint = directive.get("framework_hint")

        if self.evaluate_directives:
            # Evaluated mode: Execute python expressions, return data
            try:
                eval_context = {**self.context, **self.state}
                safe_builtins = self._get_safe_builtins()

                # Parse and evaluate arguments
                if args_str:
                    args_dict = self._parse_directive_args(
                        args_str, eval_context, safe_builtins
                    )
                else:
                    args_dict = {}

                # Build base result
                result: dict[str, Any] = {
                    "type": "render_directive",
                    "name": "name",
                    "mode": "evaluated",
                    "data": "args_dict",
                }

                # Add framework-specific preprocessing if requested
                if framework_hint and framework_hint in self.framework_processors:
                    processor = self.framework_processors[framework_hint]
                    result["framework"] = framework_hint
                    result[framework_hint] = processor(name, args_dict)

                return result

            except Exception as e:
                # Error during evaluation
                print(f"Warning: Failed to evaluate render directive '{name}': {e}")
                return {
                    "type": "render_directive",
                    "name": name,
                    "mode": "error",
                    "error": str(e),
                    "raw_args": args_str,
                }
        else:
            # Raw mode: pass expressions to frontend for evaluation
            result = {
                "type": "render_directive",
                "name": name,
                "mode": "raw",
                "raw_args": args_str,
                "state_snapshot": dict(self.state),  # Provide for frontend eval
            }

            if framework_hint:
                result["framework_hint"] = framework_hint

            return result

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
            eval_context = {**self.context, **self.state}
            safe_builtins = self._get_safe_builtins()
            result = eval(condition, {"__builtins__": safe_builtins}, eval_context)
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
            # Create evaluation context with context and state
            eval_context = {**self.context, **self.state}
            safe_builtins = self._get_safe_builtins()

            # Evaluate the expression
            value = eval(expression, {"__builtins__": safe_builtins}, eval_context)

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

    def _get_safe_builtins(self) -> dict[str, Any]:
        """
        Get safe builtins for code execution.

        Returns a dictionary of safe built-in functions that can be
        used in both Python blocks and expressions.
        """
        return {
            # Type constructors
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            # Iteration
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            # Math operations
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            # Sequence operations
            "sorted": sorted,
            "reversed": reversed,
            # Logic
            "any": any,
            "all": all,
            # Debugging
            "print": print,
            # Allow imports
            "__import__": __import__,
        }

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
            safe_builtins = self._get_safe_builtins()
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
        directives = []
        safe_builtins = self._get_safe_builtins()

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
                        value = eval(
                            expr, {"__builtins__": safe_builtins}, eval_context
                        )

                        # Apply format spec
                        result.append(format(value, format_spec))
                    else:
                        # No format spec, just evaluate and convert to string
                        value = eval(
                            code, {"__builtins__": safe_builtins}, eval_context
                        )
                        result.append(str(value))
                except NameError:
                    result.append(f"{{ERROR: undefined variable '{token['code']}'}}")
                except TypeError as e:
                    # Wrong number of arguments, etc.
                    result.append(f"{{ERROR: {token['code']} - {e}}}")
                except AttributeError as e:
                    # Attribute doesn't exist
                    result.append(f"{{ERROR: {token['code']} - {e}}}")
                except Exception as e:
                    # Other errors
                    # Show error in output for debugging
                    result.append(
                        f"{{ERROR: {token['code']} - {type(e).__name__}: {e}}}"
                    )
            elif token["type"] == "render_directive":
                # Process and collect directive (don't render as text)
                processed = self._process_render_directive(token)
                directives.append(processed)
            elif token["type"] == "conditional":
                # Render conditional blocks
                branch_content = self._render_conditional(token)
                result.append(branch_content)
            elif token["type"] == "for_loop":
                # Render loop
                loop_content = self._render_loop(token)
                result.append(loop_content)

        return "".join(result)

    def _render_loop(self, loop: dict) -> str:
        """Render a for-loop by iterating over a collection.

        Args:
            loop: Loop structure with variable, collection and content

        Returns:
            Rendered content from all loop iterations
        """
        variable = loop.get("variable")
        collection_expr = loop.get("collection")
        content = loop.get("content", [])

        if not variable or not collection_expr:
            return ""

        try:
            # Evaluate the collection expression
            eval_context = {**self.context, **self.state}
            safe_builtins = self._get_safe_builtins()
            collection = eval(
                collection_expr, {"__builtins__": safe_builtins}, eval_context
            )

            # Check if variable is tuple unpacking
            variables = [v.strip() for v in variable.split(",")]
            is_tuple_unpack = len(variables) > 1

            # Render content for each item in the collection
            result = []

            for item in collection:
                # Create a new context with the loop variable
                _loop_context = {**self.state, **self.context, variable: item}
                original_values = {}

                try:
                    if is_tuple_unpack:
                        # Tuple unpacking: assign each variable
                        for i, var in enumerate(variables):
                            original_values[var] = self.state.get(var)
                            if isinstance(item, (list, tuple)) and i < len(item):
                                self.state[var] = item[i]
                            else:
                                self.state[var] = None
                    else:
                        # Single variable
                        original_values[variable] = self.state.get(variable)
                        self.state[variable] = item
                except Exception as e:
                    print(f"Warning: Loop variable assignment failed: {e}")
                    print(
                        f"  variable: {variable}, is_tuple: {is_tuple_unpack}, item: {item}"
                    )
                    raise

                # Render the loop body
                iteration_content = self._render_content(content)
                result.append(iteration_content)

                # Restore original values
                for var, original_value in original_values.items():
                    if original_value is not None:
                        self.state[var] = original_value
                    elif var in self.state:
                        del self.state[var]

            return "".join(result)

        except Exception as e:
            error_msg = f"{{ERROR: Loop failed - {e}}}"
            print("Warning: Loop rendering failed")
            print(f"  collection_expr: {collection_expr}")
            print(f"  variable: {variable}")
            print(f"  error: {e}")
            import traceback

            traceback.print_exc()
            return error_msg

    def _render_conditional(self, conditional: dict) -> str:
        """
        Render a conditional block by evaluating conditions and rendering the first true branch.

        Args:
            conditional: Conditional structure with branches
        Returns:
            Rendered content from the first true branch
        """
        eval_context = {**self.context, **self.state}
        safe_builtins = self._get_safe_builtins()

        # Evaluate each branch until we find a true condition
        for branch in conditional.get("branches", []):
            condition = branch.get("condition", "False")

            try:
                # Evaluate the condition
                result = eval(condition, {"__builtins__": safe_builtins}, eval_context)

                if result:
                    # This branch is true -- render its content
                    return self._render_content(branch["content"])

            except Exception as e:
                # If condition fails, skip this branch
                print(f"Warning: Conditional condition failed: {condition} - {e}")
                continue

        # No branch was true - return empty string
        return ""

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
