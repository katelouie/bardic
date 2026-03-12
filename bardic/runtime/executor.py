"""
Command execution for the Bardic runtime engine.

Handles all state-mutating operations: variable assignment, Python blocks,
expression statements, imports, and hook commands. The "write" side of the
engine — where the renderer is the "read" side.
"""

import sys
import traceback
from typing import Any

from bardic.runtime.hooks import HookManager


class CommandExecutor:
    """Executes story commands. Mutates the state dict in place.

    Takes shared references to state, context, and local scope stack.
    Python's reference semantics mean mutations here are visible to the
    renderer and engine automatically.

    Usage:
        executor = CommandExecutor(
            state=engine.state,
            context=engine.context,
            local_scope_stack=engine._local_scope_stack,
            hook_manager=engine.hook_manager,
        )
        executor.execute_commands(passage["execute"])
    """

    def __init__(
        self,
        state: dict,
        context: dict,
        local_scope_stack: list,
        hook_manager: HookManager,
    ):
        self.state = state
        self.context = context
        self._local_scope_stack = local_scope_stack
        self.hook_manager = hook_manager

    # ── Builtins & Eval Context ──

    def get_safe_builtins(self) -> dict[str, Any]:
        """Get safe builtins for code execution.

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
            # Type inspection (safe, read-only)
            "type": type,
            "isinstance": isinstance,
            # Debugging
            "print": print,
            # Allow imports
            "__import__": __import__,
        }

    def get_eval_context(self) -> dict[str, Any]:
        """Build evaluation context with state, local scope, and special variables.

        Returns a dictionary containing:
        - All global state variables
        - All context variables (from engine initialization)
        - Local scope variables (passage parameters) if in local scope
        - _state: Direct reference to global state dict
        - _local: Direct reference to current local scope (or empty dict)

        Returns:
            Dictionary to use as eval() context
        """
        # Start with context and state
        eval_context = {**self.context, **self.state}

        # Add special _state variable
        eval_context["_state"] = self.state

        # Add local scope if present
        if self._local_scope_stack:
            local_scope = self._local_scope_stack[-1]
            eval_context.update(local_scope)
            eval_context["_local"] = local_scope
        else:
            # _local is always present (empty dict if no params)
            eval_context["_local"] = {}

        return eval_context

    # ── Command Execution ──

    def execute_commands(self, commands: list[dict]) -> None:
        """Execute passage commands (python statements, python blocks, etc)."""
        for cmd in commands:
            if cmd["type"] == "python_statement":
                self.execute_python_statement(cmd)
            elif cmd["type"] == "python_block":
                self.execute_python_block(cmd)
            # Backward compatibility (deprecated)
            elif cmd["type"] == "set_var":
                self.execute_set_var(cmd)
            elif cmd["type"] == "expression_statement":
                self.execute_expression_statement(cmd)
            elif cmd["type"] == "hook":
                self.execute_hook_command(cmd)

    def execute_python_statement(self, cmd: dict) -> None:
        """Execute a Python statement (unified handler for all ~ statements).

        Handles assignments, expressions, function calls - any valid Python statement.
        Uses exec() for maximum flexibility.
        """
        code = cmd["code"]

        try:
            # Create evaluation context with context, state, and local scope
            eval_context = self.get_eval_context()
            if self._local_scope_stack:
                eval_context.update(self._local_scope_stack[-1])
            safe_builtins = self.get_safe_builtins()

            # Execute the statement
            exec(code, {"__builtins__": safe_builtins}, eval_context)

            # Sync any new/modified variables back to state
            # Skip private vars (starting with _), context vars (read-only), and local params
            local_param_names = (
                set(self._local_scope_stack[-1].keys())
                if self._local_scope_stack
                else set()
            )
            for key, value in eval_context.items():
                if (
                    not key.startswith("_")
                    and key not in self.context
                    and key not in local_param_names
                ):
                    self.state[key] = value

        except Exception as e:
            raise RuntimeError(
                f"Python statement failed: {code}\n"
                f"  Error: {e}\n"
                f"  Current state: {list(self.state.keys())}"
            )

    def execute_set_var(self, cmd: dict) -> None:
        """Execute a variable assignment."""
        var_name = cmd["var"]
        expression = cmd["expression"]

        # Try to evaluate the expression
        try:
            # Create evaluation context with context, state, and local scope
            eval_context = self.get_eval_context()
            if self._local_scope_stack:
                eval_context.update(self._local_scope_stack[-1])
            safe_builtins = self.get_safe_builtins()

            # Evaluate the expression
            value = eval(expression, {"__builtins__": safe_builtins}, eval_context)

            # Check if var_name contains a dot (attribute assignment like reader.background)
            if "." in var_name:
                # Use exec for attribute assignments
                assignment_code = f"{var_name} = __value__"
                eval_context["__value__"] = value
                exec(assignment_code, {"__builtins__": safe_builtins}, eval_context)
            else:
                # Simple variable - store in state
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
                value = self.parse_literal(expression)

                # Check if var_name contains a dot (attribute assignment)
                if "." in var_name:
                    # Use exec for attribute assignments
                    eval_context = self.get_eval_context()
                    safe_builtins = self.get_safe_builtins()
                    assignment_code = f"{var_name} = __value__"
                    eval_context["__value__"] = value
                    exec(assignment_code, {"__builtins__": safe_builtins}, eval_context)
                else:
                    # Simple variable - store in state
                    self.state[var_name] = value
            except Exception as e:
                raise RuntimeError(
                    f"Variable assignment failed: {var_name} = {expression}\n"
                    f"  Error: {e}\n"
                    f"  Expression could not be evaluated or parsed as literal"
                )

    def execute_expression_statement(self, cmd: dict) -> None:
        """Execute an expression statement (like a function call) without assignment."""
        code = cmd["code"]

        # Try to evaluate the expression for its side effects
        try:
            # Create evaluation context with context and state
            eval_context = self.get_eval_context()
            if self._local_scope_stack:
                eval_context.update(self._local_scope_stack[-1])
            safe_builtins = self.get_safe_builtins()

            # Evaluate the expression (result is discarded, we only care about side effects)
            eval(code, {"__builtins__": safe_builtins}, eval_context)

        except Exception as e:
            raise RuntimeError(
                f"Expression statement failed: {code}\n"
                f"  Error: {e}\n"
                f"  Current state: {list(self.state.keys())}"
            )

    def execute_hook_command(self, cmd: dict) -> None:
        """Execute a hook registration/unregistration command."""
        action = cmd["action"]
        event = cmd["event"]
        target = cmd["target"]

        if action == "add":
            self.hook_manager.register(event, target)
        elif action == "remove":
            self.hook_manager.unregister(event, target)

    def execute_python_block(self, cmd: dict) -> None:
        """Execute a python code block.

        The code block has access to:
        - self.state (current game state)
        - Any context provided at engine initialization

        Args:
            cmd: Command dictionary with 'code' key
        """
        code = cmd["code"]

        try:
            # Create execution context with safe builtins
            safe_builtins = self.get_safe_builtins()
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

    # ── Imports ──

    def execute_imports(self, story: dict) -> None:
        """Execute import statements from the story.

        Imports are executed in a temporary namespace and then added to the state,
        making them available to all passages.

        Classes are automatically registered in context for serialization.
        """
        import_statements = story.get("imports", [])

        if not import_statements:
            return

        # Join all import statements
        import_code = "\n".join(import_statements)

        if not import_code.strip():
            return

        try:
            # Add current directory to path for imports
            if "." not in sys.path:
                sys.path.insert(0, ".")
            # Execute imports with safe builtins
            safe_builtins = self.get_safe_builtins()
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
                f"  {e}\n\n"
                f"Import code:\n{import_code}\n\n"
                "Make sure the module is installed and accessible."
            )

        except Exception as e:
            raise RuntimeError(
                f"Error executing imports:\n"
                f"  {type(e).__name__}: {e}\n\n"
                f"Import code:\n{import_code}"
            )

    # ── Utilities ──

    @staticmethod
    def parse_literal(value_str: str) -> Any:
        """Parse a literal value (string, number, boolean)."""
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
