"""Content, choice, and tag parsing."""

import re
from typing import Optional, Any

from .preprocessing import strip_inline_comment


def parse_tags(line: str) -> tuple[str, list[str]]:
    """
    Extract tags from the end of a line.

    Tags start with ^ and can optionally have parameters with :.
    Multiple tags must be space-separated.

    Examples:
        "Some text ^CLIENT_CARD ^AVAILABLE" -> ("Some text", ["CLIENT_CARD", "AVAILABLE"])
        "Text ^CLIENT:SPECIAL" -> ("Text", ["CLIENT:SPECIAL"])
        "No tags" -> ("No tags", [])

    Args:
        line: The line to parse tags from

    Returns:
        Tuple of (line_without_tags, list_of_tags)
    """
    # Find all tags (^word or ^word:param) at the end of the line
    tag_pattern = r'\^[\w]+(?::[\w-]+)?'
    tags = re.findall(tag_pattern, line)

    if not tags:
        return line, []

    # Remove tags from line
    line_without_tags = line
    for tag in tags:
        line_without_tags = line_without_tags.replace(tag, '', 1)

    # Clean up extra whitespace
    line_without_tags = line_without_tags.rstrip()

    # Remove ^ prefix from tags
    clean_tags = [tag[1:] for tag in tags]

    return line_without_tags, clean_tags


def extract_passage_params(passage_header: str) -> tuple[str, str]:
    """
    Extract parameter list from passage header.

    Examples:
        "PassageName(x, y)" -> ("PassageName", "x, y")
        "PassageName(x, y=5) ^tag" -> ("PassageName ^tag", "x, y=5")
        "PassageName" -> ("PassageName", "")
        "PassageName()" -> ("PassageName", "")

    Args:
        passage_header: The passage header after "::" and inline comment removal

    Returns:
        Tuple of (passage_name_with_tags, params_str)
    """
    # Find opening paren if present
    if '(' not in passage_header:
        return passage_header, ""

    paren_start = passage_header.index('(')
    before_paren = passage_header[:paren_start]

    # Find matching closing paren using depth tracking
    depth = 0
    paren_end = -1
    for i in range(paren_start, len(passage_header)):
        if passage_header[i] == '(':
            depth += 1
        elif passage_header[i] == ')':
            depth -= 1
            if depth == 0:
                paren_end = i
                break

    if paren_end == -1:
        # Unclosed paren - will be caught as syntax error later
        return passage_header, ""

    params_str = passage_header[paren_start + 1:paren_end]
    after_paren = passage_header[paren_end + 1:]

    # Reconstruct name without params but with tags (if any)
    passage_name_with_tags = before_paren + after_paren

    return passage_name_with_tags.strip(), params_str.strip()


