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

    # Split on {expressions}
    parts = re.split(r"(\{[^}]+\})", line_without_tags)

    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            # This is an expression
            expr = part[1:-1]  # Remove { and }
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
