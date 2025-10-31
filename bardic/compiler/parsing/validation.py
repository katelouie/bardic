"""Post-processing validation and cleanup."""

import sys
import re
from typing import Dict, Any, Optional, List, Tuple

from .errors import format_error


def validate_choice_syntax(
    line: str, line_num: int, lines: List[str], filename: Optional[str] = None,
    line_map: Optional[List] = None
) -> None:
    """
    Validate choice line syntax before parsing.

    Checks for common syntax errors:
    - Missing brackets
    - Missing arrow
    - Unclosed conditionals
    - Invalid targets

    Args:
        line: The choice line to validate (starts with + or *)
        line_num: Line number (0-indexed) for error reporting
        lines: Source lines for error context
        filename: Optional filename for error context

    Raises:
        SyntaxError: If choice syntax is malformed
    """
    from .preprocessing import strip_inline_comment

    # Strip comments and whitespace for analysis
    clean_line, _ = strip_inline_comment(line.strip())

    # Check 1: Must have arrow
    if " -> " not in clean_line:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Missing arrow '->'",
                pointer_length=len(line.strip()),
                suggestion="Choices must specify a target passage with ->\nExpected format: + [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    # Split on arrow to get left side (choice) and right side (target)
    parts = clean_line.split(" -> ", 1)
    choice_part = parts[0]
    target_part = parts[1].strip() if len(parts) > 1 else ""

    # Check 2: Must have opening bracket
    if "[" not in choice_part:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Missing opening bracket '['",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 3: Must have closing bracket
    if "]" not in choice_part:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Missing closing bracket ']'",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 4: Check for conditionals FIRST (to handle nested brackets like {cards[0]})
    # If conditional present, find its boundaries first
    cond_start = -1
    cond_end = -1

    if "{" in choice_part:
        if "}" not in choice_part:
            raise SyntaxError(
                format_error(
                    error_type="Malformed Choice",
                    line_num=line_num,
                    lines=lines,
                    message="Unclosed conditional - missing '}'",
                    pointer_length=len(line.strip()),
                    suggestion="Expected format: + {condition} [Choice text] -> Target\nConditional choices must have matching { and } before the bracket",
                    filename=filename,
                    line_map=line_map,
                )
            )

        # Find matching braces (handle nesting)
        cond_start = choice_part.index("{")
        depth = 0
        for i in range(cond_start, len(choice_part)):
            if choice_part[i] == "{":
                depth += 1
            elif choice_part[i] == "}":
                depth -= 1
                if depth == 0:
                    cond_end = i
                    break

    # Check 5: If } present without {, error
    if "}" in choice_part and "{" not in choice_part:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Found '}' without matching '{'",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + {condition} [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 6: Find choice text brackets (AFTER conditional if present)
    # Look for brackets that are NOT inside the conditional
    search_start = cond_end + 1 if cond_end >= 0 else 0
    remaining = choice_part[search_start:]

    if "[" not in remaining:
        # No bracket after conditional (or at all)
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Missing opening bracket '['",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    if "]" not in remaining:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Missing closing bracket ']'",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 7: Brackets must be in correct order (in remaining part)
    bracket_open = remaining.index("[") + search_start
    bracket_close = remaining.index("]") + search_start
    if bracket_close < bracket_open:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Closing bracket ']' appears before opening bracket '['",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 8: Target must not be empty
    if not target_part:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Missing target passage name",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target\nTarget passage name is required after ->",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 8: Extract target (before any tags/comments)
    # Target is the first word after ->
    target_name = target_part.split()[0] if target_part.split() else ""

    # Check 9: Target should follow passage naming rules (no spaces, etc)
    if " " in target_name:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message=f"Invalid target '{target_name}' contains spaces",
                pointer_length=len(line.strip()),
                suggestion=f"Target names can't contain spaces. Use '{target_name.replace(' ', '_')}' instead.",
                filename=filename,
                line_map=line_map,
            )
        )

    # Check 10: Empty choice text
    text_start = bracket_open + 1
    text_end = bracket_close
    choice_text = choice_part[text_start:text_end].strip()

    if not choice_text:
        raise SyntaxError(
            format_error(
                error_type="Malformed Choice",
                line_num=line_num,
                lines=lines,
                message="Empty choice text - brackets contain nothing",
                pointer_length=len(line.strip()),
                suggestion="Expected format: + [Choice text] -> Target\nChoice text cannot be empty",
                filename=filename,
                line_map=line_map,
            )
        )


