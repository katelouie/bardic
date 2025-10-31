"""Error formatting utilities for Bardic parser."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SourceLocation:
    """Maps a line in concatenated source to its original file location."""
    file_path: str          # Original file path
    line_num: int          # Line number in original file (0-indexed)


def format_error(
    error_type: str,
    line_num: int,
    lines: List[str],
    message: str,
    pointer_col: int = 0,
    pointer_length: int = None,
    suggestion: str = None,
    filename: str = None,
    line_map: Optional[List[SourceLocation]] = None
) -> str:
    """
    Format a beautiful error message with context.

    Args:
        error_type: Type of error (e.g., "Syntax Error", "Unclosed Block")
        line_num: Line number where error occurred (0-indexed in concatenated source)
        lines: All source lines (concatenated if using @include)
        message: Main error message
        pointer_col: Column where error starts (for pointer alignment)
        pointer_length: Length of pointer (defaults to rest of line)
        suggestion: Optional hint for how to fix
        filename: Optional filename to include in error (overridden by line_map if provided)
        line_map: Optional source mapping for @include files

    Returns:
        Formatted error string with context and visual pointer
    """
    # Resolve original source location if we have a line map
    if line_map and line_num < len(line_map):
        loc = line_map[line_num]
        display_filename = loc.file_path
        display_line = loc.line_num + 1  # 1-indexed for display
    else:
        display_filename = filename
        display_line = line_num + 1

    # Build header
    parts = []
    parts.append(f"✗ {error_type}")
    if display_filename:
        parts.append(f" in {display_filename}")
    parts.append(f" on line {display_line}:")
    parts.append(f"  {message}")
    parts.append("")

    # Get context lines (±2 around error)
    start = max(0, line_num - 2)
    end = min(len(lines), line_num + 3)

    # Show context with file boundary annotations
    last_file = None
    for i in range(start, end):
        if i >= len(lines):
            break

        # Check if we crossed a file boundary (only when using line_map)
        if line_map and i < len(line_map):
            current_file = line_map[i].file_path
            if last_file is not None and current_file != last_file:
                # Annotate file boundary
                parts.append(f"  {'':4}   --- from {current_file} ---")
            last_file = current_file

            # Use original line number from line_map for display
            display_num = line_map[i].line_num + 1
        else:
            # No line_map, use concatenated line number
            display_num = i + 1

        line = lines[i]
        line_marker = f"  {display_num:4} | "
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
