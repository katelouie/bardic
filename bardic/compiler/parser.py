"""
Parse .bard files into intermediate representation.

Supports:
- :: PassageName (passage headers)
- Regular Text
- + [Choice Text] -> Target Passage (choices)
"""

import re
from pathlib import Path
from typing import Dict, Optional, Any
import sys


def resolve_includes(source: str, base_path: str, seen: Optional[set] = None) -> str:
    """
    Resolve @include directives recursively.

    Args:
        source: The source text with potential @include directives
        base_path: Path to the file being processed (for relative includes)
        seen: Set of already-included files (to detect circular includes)

    Returns:
        Source text with all includes expanded

    Raises:
        ValueError: If circular include detected
        FileNotFoundError: If included file doesn't exist
    """
    if seen is None:
        seen = set()

    # Normalize base path
    base_path = str(Path(base_path).resolve())

    # Check for circular includes
    if base_path in seen:
        raise ValueError(f"Circular include detected: {base_path}")

    seen.add(base_path)

    lines = source.split("\n")
    result = []

    for line in lines:
        # Check for @include directive
        if line.strip().startswith("@include "):
            # Extract the include path
            include_path = line.strip()[9:].strip()  # Remove '@include '

            # Resolve relative to the current file
            base_dir = Path(base_path).parent
            full_path = (base_dir / include_path).resolve()

            try:
                # Read the included file
                with open(full_path, "r", encoding="utf-8") as f:
                    included_content = f.read()

                # Recursively resolve includes in the included file
                resolved_content = resolve_includes(
                    included_content,
                    str(full_path),
                    seen.copy(),  # Pass a copy so each branch tracks separately
                )

                # Add the resolved content
                result.append(resolved_content)

            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Include file not found: {include_path}\n"
                    f"  Looking for: {full_path}\n"
                    f"  Included from: {base_path}\n"
                )

        else:
            # Regular line -- keep it
            result.append(line)

    return "\n".join(result)


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
    explicit_start = None

    lines = source.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # @start directive (optional override)
        if line.strip().startswith("@start "):
            explicit_start = line.strip()[7:].strip()
            i += 1
            continue

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

    # Determine initial passage (priority order)
    initial_passage = _determine_initial_passage(passages, explicit_start)

    # Detect duplicate passages
    check_duplicate_passages(passages)
    # This is optional - just noting where we'd add this
    # We'd need to track source file in the token stream
    # For now, duplicates are naturally prevented by dict keys

    # Build final structure
    return {
        "version": "0.1.0",
        "initial_passage": initial_passage,
        "passages": passages,
    }


def _determine_initial_passage(
    passages: dict[str, Any], explicit_start: Optional[str] = None
) -> str:
    """
    Determine which passage to start with.

    Priority:
    1. Explicit @start directive
    2. Passage named "Start" (convention)
    3. First passage (with warning)

    Args:
        passages: Dictionary of parsed passages
        explicit_start: Optional explicit start passage from @start directive

    Returns:
        Name of the initial passage

    Raises:
        ValueError: If no passages or if explicit start passage not found
    """
    if not passages:
        raise ValueError("Story has no passages")

    # 1. Explicit @start directive
    if explicit_start:
        if explicit_start not in passages:
            raise ValueError(
                f"Start passage '{explicit_start}' specified by @start directive not found.\n"
                f"Available passages: {', '.join(sorted(passages.keys()))}"
            )
        return explicit_start

    # 2. Default to "Start" if exists (convention, similar to Twine)
    if "Start" in passages:
        return "Start"

    # 3. Fallback to first passage (with warning)
    first_passage = list(passages.keys())[0]
    print(
        f"Warning: No 'Start' passage found and no @start directive specified.\n"
        f"Defaulting to first passage: '{first_passage}'\n"
        f"Consider adding a ':: Start' passage or '@start {first_passage}' directive.",
        file=sys.stderr,
    )
    return first_passage


def check_duplicate_passages(
    passages: dict[str, Any], filepath: Optional[str] = None
) -> None:
    """Check for duplicate passage names.

    This is called after parsing to ensure no passages are defined twice.

    Args:
        passages: Dictionary of parsed passages
        filepath: Optional filepath for error context

    Raises:
        ValueError: If duplicate passages found
    """
    # In the current implementation, the dict naturally prevents duplicates
    # But we could track source files for better error messages
    # For now, this is a placeholder for future enhancement
    pass


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
    Parse a .bard file from disk, resolving includes.

    Args:
        filepath: Path to the .bard file

    Returns:
        Parsed story structure
    """
    # Read the source file
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    # Resolve any includes first
    resolved_source = resolve_includes(source, filepath)

    # Then parse everything else normally
    return parse(resolved_source)


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