def parse_passage_params(params_str: str, line_num: int, lines: list,
                         filename: Optional[str], line_map: Optional[list]) -> list[dict]:
    """
    Parse passage parameter declarations.

    Examples:
        "x, y" -> [{"name": "x", "default": None}, {"name": "y", "default": None}]
        "x, y=5" -> [{"name": "x", "default": None}, {"name": "y", "default": "5"}]
        "item, count=1" -> [{"name": "item", "default": None}, {"name": "count", "default": "1"}]

    Args:
        params_str: The parameters string (contents of parentheses)
        line_num: Current line number for error reporting (0-indexed)
        lines: All lines in file for error context
        filename: Optional filename for error messages
        line_map: Optional source mapping for @include files

    Returns:
        List of {"name": str, "default": str|None} dicts

    Raises:
        SyntaxError: If parameter syntax is invalid
    """
    from .errors import format_error

    if not params_str:
        return []

    params = []
    seen_optional = False
    param_names = set()

    # Split on commas, respecting nested parens/brackets/braces
    param_parts = _split_on_commas(params_str)

    for part in param_parts:
        part = part.strip()
        if not part:
            continue

        # Check if has default value (contains =)
        if '=' in part:
            # Split on first = only
            equals_pos = part.index('=')
            param_name = part[:equals_pos].strip()
            default_value = part[equals_pos + 1:].strip()
            seen_optional = True
        else:
            param_name = part
            default_value = None

            # Check: required param can't come after optional
            if seen_optional:
                raise SyntaxError(format_error(
                    error_type="Invalid Parameter Order",
                    line_num=line_num + 1,
                    lines=lines,
                    message=f"Required parameter '{param_name}' cannot follow optional parameter",
                    pointer_length=len(params_str),
                    suggestion="Put all required parameters before optional ones",
                    filename=filename,
                    line_map=line_map
                ))

        # Validate parameter name
        if not param_name.isidentifier():
            raise SyntaxError(format_error(
                error_type="Invalid Parameter Name",
                line_num=line_num + 1,
                lines=lines,
                message=f"'{param_name}' is not a valid parameter name",
                pointer_length=len(params_str),
                suggestion="Parameter names must be valid Python identifiers (letters, numbers, underscore)",
                filename=filename,
                line_map=line_map
            ))

        # Check for Python keywords
        import keyword
        if keyword.iskeyword(param_name):
            raise SyntaxError(format_error(
                error_type="Invalid Parameter Name",
                line_num=line_num + 1,
                lines=lines,
                message=f"'{param_name}' is a Python keyword and cannot be used as a parameter name",
                pointer_length=len(params_str),
                suggestion="Choose a different parameter name",
                filename=filename,
                line_map=line_map
            ))

        # Check for duplicates
        if param_name in param_names:
            raise SyntaxError(format_error(
                error_type="Duplicate Parameter",
                line_num=line_num + 1,
                lines=lines,
                message=f"Parameter '{param_name}' is defined multiple times",
                pointer_length=len(params_str),
                suggestion="Each parameter must have a unique name",
                filename=filename,
                line_map=line_map
            ))

        param_names.add(param_name)
        params.append({"name": param_name, "default": default_value})

    return params


def _split_on_commas(text: str) -> list[str]:
    """
    Split text on commas, respecting nested parentheses, brackets, and braces.

    Example:
        "x, func(a, b), z" -> ["x", "func(a, b)", "z"]
    """
    parts = []
    current = []
    depth = 0

    for char in text:
        if char in '([{':
            depth += 1
            current.append(char)
        elif char in ')]}':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            # Top-level comma - split here
            parts.append(''.join(current))
            current = []
        else:
            current.append(char)

    # Don't forget the last part
    if current:
        parts.append(''.join(current))

    return parts


def extract_target_and_args(target_with_args: str) -> tuple[str, str]:
    """
    Extract passage name and arguments from a target specification.

    Examples:
        "PassageName" -> ("PassageName", "")
        "PassageName(x, y)" -> ("PassageName", "x, y")
        "PassageName(func(a, b), z)" -> ("PassageName", "func(a, b), z")

    Args:
        target_with_args: The target specification (may include arguments)

    Returns:
        Tuple of (passage_name, args_str)
    """
    if '(' not in target_with_args:
        return target_with_args, ""

    paren_start = target_with_args.index('(')
    passage_name = target_with_args[:paren_start]

    # Find matching closing paren using depth tracking
    depth = 0
    paren_end = -1
    for i in range(paren_start, len(target_with_args)):
        if target_with_args[i] == '(':
            depth += 1
        elif target_with_args[i] == ')':
            depth -= 1
            if depth == 0:
                paren_end = i
                break

    if paren_end == -1:
        # Unclosed paren - return as-is, will error later
        return target_with_args, ""

    args_str = target_with_args[paren_start + 1:paren_end]

    return passage_name, args_str


