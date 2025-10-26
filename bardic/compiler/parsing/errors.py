"""Error formatting utilities for Bardic parser."""

from typing import List


def format_error(
    error_type: str,
    line_num: int,
    lines: List[str],
    message: str,
    pointer_col: int = 0,
    pointer_length: int = None,
    suggestion: str = None,
    filename: str = None
) -> str:
    """
    Format a beautiful error message with context.

    Args:
        error_type: Type of error (e.g., "Syntax Error", "Unclosed Block")
        line_num: Line number where error occurred (0-indexed)
        lines: All source lines
        message: Main error message
        pointer_col: Column where error starts (for pointer alignment)
        pointer_length: Length of pointer (defaults to rest of line)
        suggestion: Optional hint for how to fix
        filename: Optional filename to include in error

    Returns:
        Formatted error string with context and visual pointer
    """
    # Build header
    parts = []
    parts.append(f"✗ {error_type}")
    if filename:
        parts.append(f" in {filename}")
    parts.append(f" on line {line_num + 1}:")
    parts.append(f"  {message}")
    parts.append("")

    # Get context lines (±2 around error)
    start = max(0, line_num - 2)
    end = min(len(lines), line_num + 3)

    # Show context
    for i in range(start, end):
        if i >= len(lines):
            break
        line = lines[i]
        line_marker = f"  {i + 1:4} | "
        parts.append(line_marker + line)

        # Add pointer under error line
        if i == line_num:
            if pointer_length is None:
                # Point to rest of line from pointer_col
                pointer_length = len(line.strip()) - pointer_col
            indent = len(line_marker) + pointer_col
            pointer = " " * indent + "^" * max(1, pointer_length)
            parts.append(pointer)

    parts.append("")

    if suggestion:
        parts.append(f"  Hint: {suggestion}")
        parts.append("")

    return "\n".join(parts)
