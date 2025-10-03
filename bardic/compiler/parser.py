"""
Parse .bard files into intermediate representation.

Supports:
- :: PassageName (passage headers)
- Regular Text
- + [Choice Text] -> Target Passage (choices)
"""

import re
from typing import Dict, Optional, Any


def parse(source: str) -> Dict[str, Any]:
    """
    Parse a .bard source string into structured data.

    Args:
        source: The .bard file content as a string

    Returns:
        Dict containing version, initial_passage, and passages
    """
    passages = {}
    current_passage = None

    lines = source.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Passage Header: :: PassageName
        if line.startswith(":: "):
            passage_name = line[3:].strip()
            current_passage = {
                "id": passage_name,
                "content": [],
                "choices": [],
                "execute": [],
            }
            passages[passage_name] = current_passage
            i += 1
            continue

        # Skip if not in a passage
        if not current_passage:
            i += 1
            continue

        # Variable assignment: ~ var = value
        if line.startswith("~ ") and current_passage:
            assignment = line[2:].strip()
            if "=" in assignment:
                var_name, value_expr = assignment.split("=", 1)
                var_name = var_name.strip()
                value_expr = value_expr.strip()

                # Store as execution command
                current_passage["execute"].append(
                    {"type": "set_var", "var": var_name, "expression": value_expr}
                )
            i += 1
            continue

        # Choice: + [Text] -> Target or + {condition} [Text] -> Target
        if line.startswith("+ "):
            choice = parse_choice_line(line, current_passage)
            if choice:
                current_passage["choices"].append(choice)
            i += 1
            continue

        # Regular content line
        if line.strip() and current_passage:
            content_tokens = parse_content_line(line)
            current_passage["content"].extend(content_tokens)
            # Add newline after content line
            current_passage["content"].append({"type": "text", "value": "\n"})
            i += 1
            continue

        # Empty line
        if not line.strip() and current_passage:
            current_passage["content"].append({"type": "text", "value": "\n"})
            i += 1
            continue

        i += 1

    # Build final structure
    return {
        "version": "0.1.0",
        "initial_passage": list(passages.keys())[0] if passages else None,
        "passages": passages,
    }


def parse_choice_line(line: str, passage: dict) -> Optional[dict]:
    """Parse a choice line and return choice dict or None."""
    choice_line = line[2:].strip()
    condition = None

    # Check for condition
    if choice_line.startswith("{"):
        match = re.match(r"\{([^}]+)\}\s*\[(.*?)\]\s*->\s*(\w+)", choice_line)
        if match:
            condition, choice_text, target = match.groups()
        else:
            return None
    else:
        match = re.match(r"\[(.*?)\]\s*->\s*(\w+)", choice_line)
        if match:
            choice_text, target = match.groups()
        else:
            return None

    return {"text": choice_text, "target": target, "condition": condition}


def parse_file(filepath: str) -> Dict[str, Any]:
    """
    Parse a .bard file from disk.

    Args:
        filepath: Path to the .bard file

    Returns:
        Parsed story structure
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return parse(f.read())


def parse_content_line(line: str) -> list[dict]:
    """
    Parse a content line with {variable} interpolation.

    Returns list of content tokens (text and expressions).
    """
    tokens = []

    # Split on {expressions}
    parts = re.split(r"(\{[^}]+\})", line)

    for part in parts:
        if part.startswith("{") and part.endswith("}"):
            # This is an expression
            expr = part[1:-1]  # Remove { and }
            tokens.append({"type": "expression", "code": expr})
        elif part:
            # Regular text
            tokens.append({"type": "text", "value": part})

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
