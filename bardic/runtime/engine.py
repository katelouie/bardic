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
from datetime import datetime


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
        self.state['_inputs'] = {}  # Initialize empty inputs dict (always available)
        self.used_choices = set()  # Track which one-time choices have been used
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

        Classes are automatically registered in context for serialization.
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

            # Add imported modules/objects to state AND auto-register classes
            for key, value in import_namespace.items():
                if not key.startswith("_"):
                    # Always add to state (for use in stories)
                    self.state[key] = value

                    # Auto-register classes for serialization
                    if isinstance(value, type):
                        # It's a class -- add to context for save/load
                        self.context[key] = value
                        print(f"Auto-registered class for serialization: {key}")

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
                result[f"arg_{i}"] = value

            # Process keyword arguments
            for keyword in call_node.keywords:
                arg_code = compile(ast.Expression(keyword.value), "<directive>", "eval")
                value = eval(arg_code, {"__builtins__": safe_builtins}, eval_context)
                result[keyword.arg] = value

            return result

        except Exception as e:
            raise ValueError(f"Could not parse directive arguments: {args_str}") from e

    def _process_render_directive(self, directive: dict[str, Any]) -> dict[str, Any]:
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
                    "name": name,
                    "mode": "evaluated",
                    "data": args_dict,
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

        If a jump is encountered, returns jump_target in output.
        The CALLER decides whether to follow the jump.

        Args:
            passage_id: ID of the passage to render

        Returns:
            PassageOutput with content, choices and directives

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self.passages:
            raise ValueError(f"Passage '{passage_id}' not found.")

        passage = self.passages[passage_id]

        # Render content with current state
        if isinstance(passage["content"], list):
            # New format: list of tokens
            content, jump_target, directives = self._render_content(passage["content"])
        else:
            # Old format: plain string (backwards compatible)
            content = passage["content"]
            jump_target = None
            directives = []

        # Separate choice/input directives from render directives
        # (all are collected in the directives list by _render_content)
        choice_directives = []
        input_directives = []
        render_directives = []
        for directive in directives:
            if directive.get("type") == "choice":
                choice_directives.append(directive)
            elif directive.get("type") == "input":
                input_directives.append(directive)
            else:
                render_directives.append(directive)

        # Merge conditional/loop choices with passage-level choices
        all_choices = list(passage["choices"]) + choice_directives

        # Filter merged choices based on conditions AND render text with interpolation
        available_choices = []
        for choice in all_choices:
            if self._is_choice_available(choice):
                # Render choice text (interpolates variables)
                rendered_choice = self._render_choice_text(choice)
                available_choices.append(rendered_choice)

        # Also include passage-level input directives (for backwards compatibility)
        passage_level_inputs = passage.get("input_directives", [])
        input_directives.extend(passage_level_inputs)

        return PassageOutput(
            content=content,
            choices=available_choices,
            passage_id=passage_id,
            jump_target=jump_target,  # Just report it here, don't follow in this fn.
            render_directives=render_directives,
            input_directives=input_directives,
        )

    def _render_choice_text(self, choice: dict) -> dict:
        """
        Render a choice with interpolated text.

        Handles both new format (tokenized text) and old format (string text)
        for backward compatibility.

        Args:
            choice: Choice dict with text field (string or token list)

        Returns:
            Choice dict with rendered text as string
        """
        choice_text = choice["text"]

        # Check if text is already a string (old format - backward compatible)
        if isinstance(choice_text, str):
            rendered_text = choice_text
        else:
            # New format - token list, render it
            rendered_text, _, _ = self._render_content(choice_text)

        # Return choice with rendered text
        return {
            **choice,
            "text": rendered_text
        }

    def _is_choice_available(self, choice: dict) -> bool:
        """Check if a choice should be shown based on its condition and if used (1-time).

        A choice is available if:
        1. Its condition (if any) evaluates to True
        2. It's sticky (+ ) or it hasn't been used yet (* )
        """
        # Check if one-time choice has already been used
        sticky = choice.get("sticky", True)
        if not sticky:
            # This is a one-time choice - check if used
            choice_id = f"{self.current_passage_id}:{choice['text']}:{choice['target']}"
            if choice_id in self.used_choices:
                return False  # Already used, hide it

        # Check condition (if present)
        condition = choice.get("condition")

        # No condition = always available (if not used)
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
            passage_id: ID of the passage to navigate to

        Returns:
            PassageOutput for the final passage (after following any jumps)

        Raises:
            ValueError: If passage_id doesn't exist
            RuntimeError: If a jump loop is detected
        """
        if passage_id not in self.passages:
            raise ValueError(f"Cannot navigate to unknown passage: '{passage_id}'")

        accumulated_content = []
        accumulated_directives = []
        visited = set()

        # Start with the requested passage
        current_id = passage_id

        # Follow jump chain
        while True:
            # Check for jump loops
            if current_id in visited:
                jump_chain = " -> ".join(visited) + f" -> {current_id}"
                raise RuntimeError(f"Jump loop detected: {jump_chain}")

            visited.add(current_id)

            # Update current passage
            self.current_passage_id = current_id

            # Execute commands (side effects happen here, once per passage)
            self._execute_passage(current_id)

            # Render the passage
            output = self._render_passage(current_id)

            # Accumulate content
            if output.content:
                accumulated_content.append(output.content)

            # Accumulatve directives
            if output.render_directives:
                accumulated_directives.extend(output.render_directives)

            # Check for jump
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

        chosen_choice = filtered_choices[choice_index]
        target = chosen_choice["target"]

        # Track this choice if it's one-time (not sticky)
        if not chosen_choice.get(
            "sticky", True
        ):  # Default to True for backwards compatability
            # Create a unique ID for this choice based on passage + choice index + target
            choice_id = f"{current_output.passage_id}:{chosen_choice['text']}:{target}"
            self.used_choices.add(choice_id)

        # Navigate to target (executes and caches)
        return self.goto(target)

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
        if '_inputs' not in self.state:
            self.state['_inputs'] = {}

        # Merge new inputs (overwrites duplicates)
        self.state['_inputs'].update(input_data)

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

    def _render_content(
        self, content_tokens: list[dict]
    ) -> tuple[str, Optional[str], list[dict]]:
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
            elif token["type"] == "inline_conditional":
                # Evaluate inline conditional: {condition ? truthy | falsy}
                try:
                    eval_context = {**self.context, **self.state}
                    safe_builtins = self._get_safe_builtins()

                    # Evaluate the condition
                    condition_result = eval(
                        token["condition"],
                        {"__builtins__": safe_builtins},
                        eval_context
                    )

                    # Choose branch based on condition (truthy or falsy)
                    branch_text = token["truthy"] if condition_result else token["falsy"]

                    # The branch might be:
                    # 1. Plain text: "Healthy"
                    # 2. An expression: "{func()}"
                    # 3. Empty: ""

                    if not branch_text:
                        # Empty branch - add nothing
                        pass
                    elif branch_text.startswith("{") and branch_text.endswith("}"):
                        # Branch contains an expression - evaluate it
                        branch_expr = branch_text[1:-1]  # Remove { }

                        # Check for format spec in the branch expression
                        if ":" in branch_expr and not any(
                            op in branch_expr for op in ["==", "!=", "<=", ">=", "::"]
                        ):
                            # Has format spec
                            colon_idx = branch_expr.find(":")
                            expr = branch_expr[:colon_idx].strip()
                            format_spec = branch_expr[colon_idx + 1:].strip()

                            value = eval(expr, {"__builtins__": safe_builtins}, eval_context)
                            result.append(format(value, format_spec))
                        else:
                            # No format spec
                            value = eval(branch_expr, {"__builtins__": safe_builtins}, eval_context)
                            result.append(str(value))
                    else:
                        # Plain text - add as-is
                        result.append(branch_text)

                except Exception as e:
                    # Error evaluating inline conditional
                    result.append(f"{{ERROR: inline conditional - {e}}}")
            elif token["type"] == "render_directive":
                # Process and collect directive (don't render as text)
                processed = self._process_render_directive(token)
                directives.append(processed)
            elif token["type"] == "input":
                # Collect input directive (don't render as text)
                directives.append(token)
            elif token["type"] == "python_block":
                # Execute Python block (modifies state, produces no text output)
                # This happens during rendering, so it only runs if its branch/loop is active
                self._execute_python_block(token)
                # Don't append anything to result - Python blocks don't generate text
            elif token["type"] == "conditional":
                # Render conditional blocks
                branch_content, jump_target, branch_directives = (
                    self._render_conditional(token)
                )
                result.append(branch_content)
                directives.extend(branch_directives)  # Collect directives from branch
                # If jump was found in the conditional, stop and return
                if jump_target:
                    return "".join(result), jump_target, directives
            elif token["type"] == "for_loop":
                # Render loop
                loop_content, jump_target, loop_directives = self._render_loop(token)
                result.append(loop_content)
                directives.extend(loop_directives)  # Collect directives from loop
                # If jump was found in the loop, stop and return
                if jump_target:
                    return "".join(result), jump_target, directives
            elif token["type"] == "jump":
                # Jump found - stop rendering HERE and return the target
                return "".join(result), token["target"], directives

        return "".join(result), None, directives

    def _render_loop(self, loop: dict) -> tuple[str, Optional[str], list[dict]]:
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
            return "", None, []

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
            all_directives = []  # Collect directives from all iterations

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
                iteration_content, jump_target, iteration_directives = (
                    self._render_content(content)
                )
                result.append(iteration_content)
                all_directives.extend(iteration_directives)  # Collect directives

                # Add loop choices for this iteration (if any)
                # IMPORTANT: Render choice text NOW while loop variable is in scope!
                if "choices" in loop:
                    for choice in loop["choices"]:
                        # Render choice text with current loop variable
                        rendered_choice = self._render_choice_text(choice)
                        all_directives.append({"type": "choice", **rendered_choice})

                # Restore original values
                for var, original_value in original_values.items():
                    if original_value is not None:
                        self.state[var] = original_value
                    elif var in self.state:
                        del self.state[var]

                # If a jump was found, stop the loop and return
                if jump_target:
                    return "".join(result), jump_target, all_directives

            return "".join(result), None, all_directives

        except Exception as e:
            error_msg = f"{{ERROR: Loop failed - {e}}}"
            print("Warning: Loop rendering failed")
            print(f"  collection_expr: {collection_expr}")
            print(f"  variable: {variable}")
            print(f"  error: {e}")
            import traceback

            traceback.print_exc()
            return error_msg, None

    def _render_conditional(
        self, conditional: dict
    ) -> tuple[str, Optional[str], list[dict]]:
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
                    content, jump_target, directives = self._render_content(branch["content"])

                    # Add branch choices to directives (if any)
                    if "choices" in branch:
                        for choice in branch["choices"]:
                            directives.append({"type": "choice", **choice})

                    return content, jump_target, directives

            except Exception as e:
                # If condition fails, skip this branch
                print(f"Warning: Conditional condition failed: {condition} - {e}")
                continue

        # No branch was true - return empty string
        return "", None, []

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

    def reset_one_time_choices(self) -> None:
        """
        Reset all one-time choices, making them available again.

        Useful for:
        - Restarting the story
        - Implementing a "new game" feature
        - Testing/debugging
        """
        self.used_choices.clear()

    def save_state(self) -> dict[str, Any]:
        """
        Serialize engine state to a dictionary that can be saved to JSON.

        Returns a complete snapshot of the current game state including:
        - Current passage ID
        - All variables in state
        - Used one-time choices
        - Story metadata for validation

        Returns:
            Dictionary containing all state needed to restore the game

        Example:
            state = engine.save_state()
            with open('save.json', 'w') as f:
                json.dump(state, f)
        """
        # Get metadata from story
        story_metadata = self.story.get("metadata", {})

        return {
            "version": "0.1.0",  # Save format version
            "story_version": story_metadata.get("version", "unknown"),
            "story_name": story_metadata.get("title", "unknown"),
            "story_id": story_metadata.get("story_id", "unknown"),
            "timestamp": self._get_timestamp(),
            "current_passage_id": self.current_passage_id,
            "state": self._serialize_state(self.state),
            "used_choices": list(self.used_choices),
            "metadata": {
                "passage_count": len(self.passages),
                "initial_passage": self.story["initial_passage"],
            },
        }

    def load_state(self, save_data: dict[str, Any]) -> None:
        """
        Restore engine state from a saved dictionary.

        Validates the save data before loading to ensure compatibility.

        Args:
            save_data: Dictionary from save_state()

        Raises:
            ValueError: If save data is invalid or incompatible

        Example:
            with open('save.json') as f:
                save_data = json.load(f)
            engine.load_state(save_data)
        """
        # Validate save format
        if not isinstance(save_data, dict):
            raise ValueError("Save data must be a dictionary")

        if "version" not in save_data:
            raise ValueError("Save data missing version field")

        # Validate story compatibility using metadata
        story_metadata = self.story.get("metadata", {})

        saved_story_name = save_data.get("story_name", "unknown")
        current_story_name = story_metadata.get("title", "unknown")

        saved_story_id = save_data.get("story_id", "unknown")
        current_story_id = story_metadata.get("story_id", "unknown")

        # Check both story_id (primary) and story_name (secondary) for compatibility
        if saved_story_id != "unknown" and current_story_id != "unknown":
            if saved_story_id != current_story_id:
                print(
                    f"Warning: Save is from a different story ID: '{saved_story_id}' vs '{current_story_id}'"
                )
        elif saved_story_name != current_story_name and saved_story_name != "unknown":
            print(
                f"Warning: Save is from a different story: '{saved_story_name}' vs '{current_story_name}'"
            )

        # Validate passage exists
        target_passage = save_data.get("current_passage_id", "Start")
        if target_passage not in self.passages:
            raise ValueError(
                f"Save data references unknown passage: '{target_passage}'\n"
                f"Available passages: {', '.join(sorted(self.passages.keys())[:5])}..."
            )

        # Restore state
        self.state = self._deserialize_state(save_data.get("state", {}))
        self.used_choices = set(save_data.get("used_choices", []))

        # Navigate to saved passage (this re-renders with restored state)
        self.goto(target_passage)

    def _serialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Serialize state dictionary for JSON storage.

        Delegates all value serialization to _serialize_value for consistency.
        This ensures custom serialization methods and recursive handling work
        for all values, regardless of nesting level.

        Args:
            state: Raw state dictionary

        Returns:
            JSON-serializable dictionary
        """
        serialized = {}
        for key, value in state.items():
            serialized[key] = self._serialize_value(value)
        return serialized

    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value for JSON storage.

        Priority order:
        0. Skip classes/types (they shouldn't be in save files)
        1. Check for custom to_save_dict() method (explicit serialization)
        2. Try direct JSON serialization (primitives)
        3. Collections (lists, tuples, dicts) - recurse
        4. Objects with __dict__
        5. Fallback to string representation
        """
        # Priority 0: Skip classes/types - they shouldn't be serialized
        if isinstance(value, type):
            # This is a class definition, not an instance - skip it
            return None

        # Priority 1: Custom serialization method
        if hasattr(value, "to_save_dict") and callable(getattr(value, "to_save_dict")):
            return {
                "_type": type(value).__name__,
                "_module": type(value).__module__,
                "_data": value.to_save_dict(),
                "_custom": True,  # Flag that this used custom serialization
            }

        # Priority 2: Direct JSON serialization (primitives)
        try:
            json.dumps(value)
            return value
        except (TypeError, ValueError):
            pass

        # Priority 3: Collections - recurse for nested structures
        if isinstance(value, list):
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, tuple):
            # Store tuples as lists (JSON doesn't have tuples)
            return [self._serialize_value(v) for v in value]
        elif isinstance(value, dict):
            # Recurse through dict values
            return {k: self._serialize_value(v) for k, v in value.items()}

        # Priority 4: Object with __dict__
        if hasattr(value, "__dict__"):
            return {
                "_type": type(value).__name__,
                "_module": type(value).__module__,
                "_data": {
                    # Recurse for nested objects in attributes
                    k: self._serialize_value(v)
                    for k, v in value.__dict__.items()
                    if not k.startswith("_")
                },
            }

        # Priority 5: Fallback to string
        print(f"Warning: Serializing {type(value).__name__} as string representation")
        return {"_type": "string_repr", "_value": str(value)}

    def _deserialize_state(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Deserialize state dictionary from JSON storage.

        Delegates all value deserialization to _deserialize_value for consistency.
        This ensures custom deserialization methods and recursive handling work
        for all values, regardless of nesting level.

        Args:
            state: Serialized state dictionary

        Returns:
            Restored state dictionary
        """
        deserialized = {}
        for key, value in state.items():
            deserialized[key] = self._deserialize_value(value)
        return deserialized

    def _deserialize_value(self, value: Any) -> Any:
        """Deserialize a single value from JSON storage.

        Priority Order:
        1. Handle primitives (return as-is)
        2. Handle collections (recurse)
        3. Handle objects with custom from_save_dict() (explicit deserialization)
        4. Handle objects with __new__ + __dict__ (automatic deserialization)
        5. Return as dict if class not available
        """
        # Priority 1: Primitives - return as-is
        if not isinstance(value, (dict, list)):
            return value

        # Priority 2: Collections - recurse
        if isinstance(value, list):
            return [self._deserialize_value(v) for v in value]

        # Priority 3-5: Objects with _type metadata
        if not isinstance(value, dict) or "_type" not in value:
            # Plain dict without _type - recurse through values
            if isinstance(value, dict):
                return {k: self._deserialize_value(v) for k, v in value.items()}
            return value

        obj_type = value["_type"]
        obj_data = value.get("_data", {})

        # Special case: string representation
        if obj_type == "string_repr":
            return value.get("_value", "")

        # Try to get class from context
        if obj_type not in self.context:
            # Class not available - recurse through data dict
            print(f"Warning: Class '{obj_type}' not in context, keeping as dict")
            return {k: self._deserialize_value(v) for k, v in obj_data.items()}

        cls = self.context[obj_type]

        # Priority 3: Custom deserialization method
        if hasattr(cls, "from_save_dict") and callable(getattr(cls, "from_save_dict")):
            try:
                return cls.from_save_dict(obj_data)
            except Exception as e:
                print(f"Warning: Custom deserialization failed for {obj_type}: {e}")
                # Fall through to automatic method

        # Priority 4: Automatic deserialization using __new__
        try:
            obj = cls.__new__(cls)
            if hasattr(obj, "__dict__"):
                # Recursively deserialize nested values in obj_data
                deserialized_data = {
                    k: self._deserialize_value(v) for k, v in obj_data.items()
                }
                obj.__dict__.update(deserialized_data)
            return obj
        except Exception as e:
            print(f"Warning: Failed to deserialize {obj_type}: {e}")
            # Recurse through data dict as fallback
            return {k: self._deserialize_value(v) for k, v in obj_data.items()}

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()

    def get_save_metadata(self) -> dict[str, Any]:
        """
        Get metadata about the current save state without full serialization.

        Useful for displaying save slot information without loading the full save.

        Returns:
            Dictionary with save metadata (passage, timestamp, etc.)
        """
        return {
            "current_passage": self.current_passage_id,
            "timestamp": self._get_timestamp(),
            "story_name": self.story.get("name", "unknown"),
            "has_choices": self.has_choices(),
        }
