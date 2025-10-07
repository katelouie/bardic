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


def extract_imports(source: str) -> tuple[list[str], str]:
    """
    Extract Python import statements from the beginning of the file.

    Import statemeneets must appear at the *very top* of the file, before any
    passages, includes, or other content.

    Args:
        source: The source text

    Returns:
        Tuple of (import_statements, remaining_source)
    """
    lines = source.split("\n")
    imports = []
    remaining_lines = []

    in_imports_section = True

    for line in lines:
        stripped = line.strip()

        # Empty lines and comments are allow in import section:
        if not stripped or stripped.startswith("#"):
            if in_imports_section:
                imports.append(line)
            else:
                remaining_lines.append(line)

        # Check if this is an import statement
        if stripped.startswith(("import ", "from ")):
            if in_imports_section:
                imports.append(line)
            else:
                # Import after non-import content -- error
                raise ValueError(
                    "Import statements must appear at the top of the file\n"
                    f"Found import after other content: {stripped}"
                )
        else:
            # First non-import, non-empty, non-comment line
            in_imports_section = False
            remaining_lines.append(line)

    return imports, "\n".join(remaining_lines)


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


def extract_python_block(lines: list[str], start_index: int) -> tuple[str, int]:
    """
    Extract a <<py...>> block from lines.

    Args:
        lines: List of all lines
        start_index: Index of the <<py line

    Returns:
        Tuple of (python code, lines consumed)
    """
    # Skip the opening <<py line
    i = start_index + 1
    code_lines = []

    # Find the base indentation (first non-empty line)
    base_indent = None

    while i < len(lines):
        line = lines[i]

        # Check for closing >>
        if line.strip() == ">>":
            break

        # Determine base indentation from first real line
        if base_indent is None and line.strip():
            base_indent = len(line) - len(line.lstrip())

        # Remove base indentation, preserve relative indentation
        if base_indent is not None and line.strip():
            # Remove only the base indentation
            if len(line) >= base_indent and line[:base_indent].strip() == "":
                adjusted_line = line[base_indent:]
            else:
                adjusted_line = line
            code_lines.append(adjusted_line)
        elif not line.strip():
            # Preserve empty lines
            code_lines.append("")
        else:
            # First line or line with no indent
            code_lines.append(line)

        i += 1

    # Join code lines
    code = "\n".join(code_lines)

    # Return code and number of lines consumed (including opening and closing)
    lines_consumed = i - start_index + 1

    return code, lines_consumed


def extract_conditional_block(lines: list[str], start_index: int) -> tuple[dict, int]:
    """
    Extract a <<if>>...<<endif>> block from lines.

    Args:
        lines: list of all lines
        start_index: index of the <<if line

    Returns:
        Tuple of (conditional_structure, lines_consumed)
    """
    conditional = {"type": "conditional", "branches": []}

    current_branch = None
    i = start_index
    nesting_level = 0  # Track nested <<if>> blocks

    while i < len(lines):
        line = lines[i].strip()

        # Check for nested <<if>> (not the opening one)
        if line.startswith("<<if ") and i != start_index:
            # This is a nested conditional - add it to the current branch content
            if current_branch is not None:
                # Recursively extract the nested conditional
                nested_conditional, nested_lines = extract_conditional_block(lines, i)
                current_branch["content"].append(nested_conditional)
                i += nested_lines
                continue

        # Check for opening <<if>> (only at start_index)
        if line.startswith("<<if ") and i == start_index:
            match = re.match(r"<<if\s+(.+?)>>", line)
            if match:
                condition = match.group(1).strip()
                current_branch = {"condition": condition, "content": []}
            i += 1
            continue

        # Check for <<endif>> - might be closing nested or *this* conditional
        if line.startswith("<<endif>>"):
            if nesting_level > 0:
                # This closes a nested conditional, not ours
                nesting_level -= 1
                # Add the endif as text to the current branch
                if current_branch is not None:
                    current_branch["content"].append(
                        {"type": "text", "value": "<<endif>>"}
                    )
                i += 1
                continue
            else:
                # This closes OUR conditional
                # Save final branch
                if current_branch:
                    conditional["branches"].append(current_branch)
                i += 1
                break

        # Check for <<elif condition>> at our level
        if line.startswith("<<elif ") and nesting_level == 0:
            # Save previous branch
            if current_branch:
                conditional["branches"].append(current_branch)

            match = re.match(r"<<elif\s+(.+?)>>", line)
            if match:
                condition = match.group(1).strip()
                current_branch = {"condition": condition, "content": []}
            i += 1
            continue

        # Check for <<else>> at our level
        if line.startswith("<<else>>") and nesting_level == 0:
            # Save previous branch
            if current_branch:
                conditional["branches"].append(current_branch)

            # Else branch always has condition True
            current_branch = {"condition": "True", "content": []}
            i += 1
            continue

        # Regular content line -- add to current branch
        if current_branch is not None:
            # Parse the line for expressions
            content_tokens = parse_content_line(lines[i])
            current_branch["content"].extend(content_tokens)
            # Add newline after content line (same as main parser)
            current_branch["content"].append({"type": "text", "value": "\n"})

        i += 1

    # Calculate lines consumed
    lines_consumed = i - start_index

    return conditional, lines_consumed


def parse(source: str) -> Dict[str, Any]:
    """
    Parse a .bard source string into structured data.

    Args:
        source: The .bard file content as a string

    Returns:
        Dict containing version, initial_passage, and passages
    """
    # Extract imports first
    import_statements, remaining_source = extract_imports(source)

    passages = {}
    current_passage = None
    explicit_start = None

    lines = remaining_source.split("\n")
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

        # Python block: <<py
        if line.strip().startswith("<<py"):
            code, lines_consumed = extract_python_block(lines, i)
            current_passage["execute"].append({"type": "python_block", "code": code})
            i += lines_consumed
            continue

        # Conditional block: <<if
        if line.strip().startswith("<<if "):
            conditional, lines_consumed = extract_conditional_block(lines, i)
            current_passage["content"].append(conditional)
            i += lines_consumed
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

        # Empty line - just add a newline
        if not line.strip() and current_passage:
            current_passage["content"].append({"type": "text", "value": "\n"})
            i += 1
            continue

        i += 1

    # Clean up whitespace in all passages
    for passage in passages.values():
        _cleanup_whitespace(passage)
        _trim_trailing_newlines(passage)

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
        "imports": import_statements,
        "passages": passages,
    }


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
        if (token.get("type") == "text" and
            token.get("value") == "\n" and
            i + 1 < len(content) and
            content[i + 1].get("type") == "conditional"):

            # Skip this newline if there's already a newline before it
            if cleaned and cleaned[-1].get("type") == "text" and cleaned[-1].get("value") == "\n":
                i += 1
                continue

        # Check if this is a newline after a conditional
        if (token.get("type") == "text" and
            token.get("value") == "\n" and
            cleaned and
            cleaned[-1].get("type") == "conditional"):

            # Skip if next token is also a newline (avoid double spacing after conditional)
            if i + 1 < len(content) and content[i + 1].get("type") == "text" and content[i + 1].get("value") == "\n":
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