def validate_passage_name(
    passage_name: str,
    line_num: int,
    lines: List[str],
    filename: Optional[str] = None,
    line_map: Optional[List] = None
) -> None:
    """
    Validate that a passage name follows strict naming rules.

    Rules:
    - Must start with letter (a-z, A-Z) or underscore (_)
    - Can contain: letters, numbers, underscores, dots
    - Cannot contain: spaces, hyphens, or special characters
    - Cannot start with a number

    Args:
        passage_name: The passage name to validate
        line_num: Line number (0-indexed) for error reporting
        lines: Source lines for error context
        filename: Optional filename for error context
        line_map: Optional source mapping for @include files

    Raises:
        SyntaxError: If passage name violates naming rules
    """
    # Check for empty name
    if not passage_name or passage_name.isspace():
        raise SyntaxError(
            format_error(
                error_type="Invalid Passage Name",
                line_num=line_num,
                lines=lines,
                message="Passage name cannot be empty",
                pointer_length=2,  # Point at ::
                suggestion="Provide a passage name after :: (e.g., :: MyPassage)",
                filename=filename,
                line_map=line_map,
            )
        )

    # Valid pattern: starts with letter or underscore, contains letters/numbers/underscores/dots
    valid_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$")

    if not valid_pattern.match(passage_name):
        # Detect specific problems for helpful error messages
        suggestion = None
        fixed_name = None

        if " " in passage_name:
            # Spaces in name
            fixed_name = passage_name.replace(" ", "_")
            suggestion = f'Replace spaces with underscores: ":: {fixed_name}"'
        elif "-" in passage_name:
            # Hyphens in name
            fixed_name = passage_name.replace("-", "_")
            suggestion = f'Replace hyphens with underscores: ":: {fixed_name}"'
        elif passage_name[0].isdigit():
            # Starts with number
            fixed_name = f"_{passage_name}"
            suggestion = f'Passage names must start with a letter or underscore: ":: {fixed_name}"'
        else:
            # Generic special character error
            # Find the first invalid character
            for i, char in enumerate(passage_name):
                if not (char.isalnum() or char in "_."):
                    suggestion = (
                        f"Invalid character '{char}' at position {i+1}. "
                        f"Passage names can only contain letters, numbers, underscores, and dots."
                    )
                    break

        raise SyntaxError(
            format_error(
                error_type="Invalid Passage Name",
                line_num=line_num,
                lines=lines,
                message=f"'{passage_name}' is not a valid passage name",
                pointer_length=len(passage_name) + 3,  # Include ":: "
                suggestion=suggestion
                or "Passage names must start with a letter or underscore, and contain only letters, numbers, underscores, and dots.",
                filename=filename,
                line_map=line_map,
            )
        )


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
    filename: Optional[str] = None,
    line_map: Optional[List] = None
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
            # line_num is 1-indexed, convert to 0-indexed for line_map lookup
            line_idx = line_num - 1

            # Resolve source location
            if line_map and line_idx < len(line_map):
                loc = line_map[line_idx]
                display_file = loc.file_path
                display_line = loc.line_num + 1  # Convert to 1-indexed
                file_prefix = f" in {display_file}" if display_file != filename else ""
            else:
                display_line = line_num
                file_prefix = ""

            # Show snippet of that line
            line_content = lines[line_idx].strip() if line_idx < len(lines) else ""
            if i == 0:
                error_parts.append(f"    Line {display_line:4}{file_prefix}: {line_content}  ← First definition\n")
            else:
                error_parts.append(f"    Line {display_line:4}{file_prefix}: {line_content}  ← Duplicate!\n")
        error_parts.append("\n")

    error_parts.append("  Hint: Each passage must have a unique name.\n")
    error_parts.append("        Consider renaming duplicates or removing redundant definitions.\n")

    raise ValueError("".join(error_parts))