def parse_choice_line(line: str, passage: dict) -> Optional[dict]:
    """Parse a choice line and return choice dict or None.

    Supports:
    + [Text] -> Target (sticky choice, always available)
    * [Text] -> Target (one-time choice, disappears after use)
    {condition} + [Text] -> Target (conditional sticky)
    {condition} * [Text] -> Target (conditional one-time)
    + [Text] -> Target ^TAG1 ^TAG2:param (with tags)
    + [Text] -> Target // inline comment
    """
    # Strip inline comment first (before any parsing!)
    line, _ = strip_inline_comment(line)

    # Extract tags
    line_without_tags, tags = parse_tags(line)

    # Determine if sticky ('+') or one-time ('*')
    if line_without_tags.startswith("+ "):
        sticky = True
        choice_line = line_without_tags[2:].strip()
    elif line_without_tags.startswith("* "):
        sticky = False
        choice_line = line_without_tags[2:].strip()
    else:
        # Not a valid choice
        return None

    condition = None

    # Check for condition
    if choice_line.startswith("{"):
        match = re.match(r"\{([^}]+)\}\s*\[(.*?)\]\s*->\s*(.+)", choice_line)
        if match:
            condition, choice_text, target_with_args = match.groups()
        else:
            return None
    else:
        match = re.match(r"\[(.*?)\]\s*->\s*(.+)", choice_line)
        if match:
            choice_text, target_with_args = match.groups()
        else:
            return None

    # Extract passage name and arguments from target
    target, args = extract_target_and_args(target_with_args.strip())

    return {
        "text": parse_content_line(choice_text),  # Tokenize for interpolation
        "target": target,
        "args": args,  # NEW: store argument expressions
        "condition": condition,
        "sticky": sticky,
        "tags": tags,
    }


def find_pipe_separator(text: str, start: int = 0) -> int:
    """
    Find the | separator in an inline conditional, accounting for nested {}.

    Args:
        text: The text to search (after the ?)
        start: Where to start searching

    Returns:
        Index of the | separator, or -1 if not found

    Example:
        "{func()} | text" -> returns 9 (the | at top level)
        "{a ? {b | c} | d} | text" -> returns 14 (skips nested |)
    """
    depth = 0  # Track {} nesting depth

    for i in range(start, len(text)):
        char = text[i]

        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        elif char == '|' and depth == 0:
            # Found separator at top level (not inside nested {})
            return i

    return -1  # No separator found


def split_expressions_with_depth(text: str) -> list[str]:
    """
    Split text on {expressions}, handling nested braces correctly.

    Returns alternating list of [text, {expr}, text, {expr}, ...]
    Preserves empty strings where appropriate.

    Validates that all braces are properly matched.

    Examples:
        "Hello {name}" -> ["Hello ", "{name}", ""]
        "{a ? {b} | c}" -> ["", "{a ? {b} | c}", ""]
        "text {x} more {y} end" -> ["text ", "{x}", " more ", "{y}", " end"]

    Raises:
        ValueError: If braces are mismatched or unclosed
    """
    result = []
    current = []
    depth = 0

    for char in text:
        if char == '{':
            if depth == 0:
                # Save text before expression (even if empty)
                result.append(''.join(current))
                current = ['{']
            else:
                current.append(char)
            depth += 1
        elif char == '}':
            depth -= 1
            if depth < 0:
                # Found } without matching {
                raise ValueError(f"Found '}}' without matching '{{' in: {text}")
            current.append(char)
            if depth == 0:
                # Complete expression
                result.append(''.join(current))
                current = []
        else:
            current.append(char)

    # Check if we ended with unclosed braces
    if depth > 0:
        raise ValueError(f"Unclosed expression in: {text}")

    # Add remaining text (even if empty)
    if current or (result and not text.endswith('}')):
        result.append(''.join(current))

    return result


