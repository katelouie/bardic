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
        match = re.match(r"\{([^}]+)\}\s*\[(.*?)\]\s*->\s*([\w.]+)", choice_line)
        if match:
            condition, choice_text, target = match.groups()
        else:
            return None
    else:
        match = re.match(r"\[(.*?)\]\s*->\s*([\w.]+)", choice_line)
        if match:
            choice_text, target = match.groups()
        else:
            return None

    return {
        "text": parse_content_line(choice_text),  # Tokenize for interpolation
        "target": target,
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

    Examples:
        "Hello {name}" -> ["Hello ", "{name}", ""]
        "{a ? {b} | c}" -> ["", "{a ? {b} | c}", ""]
        "text {x} more {y} end" -> ["text ", "{x}", " more ", "{y}", " end"]
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
            current.append(char)
            if depth == 0:
                # Complete expression
                result.append(''.join(current))
                current = []
        else:
            current.append(char)

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


def parse_content_line(line: str) -> list[dict]:
    """
    Parse a content line with {variable} interpolation and optional tags.

    Returns list of content tokens (text and expressions).
    Tags are attached to the last token in the line.
    Supports inline comments: text // comment
    """
    # Strip inline comment first (before any parsing!)
    line, _ = strip_inline_comment(line)

    # Extract tags
    line_without_tags, tags = parse_tags(line)

    tokens = []

    # Split on {expressions} with depth-tracking for nested braces
    parts = split_expressions_with_depth(line_without_tags)

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
