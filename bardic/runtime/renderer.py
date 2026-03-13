"""
Content rendering for the Bardic runtime engine.

Handles all content token rendering: text, expressions, inline conditionals,
loops, conditional blocks, directives, and choice filtering. The "read" side
of the engine — though it also delegates code execution to the executor for
Python statements and blocks encountered during rendering (e.g., inside
conditionals and loops).
"""

import traceback
from typing import Any, Callable, Optional

from bardic.runtime.types import PassageOutput


class ContentRenderer:
    """Renders passage content, choices, and directives.

    Takes shared references to state, executor, and other subsystems.
    Python's reference semantics mean state mutations by the executor
    during rendering (e.g., @py blocks inside @if) are visible here
    automatically.

    Usage:
        renderer = ContentRenderer(
            eval_context_provider=executor.get_eval_context,
            builtins_provider=executor.get_safe_builtins,
            state=engine.state,
            local_scope_stack=engine._local_scope_stack,
            executor=engine.executor,
            directive_processor=engine.directive_processor,
            passages=engine.passages,
            used_choices=engine.used_choices,
            join_section_index=engine._join_section_index,
            evaluate_directives=engine.evaluate_directives,
        )
    """

    def __init__(
        self,
        eval_context_provider: Callable[[], dict],
        builtins_provider: Callable[[], dict],
        state: dict,
        local_scope_stack: list,
        executor: Any,  # CommandExecutor — avoid circular import
        directive_processor: Any,  # DirectiveProcessor — avoid circular import
        passages: dict,
        used_choices: set,
        join_section_index: dict,
        evaluate_directives: bool = True,
    ):
        self._get_eval_context = eval_context_provider
        self._get_safe_builtins = builtins_provider
        self._state = state
        self._local_scope_stack = local_scope_stack
        self._executor = executor
        self._directive_processor = directive_processor
        self._passages = passages
        self._used_choices = used_choices
        self._join_section_index = join_section_index
        self._evaluate_directives = evaluate_directives

    # ── Passage-Level Rendering ──

    def render_passage(self, passage_id: str, current_passage_id: str) -> PassageOutput:
        """
        Render a passage (pure, no side effects on navigation state).

        This renders content and filters choices based on current state.
        It does NOT execute commands - that's done by engine._execute_passage.

        If a jump is encountered, returns jump_target in output.
        The CALLER decides whether to follow the jump.

        Args:
            passage_id: ID of the passage to render
            current_passage_id: The engine's current passage (for join section lookup)

        Returns:
            PassageOutput with content, choices and directives

        Raises:
            ValueError: If passage_id doesn't exist
        """
        if passage_id not in self._passages:
            raise ValueError(f"Passage '{passage_id}' not found.")

        passage = self._passages[passage_id]

        # Render content with current state
        if isinstance(passage["content"], list):
            # New format: list of tokens
            content, jump_target, directives = self.render_content(passage["content"])
        else:
            # Old format: plain string (backwards compatible)
            content = passage["content"]
            jump_target = None
            directives = []

        # Separate choice/input directives from render directives
        # (all are collected in the directives list by render_content)
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
        current_section = self._join_section_index.get(passage_id, 0)
        for choice in all_choices:
            choice_section = choice.get("section", 0)
            if (
                self.is_choice_available(choice, current_passage_id)
                and choice_section == current_section
            ):
                # Render choice text (interpolates variables)
                rendered_choice = self.render_choice_text(choice)
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

    def render_choice_text(self, choice: dict) -> dict:
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
            rendered_text, _, _ = self.render_content(choice_text)

        # Return choice with rendered text
        return {**choice, "text": rendered_text}

    def is_choice_available(self, choice: dict, current_passage_id: str) -> bool:
        """Check if a choice should be shown based on its condition and if used (1-time).

        A choice is available if:
        1. Its condition (if any) evaluates to True
        2. It's sticky (+ ) or it hasn't been used yet (* )

        Args:
            choice: Choice dict with optional condition and sticky fields
            current_passage_id: The engine's current passage ID (for choice ID tracking)
        """
        # Check if one-time choice has already been used
        sticky = choice.get("sticky", True)
        if not sticky:
            # This is a one-time choice - check if used
            # Render choice text to get a plain string that matches the ID format in choose()
            rendered = self.render_choice_text(choice)
            choice_id = f"{current_passage_id}:{rendered['text']}:{choice['target']}"
            if choice_id in self._used_choices:
                return False  # Already used, hide it

        # Check condition (if present)
        condition = choice.get("condition")

        # No condition = always available (if not used)
        if not condition:
            return True

        # Else, evaluate the condition
        try:
            eval_context = self._get_eval_context()
            if self._local_scope_stack:
                eval_context.update(self._local_scope_stack[-1])
            safe_builtins = self._get_safe_builtins()
            result = eval(condition, {"__builtins__": safe_builtins}, eval_context)
            return bool(result)
        except Exception as e:
            # If condition fails to evaluate, hide the choice
            print(f"Warning: Choice condition failed: {condition} - {e}")
            return False

    def render_from_join_marker(self, section_idx: int, current_passage_id: str) -> PassageOutput:
        """
        Render the current passage starting from after a specific @join marker.

        Finds the Nth join_marker in content (where N = section_idx),
        then renders everything after it until the next @join or end.

        Args:
            section_idx: Which @join marker to start from (0 = first)
            current_passage_id: The engine's current passage ID

        Returns:
            PassageOutput with content and choices from after the @join
        """
        passage = self._passages[current_passage_id]
        content_tokens = passage.get("content", [])

        # Find the Nth join_marker
        join_markers_found = 0
        start_idx = 0

        for i, token in enumerate(content_tokens):
            if isinstance(token, dict) and token.get("type") == "join_marker":
                if join_markers_found == section_idx:
                    start_idx = i + 1  # Start AFTER the marker
                    break
                join_markers_found += 1

        if start_idx == 0 and section_idx > 0:
            # Didn't find the requested join marker
            raise RuntimeError(
                f"@join marker {section_idx} not found in passage '{current_passage_id}'"
            )

        # Find where to stop (next @join or end)
        end_idx = len(content_tokens)
        for i in range(start_idx, len(content_tokens)):
            token = content_tokens[i]
            if isinstance(token, dict) and token.get("type") == "join_marker":
                end_idx = i
                break

        # Render content between markers
        section_tokens = content_tokens[start_idx:end_idx]
        content, jump_target, directives = self.render_content(section_tokens)

        # Get choices for current section only
        current_section = section_idx + 1  # We're now IN section N+1

        section_choices = []
        for choice in passage.get("choices", []):
            choice_section = choice.get("section", 0)

            if choice_section == current_section:
                # This choice belongs to the current section
                if self.is_choice_available(choice, current_passage_id):
                    rendered = self.render_choice_text(choice)
                    section_choices.append(rendered)

        return PassageOutput(
            content=content,
            choices=section_choices,
            passage_id=current_passage_id,
            render_directives=directives,
            input_directives=[],
            jump_target=jump_target,
        )

    # ── Content Token Rendering ──

    def render_content(self, content_tokens: list[dict]) -> tuple[str, Optional[str], list[dict]]:
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
                    # Merge context, state, and local scope for evaluation
                    eval_context = self._get_eval_context()
                    if self._local_scope_stack:
                        eval_context.update(self._local_scope_stack[-1])
                    code = token["code"]

                    # Check for format specifier (e.g., "average:.1f")
                    if ":" in code and not any(op in code for op in ["==", "!=", "<=", ">=", "::"]):
                        # Split expression and format spec
                        # Find the first : that's not part of an operator
                        colon_idx = code.find(":")
                        expr = code[:colon_idx].strip()
                        format_spec = code[colon_idx + 1 :].strip()

                        # Evaluate the expression
                        value = eval(expr, {"__builtins__": safe_builtins}, eval_context)

                        # Apply format spec
                        result.append(format(value, format_spec))
                    else:
                        # No format spec, just evaluate and convert to string
                        value = eval(code, {"__builtins__": safe_builtins}, eval_context)
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
                    result.append(f"{{ERROR: {token['code']} - {type(e).__name__}: {e}}}")
            elif token["type"] == "inline_conditional":
                # Evaluate inline conditional: {condition ? truthy | falsy}
                try:
                    eval_context = self._get_eval_context()
                    safe_builtins = self._get_safe_builtins()

                    # Evaluate the condition
                    condition_result = eval(
                        token["condition"],
                        {"__builtins__": safe_builtins},
                        eval_context,
                    )

                    # Choose branch based on condition (truthy or falsy)
                    # Branches are now token lists (new format) or strings (backward compatibility)
                    branch = token["truthy"] if condition_result else token["falsy"]

                    # Handle both new format (token list) and old format (string)
                    if isinstance(branch, list):
                        # New format: token list like [{"type": "text", "value": "HP: "}, {"type": "expression", "code": "health"}]
                        # Recursively render the tokens
                        branch_content, _, _ = self.render_content(branch)
                        result.append(branch_content)
                    elif isinstance(branch, str):
                        # Old format (backward compatibility): plain string or single expression
                        if not branch:
                            # Empty branch - add nothing
                            pass
                        elif branch.startswith("{") and branch.endswith("}"):
                            # Branch contains an expression - evaluate it
                            branch_expr = branch[1:-1]  # Remove { }

                            # Check for format spec in the branch expression
                            if ":" in branch_expr and not any(
                                op in branch_expr for op in ["==", "!=", "<=", ">=", "::"]
                            ):
                                # Has format spec
                                colon_idx = branch_expr.find(":")
                                expr = branch_expr[:colon_idx].strip()
                                format_spec = branch_expr[colon_idx + 1 :].strip()

                                value = eval(expr, {"__builtins__": safe_builtins}, eval_context)
                                result.append(format(value, format_spec))
                            else:
                                # No format spec
                                value = eval(
                                    branch_expr,
                                    {"__builtins__": safe_builtins},
                                    eval_context,
                                )
                                result.append(str(value))
                        else:
                            # Plain text - add as-is
                            result.append(branch)

                except Exception as e:
                    # Error evaluating inline conditional
                    result.append(f"{{ERROR: inline conditional - {e}}}")
            elif token["type"] == "render_directive":
                # Process and collect directive (don't render as text)
                processed = self._directive_processor.process_render_directive(
                    token, evaluate=self._evaluate_directives
                )
                directives.append(processed)
            elif token["type"] == "input":
                # Collect input directive (don't render as text)
                directives.append(token)
            elif token["type"] == "python_statement":
                # Execute Python statement (modifies state, produces no text output)
                # This happens during rendering, so it only runs if its branch/loop is active
                self._executor.execute_python_statement(token)
                # Don't append anything to result - Python statements don't generate text
            elif token["type"] == "set_var":
                # Backward compatibility: Execute variable assignment
                self._executor.execute_set_var(token)
            elif token["type"] == "expression_statement":
                # Backward compatibility: Execute expression statement
                self._executor.execute_expression_statement(token)
            elif token["type"] == "python_block":
                # Execute Python block (modifies state, produces no text output)
                # This happens during rendering, so it only runs if its branch/loop is active
                self._executor.execute_python_block(token)
                # Don't append anything to result - Python blocks don't generate text
            elif token["type"] == "conditional":
                # Render conditional blocks
                branch_content, jump_target, branch_directives = self.render_conditional(token)
                result.append(branch_content)
                directives.extend(branch_directives)  # Collect directives from branch
                # If jump was found in the conditional, stop and return
                if jump_target:
                    return "".join(result), jump_target, directives
            elif token["type"] == "for_loop":
                # Render loop
                loop_content, jump_target, loop_directives = self.render_loop(token)
                result.append(loop_content)
                directives.extend(loop_directives)  # Collect directives from loop
                # If jump was found in the loop, stop and return
                if jump_target:
                    return "".join(result), jump_target, directives
            elif token["type"] == "jump":
                # Jump found - stop rendering HERE and return the target
                return "".join(result), token["target"], directives
            elif token["type"] == "hook":
                # Execute hook registration/unregistration during render
                # (for hooks inside conditionals/loops)
                self._executor.execute_hook_command(token)
                # Hooks don't produce text output
            elif token["type"] == "join_marker":
                # Stop rendering at @join marker - content after @join comes later
                break

        return "".join(result), None, directives

    def render_loop(self, loop: dict) -> tuple[str, Optional[str], list[dict]]:
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
            eval_context = self._get_eval_context()
            if self._local_scope_stack:
                eval_context.update(self._local_scope_stack[-1])
            safe_builtins = self._get_safe_builtins()
            collection = eval(collection_expr, {"__builtins__": safe_builtins}, eval_context)

            # Check if variable is tuple unpacking
            variables = [v.strip() for v in variable.split(",")]
            is_tuple_unpack = len(variables) > 1

            # Render content for each item in the collection
            result = []
            all_directives = []  # Collect directives from all iterations

            for item in collection:
                original_values = {}

                try:
                    if is_tuple_unpack:
                        # Tuple unpacking: assign each variable
                        for i, var in enumerate(variables):
                            original_values[var] = self._state.get(var)
                            if isinstance(item, (list, tuple)) and i < len(item):
                                self._state[var] = item[i]
                            else:
                                self._state[var] = None
                    else:
                        # Single variable
                        original_values[variable] = self._state.get(variable)
                        self._state[variable] = item
                except Exception as e:
                    print(f"Warning: Loop variable assignment failed: {e}")
                    print(f"  variable: {variable}, is_tuple: {is_tuple_unpack}, item: {item}")
                    raise

                # Render the loop body
                iteration_content, jump_target, iteration_directives = self.render_content(content)
                result.append(iteration_content)
                all_directives.extend(iteration_directives)  # Collect directives

                # Add loop choices for this iteration (if any)
                # IMPORTANT: Render choice text NOW while loop variable is in scope!
                if "choices" in loop:
                    for choice in loop["choices"]:
                        # Render choice text with current loop variable
                        rendered_choice = self.render_choice_text(choice)
                        all_directives.append({"type": "choice", **rendered_choice})

                # Restore original values
                for var, original_value in original_values.items():
                    if original_value is not None:
                        self._state[var] = original_value
                    elif var in self._state:
                        del self._state[var]

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
            traceback.print_exc()
            return error_msg, None, []

    def render_conditional(self, conditional: dict) -> tuple[str, Optional[str], list[dict]]:
        """
        Render a conditional block by evaluating conditions and rendering the first true branch.

        Args:
            conditional: Conditional structure with branches
        Returns:
            Rendered content from the first true branch
        """
        eval_context = self._get_eval_context()
        if self._local_scope_stack:
            eval_context.update(self._local_scope_stack[-1])
        safe_builtins = self._get_safe_builtins()

        # Evaluate each branch until we find a true condition
        for branch in conditional.get("branches", []):
            condition = branch.get("condition", "False")

            try:
                # Evaluate the condition
                result = eval(condition, {"__builtins__": safe_builtins}, eval_context)

                if result:
                    # This branch is true -- render its content
                    content, jump_target, directives = self.render_content(branch["content"])

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

    # ── Utilities ──

    @staticmethod
    def split_format_spec(code: str) -> tuple[str, str | None]:
        """Split 'expression:format_spec' at the rightmost valid colon."""
        if ":" in code and not any(op in code for op in ["==", "!=", "<=", ">=", "::"]):
            colon_idx = code.rfind(":")  # Use rfind for rightmost
            expr = code[:colon_idx].strip()
            spec = code[colon_idx + 1 :].strip()
            return expr, spec
        return code, None