def parse_inline_conditional(expr: str) -> Optional[dict]:
    """
    Parse inline conditional: {condition ? truthy | falsy}

    Args:
        expr: The expression content (without outer {})

    Returns:
        dict with type='inline_conditional', condition, truthy, falsy
        or None if this is not an inline conditional

    Examples:
        "health > 50 ? Healthy | Wounded"
        -> {
            "type": "inline_conditional",
            "condition": "health > 50",
            "truthy": "Healthy",
            "falsy": "Wounded"
        }

        "inventory ? {', '.join(inventory)} | Empty"
        -> {
            "type": "inline_conditional",
            "condition": "inventory",
            "truthy": "{', '.join(inventory)}",
            "falsy": "Empty"
        }
    """
    # Check if this looks like an inline conditional
    # Must have both ? and | to be unambiguous
    if '?' not in expr:
        return None

    # Find the ? (condition separator)
    # Use first ? at top level (not inside nested {})
    q_idx = -1
    depth = 0
    for i, char in enumerate(expr):
        if char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
        elif char == '?' and depth == 0:
            q_idx = i
            break

    if q_idx == -1:
        return None  # No top-level ?

    # Split at the ?
    condition = expr[:q_idx].strip()
    rest = expr[q_idx + 1:]  # Everything after ?

    # Find the | separator (accounting for nested {})
    pipe_idx = find_pipe_separator(rest)

    if pipe_idx == -1:
        return None  # No | found, not an inline conditional

    # Split at the |
    truthy_text = rest[:pipe_idx].strip()
    falsy_text = rest[pipe_idx + 1:].strip()

    # Tokenize the truthy and falsy branches to support mixed text + expressions
    # e.g., "HP: {health}" should become [{"type": "text", "value": "HP: "}, {"type": "expression", "code": "health"}]
    truthy_tokens = parse_content_line(truthy_text) if truthy_text else []
    falsy_tokens = parse_content_line(falsy_text) if falsy_text else []

    return {
        "type": "inline_conditional",
        "condition": condition,
        "truthy": truthy_tokens,
        "falsy": falsy_tokens
    }


def parse_content_line(
    line: str,
    line_num: int = 0,
    lines: Optional[list[str]] = None,
    filename: Optional[str] = None,
    line_map: Optional[list] = None
) -> list[dict]:
    """
    Parse a content line with {variable} interpolation and optional tags.

    Returns list of content tokens (text and expressions).
    Tags are attached to the last token in the line.
    Supports inline comments: text // comment

    Args:
        line: The line to parse
        line_num: Line number (1-indexed) for error reporting
        lines: All source lines for error context
        filename: Optional filename for error context
        line_map: Optional source location map for @include resolution

    Raises:
        SyntaxError: If braces are mismatched or unclosed
    """
    from .errors import format_error

    # Strip inline comment first (before any parsing!)
    line, _ = strip_inline_comment(line)

    # Extract tags
    line_without_tags, tags = parse_tags(line)

    tokens = []

    # Split on {expressions} with depth-tracking for nested braces
    # This now validates brace matching
    try:
        parts = split_expressions_with_depth(line_without_tags)
    except ValueError as e:
        # Convert to SyntaxError with proper formatting
        if lines is not None and line_num > 0:
            raise SyntaxError(format_error(
                error_type="Expression Error",
                line_num=line_num,
                lines=lines,
                message=str(e),
                pointer_length=len(line.strip()),
                suggestion="Check that all { have matching } braces",
                filename=filename,
                line_map=line_map
            ))
        else:
            # Fallback if context not available
            raise SyntaxError(str(e))

    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            # This is an expression - check if it's an inline conditional first
            expr = part[1:-1]  # Remove { and }

            # Try to parse as inline conditional
            inline_cond = parse_inline_conditional(expr)
            if inline_cond:
                tokens.append(inline_cond)
            else:
                # Regular expression
                tokens.append({"type": "expression", "code": expr})
        elif part:
            # Regular text
            tokens.append({"type": "text", "value": part})

    # Attach tags to the last token if there are any
    if tokens and tags:
        tokens[-1]["tags"] = tags

    return tokens


def parse_value(value_str: str) -> Any:
    """
    Parse a literal value from a string.

    Tries to convert to int, float, bool, or keeps as a string.
    """
    value = value_str.strip()

    # Try boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Try to remove quotes for strings
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    # Return as-is (will be evaluated as expression later)
    return value
