"""Directive parsing: @render, @input, and multiline expressions."""

import re
from typing import Optional

from .preprocessing import strip_inline_comment


def parse_render_line(line: str) -> Optional[dict]:
    """
    Parse a complete @render line including framwork hint detection.

    Handles:
        @render my_function(args)
        @render:react my_function(args)
        @render simple_function
        @render my_function(args) // inline comment

    Args:
        line: The full line of the story file

    Returns:
        Parsed directive dict, or None if invalid
    """
    # Strip inline comment first
    line, _ = strip_inline_comment(line)

    # Must start with @render
    if not line.strip().startswith("@render"):
        return None

    # Extract everything after "@render"
    after_render = line.strip()[7:]  # Skip '@render'

    framework_hint = None
    directive_str = None

    if after_render.startswith(":"):
        # Pattern: :framework directive_name(args)
        match = re.match(r"^:(\w+)\s+(.+)$", after_render)
        if match:
            framework_hint = match.group(1)
            directive_str = match.group(2)
        else:
            print(f"Warning: Invalid @render:framework syntax: {line.strip()}")
            return None
    elif after_render.strip():
        # No framework hint, just the directive
        directive_str = after_render.strip()
    else:
        print(f"Warning: Empty @render directive: {line.strip()}")
        return None

    # Parse the directive string and arguments
    directive = parse_render_directive(directive_str)
    if not directive:
        return None

    # Add framework hint
    directive["framework_hint"] = framework_hint

    return directive


def parse_render_directive(directive_str: str) -> Optional[dict]:
    """
    Parse a render directive with optional framework hint.

    Syntax:
        @render directive_name(args) # generic
        @render:react directive_name(args) # react convenience
        @render:unity directive_name(args) # unity convenience

    Examples:
        render_spread(cards, layout="celtic") # generic
        :react render_card_detail(card, pos="past") # react-optimized
        :unity spawn_card(card) # unity-optimized

    Args:
        directive_str: The text after '@render' or '@render:'

    Returns:
        Dict with type='render_directive', name, framework_hint, and args
    """
    directive_str = directive_str.strip()

    # Pattern: function_name(args) or function_name
    match = re.match(r"^(\w+)(?:\((.*)\))?$", directive_str)

    if not match:
        print(f"Warning: Invalid directive syntax: {directive_str}")
        return None

    name = match.group(1)
    args = match.group(2) if match.group(2) else ""

    return {"type": "render_directive", "name": name, "args": args.strip()}


def extract_multiline_expression(
    lines: list[str], start_index: int, initial_expr: str
) -> tuple[str, int]:
    """
    Extract a multi-line expression that starts with an opening bracket.

    Handles:
    - Lists: [...]
    - Dicts: {...}
    - Tuples: (...)

    Args:
        lines: All lines in the passage
        start_index: Index of the line with the opening bracket
        initial_expr: The expression from the first line (e.g. "[")

    Returns:
        Tuple of (complete_expression, lines_consumed)
    """
    # Check if this might be a multi-line expression
    stripped = initial_expr.strip()

    if not any(stripped.endswith(c) for c in ["[", "{", "("]):
        # not a multi-line expression, return as-is
        return initial_expr, 1

    # Track bracket nesting
    bracket_stack = []
    bracket_pairs = {"[": "]", "{": "}", "(": ")"}
    reverse_pairs = {"]": "[", "}": "{", ")": "("}

    # Add opening brackets from initial expression
    for char in stripped:
        if char in bracket_pairs:
            bracket_stack.append(char)

    # Start collecting lines
    expr_lines = [initial_expr]
    i = start_index + 1

    # Continue until brackets are balanced
    while i < len(lines) and bracket_stack:
        line = lines[i]

        # Track brackets in this line
        for char in line:
            if char in bracket_pairs:
                bracket_stack.append(char)
            elif char in reverse_pairs:
                # Closing bracket
                if bracket_stack and bracket_stack[-1] == reverse_pairs[char]:
                    bracket_stack.pop()
                else:
                    # Mismatched bracket - stop here
                    break

        expr_lines.append(line)
        i += 1

        # If brackets are balanced, we're done
        if not bracket_stack:
            break

    # Join all lines preserving structure
    complete_expr = "\n".join(expr_lines)
    lines_consumed = i - start_index

    return complete_expr, lines_consumed


def parse_input_line(line: str) -> Optional[dict]:
    """
    Parse an @input directive for text input.

    Syntax:
        @input name="variable_name"
        @input name="variable_name" placeholder="hint text"
        @input name="variable_name" placeholder="hint" label="Display Label"
        @input name="variable_name" // inline comment

    Args:
        line: The full line containing @input directive

    Returns:
        Dict with type='input', name, optional placeholder and label, or None if invalid
    """
    # Strip inline comment first
    line, _ = strip_inline_comment(line)

    # Must start with @input
    if not line.strip().startswith("@input"):
        return None

    # Extract everything after "@input"
    after_input = line.strip()[6:].strip()  # Skip '@input'

    if not after_input:
        print(f"Warning: Empty @input directive: {line.strip()}")
        return None

    # Parse name="value" style attributes
    # Pattern: name="variable" placeholder="text" label="Label"
    input_spec = {"type": "input"}

    # Extract all key="value" pairs
    attr_pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(attr_pattern, after_input)

    for key, value in matches:
        input_spec[key] = value

    # Validate that 'name' is present (required)
    if 'name' not in input_spec:
        print(f"Warning: @input directive missing 'name' attribute: {line.strip()}")
        return None

    # Set defaults
    if 'label' not in input_spec:
        # Default label to capitalized name
        input_spec['label'] = input_spec['name'].replace('_', ' ').title()

    if 'placeholder' not in input_spec:
        input_spec['placeholder'] = ''

    return input_spec
