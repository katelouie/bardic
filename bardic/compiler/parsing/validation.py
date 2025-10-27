"""Post-processing validation and cleanup."""

import sys
from typing import Dict, Any, Optional, List, Tuple


class BlockStack:
    """
    Track open control flow blocks for validation.

    Ensures all @if/@for/@py blocks are properly closed and matched.
    """

    def __init__(self):
        """Initialize empty block stack."""
        self.stack: List[Tuple[str, int]] = []  # [(block_type, line_number), ...]

    def push(self, block_type: str, line_num: int) -> None:
        """
        Push a new block onto the stack when opening.

        Args:
            block_type: Type of block ('if', 'for', 'py')
            line_num: Line number where block opens
        """
        self.stack.append((block_type, line_num))

    def pop(self, expected_type: str, line_num: int) -> None:
        """
        Pop a block from the stack when closing.

        Args:
            expected_type: Expected block type ('if', 'for', 'py')
            line_num: Line number where block closes

        Raises:
            SyntaxError: If no matching opening or wrong block type
        """
        if not self.stack:
            raise SyntaxError(
                f"Line {line_num + 1}: Unexpected @end{expected_type}\n"
                f"  No matching @{expected_type} found.\n"
                f"  Hint: Every @end{expected_type} must have a matching @{expected_type}."
            )

        block_type, start_line = self.stack.pop()
        if block_type != expected_type:
            raise SyntaxError(
                f"Line {line_num + 1}: Block mismatch\n"
                f"  Expected @end{block_type} (opened on line {start_line + 1})\n"
                f"  Got: @end{expected_type}\n"
                f"  Hint: Blocks must be closed in the reverse order they were opened."
            )

    def check_empty(self, passage_name: str, line_num: int) -> None:
        """
        Check that all blocks are closed before starting a new passage.

        Args:
            passage_name: Name of the new passage being started
            line_num: Line number of the passage header

        Raises:
            SyntaxError: If there are unclosed blocks
        """
        if self.stack:
            block_type, start_line = self.stack[-1]
            raise SyntaxError(
                f"Line {line_num + 1}: Unclosed @{block_type} block\n"
                f"  Block started on line {start_line + 1}\n"
                f"  Must close with @end{block_type} before new passage ':: {passage_name}'\n"
                f"  Hint: All control blocks must be closed within their passage."
            )


def _cleanup_whitespace(passage: dict[str, Any]) -> None:
    """
    Clean up excessive whitespace around conditionals.

    Removes extra newlines before and after conditional blocks to prevent
    unwanted blank lines in output.

    Args:
        passage: Passage dictionary with 'content' list
    """
    content = passage.get("content", [])
    if not content:
        return

    cleaned = []
    i = 0

    while i < len(content):
        token = content[i]

        # Check if this is a newline token before a conditional
        if (
            token.get("type") == "text"
            and token.get("value") == "\n"
            and i + 1 < len(content)
            and content[i + 1].get("type") == "conditional"
        ):
            # Skip this newline if there's already a newline before it
            if (
                cleaned
                and cleaned[-1].get("type") == "text"
                and cleaned[-1].get("value") == "\n"
            ):
                i += 1
                continue

        # Check if this is a newline after a conditional
        if (
            token.get("type") == "text"
            and token.get("value") == "\n"
            and cleaned
            and cleaned[-1].get("type") == "conditional"
        ):
            # Skip if next token is also a newline (avoid double spacing after conditional)
            if (
                i + 1 < len(content)
                and content[i + 1].get("type") == "text"
                and content[i + 1].get("value") == "\n"
            ):
                i += 1
                continue

        cleaned.append(token)
        i += 1

    passage["content"] = cleaned


def _trim_trailing_newlines(passage: dict[str, Any]) -> None:
    """
    Remove excessive trailing newlines from passage content.

    Keeps at most one trailing newline for clean formatting.

    Args:
        passage: Passage dictionary with 'content' list
    """
    content = passage.get("content", [])
    if not content:
        return

    # Count trailing newline tokens
    trailing_newlines = 0
    for token in reversed(content):
        if token.get("type") == "text" and token.get("value") == "\n":
            trailing_newlines += 1
        else:
            break

    # Keep at most 1 trailing newline, remove the rest
    if trailing_newlines > 1:
        # Remove extra newlines
        for _ in range(trailing_newlines - 1):
            content.pop()


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
    passage_locations: Dict[str, List[int]],
    lines: List[str],
    filename: Optional[str] = None
) -> None:
    """
    Check for duplicate passage names and error with complete summary.

    Args:
        passage_locations: Dict mapping passage names to list of line numbers where defined
        lines: Source code lines (for context in error message)
        filename: Optional filename for error context

    Raises:
        ValueError: If any duplicates found, with summary of ALL duplicates
    """
    # Find all duplicates (passages defined more than once)
    duplicates = {
        name: locations
        for name, locations in passage_locations.items()
        if len(locations) > 1
    }

    if not duplicates:
        return  # No duplicates, all good!

    # Build comprehensive error message
    error_parts = []
    error_parts.append("✗ Duplicate Passage Error")
    if filename:
        error_parts.append(f" in {filename}")
    error_parts.append(":\n")
    error_parts.append(f"  Found {len(duplicates)} passage(s) defined multiple times\n")
    error_parts.append("\n")

    # List each duplicate with all its locations
    for passage_name, locations in sorted(duplicates.items()):
        error_parts.append(f"  Passage '{passage_name}' defined {len(locations)} times:\n")
        for i, line_num in enumerate(locations):
            # Show snippet of that line
            line_content = lines[line_num - 1].strip() if line_num - 1 < len(lines) else ""
            if i == 0:
                error_parts.append(f"    Line {line_num:4}: {line_content}  ← First definition\n")
            else:
                error_parts.append(f"    Line {line_num:4}: {line_content}  ← Duplicate!\n")
        error_parts.append("\n")

    error_parts.append("  Hint: Each passage must have a unique name.\n")
    error_parts.append("        Consider renaming duplicates or removing redundant definitions.\n")

    raise ValueError("".join(error_parts))
