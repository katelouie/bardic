"""
Render directive processing for the Bardic runtime engine.

Handles @render directives: argument parsing, parameter binding,
framework-specific output (React), and evaluated vs raw modes.
"""

import ast
import uuid
from typing import Any, Callable


class DirectiveProcessor:
    """Processes @render directives, binds arguments, and handles framework output.

    Decoupled from the engine via callable providers for eval context and builtins,
    so it can be tested independently with plain dicts.

    Usage:
        processor = DirectiveProcessor(
            eval_context_provider=engine._get_eval_context,
            builtins_provider=engine._get_safe_builtins,
            state_provider=lambda: engine.state,
        )
        result = processor.process_render_directive(directive, evaluate=True)
    """

    def __init__(
        self,
        eval_context_provider: Callable[[], dict],
        builtins_provider: Callable[[], dict],
        state_provider: Callable[[], dict],
        framework_processors: dict[str, Callable] | None = None,
    ):
        self._get_eval_context = eval_context_provider
        self._get_builtins = builtins_provider
        self._get_state = state_provider
        self.framework_processors = framework_processors or {}

    def process_render_directive(
        self, directive: dict[str, Any], evaluate: bool = True
    ) -> dict[str, Any]:
        """Process a render directive based on configuration.

        Two modes:
        1. evaluate=True: Evaluate Python expressions, return data
        2. evaluate=False: Return raw expression, let frontend eval

        Args:
            directive: Parsed directive from content tokens
            evaluate: Whether to evaluate expressions or pass them raw

        Returns:
            Processed directive ready for frontend
        """
        name: str = directive.get("name", "")
        args_str = directive.get("args", "")
        framework_hint = directive.get("framework_hint")

        if evaluate:
            # Evaluated mode: Execute python expressions, return data
            try:
                eval_context = self._get_eval_context()
                safe_builtins = self._get_builtins()

                # Parse and evaluate arguments
                if args_str:
                    args_dict = self.parse_directive_args(args_str, eval_context, safe_builtins)
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
                "state_snapshot": dict(self._get_state()),
            }

            if framework_hint:
                result["framework_hint"] = framework_hint

            return result

    def parse_directive_args(self, args_str: str, eval_context: dict, safe_builtins: dict) -> dict:
        """Parse directive arguments into a dictionary.

        Supports both positional and keyword arguments:
        - f(a, b, c) becomes {"arg_0": a, "arg_1": b, "arg_2": c}
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
            fake_call = f"__directive__({args_str})"
            tree = ast.parse(fake_call, mode="eval")
            call_node = tree.body

            result = {}

            # Process positional arguments
            for i, arg in enumerate(call_node.args):
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

    def bind_arguments(self, params: list[dict], arg_dict: dict) -> dict:
        """Bind provided arguments to parameter names.

        Args:
            params: List of {"name": str, "default": str|None} from passage definition
            arg_dict: Parsed arguments from parse_directive_args()
                      Format: {"arg_0": val, "arg_1": val, "keyword": val, ...}

        Returns:
            Dict of parameter name -> evaluated value

        Raises:
            ValueError: If required param missing, or argument provided twice
        """
        result = {}

        # Process positional arguments
        positional_index = 0
        for i, param in enumerate(params):
            arg_key = f"arg_{positional_index}"

            if arg_key in arg_dict:
                # Positional arg provided
                result[param["name"]] = arg_dict[arg_key]
                positional_index += 1
            elif param["name"] in arg_dict:
                # Keyword arg provided
                if param["name"] in result:
                    raise ValueError(
                        f"Parameter '{param['name']}' provided multiple times "
                        f"(both positional and keyword)"
                    )
                result[param["name"]] = arg_dict[param["name"]]
            elif param["default"] is not None:
                # Use default value (evaluate it)
                eval_context = self._get_eval_context()
                # IMPORTANT: Include already-bound params in eval context
                # This allows defaults like (x, y=x*2)
                eval_context.update(result)

                safe_builtins = self._get_builtins()
                result[param["name"]] = eval(
                    param["default"], {"__builtins__": safe_builtins}, eval_context
                )
            else:
                # Required param not provided
                raise ValueError(f"Required parameter '{param['name']}' not provided")

        return result

    @staticmethod
    def process_for_react(component_name: str, args: dict) -> dict:
        """Format directive data for React convenience.

        Converts generic data into React-friendly format:
        - Suggests component name (PascalCase)
        - Generates unique key for list rendering
        - Organizes props cleanly

        Args:
            component_name: The directive name (e.g. 'card_detail')
            args: Evaluated arguments dictionary

        Returns:
            React-optimized data structure
        """
        # Convert snake_case to PascalCase for component name
        suggested_component = "".join(word.capitalize() for word in component_name.split("_"))

        # Clean up props
        props = {}
        for key, value in args.items():
            props[key] = value

        return {
            "componentName": suggested_component,
            "key": f"{component_name}_{uuid.uuid4().hex[:8]}",
            "props": props,
        }
