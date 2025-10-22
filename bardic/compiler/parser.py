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


def extract_metadata(source: str) -> tuple[dict[str, str], str]:
    """
    Extract @metadata block from the beginning of the file.

    Metadata must appear after imports but before any passages or other content.
    Format is simple key-value pairs:
        @metadata
          key: value
          another_key: another value

    Args:
        source: The source text (after imports have been extracted)

    Returns:
        Tuple of (metadata_dict, remaining_source)
    """
    lines = source.split("\n")
    metadata = {}
    remaining_lines = []

    in_metadata_block = False
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for @metadata directive
        if stripped == "@metadata":
            in_metadata_block = True
            i += 1
            continue

        # If we're in the metadata block
        if in_metadata_block:
            # Empty lines are allowed in metadata block
            if not stripped:
                i += 1
                continue

            # Check if this line looks like a key-value pair (indented, has colon)
            if line.startswith((" ", "\t")) and ":" in stripped:
                # Parse key: value
                key, value = stripped.split(":", 1)
                key = key.strip()
                value = value.strip()
                metadata[key] = value
                i += 1
                continue
            else:
                # Non-indented line or no colon - end of metadata block
                in_metadata_block = False
                # Fall through to add this line to remaining_lines

        # Not in metadata block - add to remaining lines
        remaining_lines.append(line)
        i += 1

    return metadata, "\n".join(remaining_lines)


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


def detect_and_strip_indentation(lines: list[str]) -> list[str]:
    """
    Detect base indentation from first non-empty line and strip it from all lines.

    This allows writers to indent content inside conditionals/loops for readability
    while ensuring the output doesn't have extra leading spaces.

    Key insight: Stripping the SAME amount from every line preserves relative
    indentation (critical for Python code blocks).

    Args:
        lines: List of lines to dedent

    Returns:
        List of dedented lines
    """
    if not lines:
        return lines

    # Find base indentation from first non-empty line
    base_indent = None
    for line in lines:
        if line.strip():  # Non-empty line
            # Count leading spaces/tabs
            base_indent = len(line) - len(line.lstrip())
            break

    # If all lines are empty, return as-is
    if base_indent is None:
        return lines

    # Strip base indentation from all lines
    dedented = []
    for line in lines:
        if not line.strip():
            # Empty line - preserve as-is
            dedented.append(line)
        else:
            # Check if line has enough indentation
            leading_space = len(line) - len(line.lstrip())
            if leading_space >= base_indent:
                # Strip exactly base_indent characters
                dedented.append(line[base_indent:])
            else:
                # Line has less indent than base - leave as-is
                # (This shouldn't happen with properly formatted code)
                dedented.append(line)

    return dedented


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

    Automatically strips base indentation from content for readability.

    Args:
        lines: list of all lines
        start_index: index of the <<if line

    Returns:
        Tuple of (conditional_structure, lines_consumed)
    """
    conditional = {"type": "conditional", "branches": []}

    current_branch = None
    current_branch_lines = []  # Collect content lines for this branch
    i = start_index
    nesting_level = 0  # Track nested <<if>> blocks

    def finalize_and_start_new_branch(condition_str):
        """Helper to finalize current branch and start a new one."""
        nonlocal current_branch, current_branch_lines

        # Finalize previous branch
        if current_branch:
            # Process text lines if they exist
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                # Parse dedented content
                for line in dedented:
                    content_tokens = parse_content_line(line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
            # Always append branch (even if it only has directives, no text)
            conditional["branches"].append(current_branch)

        # Start new branch
        current_branch = {"condition": condition_str, "content": []}
        current_branch_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip comment lines
        if stripped.startswith("#"):
            i += 1
            continue

        # Check for Python block
        if stripped.startswith("<<py") and current_branch is not None:
            # Dedent lines collected so far before adding Python block
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Extract Python block and add it to branch content
            # It will be executed during rendering (when this branch is evaluated)
            code, lines_consumed = extract_python_block(lines, i)
            current_branch["content"].append({"type": "python_block", "code": code})
            i += lines_consumed
            continue

        # Check for @input directive inside conditional
        if stripped.startswith("@input") and current_branch is not None:
            # Dedent lines collected so far
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Parse and add input directive
            directive = parse_input_line(line)
            if directive:
                current_branch["content"].append(directive)
            i += 1
            continue

        # Check for @render directive inside conditional
        if stripped.startswith("@render") and current_branch is not None:
            # Dedent lines collected so far
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Parse and add render directive
            directive = parse_render_line(line)
            if directive:
                current_branch["content"].append(directive)
            i += 1
            continue

        # Check for nested <<if>> (not the opening one)
        if stripped.startswith("<<if ") and i != start_index:
            # This is a nested conditional - recursively extract it
            if current_branch is not None:
                # Dedent lines collected so far before adding nested structure
                if current_branch_lines:
                    dedented = detect_and_strip_indentation(current_branch_lines)
                    for dedented_line in dedented:
                        content_tokens = parse_content_line(dedented_line)
                        current_branch["content"].extend(content_tokens)
                        current_branch["content"].append({"type": "text", "value": "\n"})
                    current_branch_lines = []  # Reset

                # Now extract nested conditional
                nested_conditional, nested_lines = extract_conditional_block(lines, i)
                current_branch["content"].append(nested_conditional)
                i += nested_lines
                continue

        # Check for nested <<for>> loop
        if stripped.startswith("<<for ") and current_branch is not None:
            # Dedent lines collected so far before adding nested loop
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Extract nested loop
            nested_loop, nested_lines = extract_loop_block(lines, i)
            current_branch["content"].append(nested_loop)
            i += nested_lines
            continue

        # Check for opening <<if>> (only at start_index)
        if stripped.startswith("<<if ") and i == start_index:
            match = re.match(r"<<if\s+(.+?)>>", stripped)
            if match:
                condition = match.group(1).strip()
                current_branch = {"condition": condition, "content": []}
                current_branch_lines = []
            i += 1
            continue

        # Check for <<endif>> - might be closing nested or *this* conditional
        if stripped.startswith("<<endif>>"):
            if nesting_level > 0:
                # This closes a nested conditional, not ours
                nesting_level -= 1
                # Add to content lines (will be parsed when branch finalizes)
                if current_branch is not None:
                    current_branch_lines.append(line)
                i += 1
                continue
            else:
                # This closes OUR conditional
                # Finalize current branch
                if current_branch:
                    # Process text lines if they exist
                    if current_branch_lines:
                        dedented = detect_and_strip_indentation(current_branch_lines)
                        for dedented_line in dedented:
                            content_tokens = parse_content_line(dedented_line)
                            current_branch["content"].extend(content_tokens)
                            current_branch["content"].append({"type": "text", "value": "\n"})
                    # Always append branch (even if it only has directives, no text)
                    conditional["branches"].append(current_branch)
                i += 1
                break

        # Check for <<elif condition>> at our level
        if stripped.startswith("<<elif ") and nesting_level == 0:
            match = re.match(r"<<elif\s+(.+?)>>", stripped)
            if match:
                condition = match.group(1).strip()
                finalize_and_start_new_branch(condition)
            i += 1
            continue

        # Check for <<else>> at our level
        if stripped.startswith("<<else>>") and nesting_level == 0:
            finalize_and_start_new_branch("True")
            i += 1
            continue

        # Check for jump inside conditional
        if stripped.startswith("->"):
            match = re.match(r"->\s*([\w.]+)", stripped)
            if match and current_branch is not None:
                target = match.group(1)
                current_branch["content"].append({"type": "jump", "target": target})
            i += 1
            continue

        # Check for choices inside conditional
        if (stripped.startswith("+") or stripped.startswith("*")) and current_branch is not None:
            # Dedent lines collected so far before adding choice
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Parse choice and add to conditional's branch
            choice = parse_choice_line(line, {})  # Pass empty dict for passage (not used)
            if choice:
                if "choices" not in current_branch:
                    current_branch["choices"] = []
                current_branch["choices"].append(choice)
            i += 1
            continue

        # Regular content line -- collect for later dedenting
        if current_branch is not None:
            current_branch_lines.append(line)

        i += 1

    # Calculate lines consumed
    lines_consumed = i - start_index

    return conditional, lines_consumed


def extract_loop_block(lines: list[str], start_index: int) -> tuple[dict, int]:
    """
    Extract a <<for>> ... <<endfor>> block from lines.

    Automatically strips base indentation from content for readability.

    Args:
        lines: List of all lines
        start_index: Index of the <<for line

    Returns:
        Tuple of (loop_structure, lines_consumed)
    """
    loop = {"type": "for_loop", "variable": None, "collection": None, "content": []}

    loop_raw_lines = []  # Collect raw lines for dedenting
    i = start_index
    loop_started = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for opening <<for>> (only at start_index)
        if stripped.startswith("<<for ") and i == start_index:
            # Parse: <<for variable in collection>>
            match = re.match(r"<<for\s+(.+?)\s+in\s+(.+?)>>", stripped)

            if match:
                loop["variable"] = match.group(1).strip()
                loop["collection"] = match.group(2).strip()
                loop_started = True
            else:
                raise ValueError(f"Invalid for loop syntax: {stripped}")

            i += 1
            continue

        # Check for <<endfor>>
        if stripped.startswith("<<endfor>>"):
            i += 1
            break

        # Regular content line - collect for later dedenting
        if loop_started:
            loop_raw_lines.append(line)

        i += 1

    # Now dedent and parse the loop content
    if loop_raw_lines:
        dedented_lines = detect_and_strip_indentation(loop_raw_lines)

        # Parse dedented lines
        j = 0
        while j < len(dedented_lines):
            line = dedented_lines[j]
            stripped = line.strip()

            # Skip comment lines
            if stripped.startswith("#"):
                j += 1
                continue

            # Check for Python block
            if stripped.startswith("<<py"):
                # Extract Python block and add it to loop content
                # It will be executed during rendering (for each iteration)
                code, lines_consumed = extract_python_block(dedented_lines, j)
                loop["content"].append({"type": "python_block", "code": code})
                j += lines_consumed
                continue

            # Check for @input directive inside loop
            if stripped.startswith("@input"):
                directive = parse_input_line(line)
                if directive:
                    loop["content"].append(directive)
                j += 1
                continue

            # Check for @render directive inside loop
            if stripped.startswith("@render"):
                directive = parse_render_line(line)
                if directive:
                    loop["content"].append(directive)
                j += 1
                continue

            # Check for nested <<for>> loop
            if stripped.startswith("<<for "):
                # Recursively extract nested loop from dedented context
                nested_loop, nested_lines_consumed = extract_loop_block(dedented_lines, j)
                loop["content"].append(nested_loop)
                j += nested_lines_consumed
                continue

            # Check for nested <<if>> inside loop
            if stripped.startswith("<<if "):
                # Recursively extract nested conditional from dedented context
                nested_conditional, nested_lines_consumed = extract_conditional_block(
                    dedented_lines, j
                )
                loop["content"].append(nested_conditional)
                j += nested_lines_consumed
                continue

            # Check for jump inside loop
            if stripped.startswith("->"):
                match = re.match(r"->\s*([\w.]+)", stripped)
                if match:
                    target = match.group(1)
                    loop["content"].append({"type": "jump", "target": target})
                j += 1
                continue

            # Check for choices inside loop
            if stripped.startswith("+") or stripped.startswith("*"):
                choice = parse_choice_line(line, {})  # Pass empty dict for passage (not used)
                if choice:
                    if "choices" not in loop:
                        loop["choices"] = []
                    loop["choices"].append(choice)
                j += 1
                continue

            # Regular content line
            content_tokens = parse_content_line(line)
            loop["content"].extend(content_tokens)
            # Add newline after content line
            loop["content"].append({"type": "text", "value": "\n"})
            j += 1

    # Calculate lines consumed
    lines_consumed = i - start_index

    return loop, lines_consumed


def parse(source: str) -> Dict[str, Any]:
    """
    Parse a .bard source string into structured data.

    Args:
        source: The .bard file content as a string

    Returns:
        Dict containing version, initial_passage, metadata, and passages
    """
    # Extract imports first
    import_statements, remaining_source = extract_imports(source)

    # Extract metadata second (after imports, before passages)
    metadata, remaining_source = extract_metadata(remaining_source)

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

        # Passage Header: :: PassageName ^TAG1 ^TAG2
        if line.startswith(":: "):
            passage_header = line[3:].strip()
            # Extract tags from passage header
            passage_name, passage_tags = parse_tags(passage_header)
            current_passage = {
                "id": passage_name,
                "content": [],
                "choices": [],
                "execute": [],
                "tags": passage_tags,  # Store passage-level tags
            }
            passages[passage_name] = current_passage
            i += 1
            continue

        # Skip if not in a passage
        if not current_passage:
            i += 1
            continue

        # Comment lines (start with #)
        if line.strip().startswith("#"):
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

        # Loop block: <<for
        if line.strip().startswith("<<for "):
            loop, lines_consumed = extract_loop_block(lines, i)
            current_passage["content"].append(loop)
            i += lines_consumed
            continue

        # Render directive: @render or @render:framework
        if line.strip().startswith("@render"):
            directive = parse_render_line(line)
            if directive:
                current_passage["content"].append(directive)
            i += 1
            continue

        # Input directive: @input
        if line.strip().startswith("@input"):
            directive = parse_input_line(line)
            if directive:
                # Store in passage for later access by engine
                if "input_directives" not in current_passage:
                    current_passage["input_directives"] = []
                current_passage["input_directives"].append(directive)
            i += 1
            continue

        # Immediate jump to target
        if line.strip().startswith("->"):
            match = re.match(r"->\s*([\w.]+)", line.strip())
            if match:
                target = match.group(1)
                current_passage["content"].append({"type": "jump", "target": target})
            i += 1
            continue

        # Variable assignment: ~ var = value
        if line.startswith("~ ") and current_passage:
            assignment = line[2:].strip()
            if "=" in assignment:
                var_name, value_expr = assignment.split("=", 1)
                var_name = var_name.strip()
                value_expr = value_expr.strip()

                # Check if this is a multi-line expression
                complete_expr, lines_consumed = extract_multiline_expression(
                    lines, i, value_expr
                )

                # Store as execution command
                current_passage["execute"].append(
                    {"type": "set_var", "var": var_name, "expression": complete_expr}
                )
                i += lines_consumed
            else:
                i += 1
            continue

        # Choice: +/* [Text] -> Target or +/* {condition} [Text] -> Target
        if line.startswith("+ ") or line.startswith("* "):
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
        "metadata": metadata,
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
    """
    # Extract tags first
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
        "text": choice_text,
        "target": target,
        "condition": condition,
        "sticky": sticky,
        "tags": tags,
    }


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
    Parse a content line with {variable} interpolation and optional tags.

    Returns list of content tokens (text and expressions).
    Tags are attached to the last token in the line.
    """
    # Extract tags first
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


def parse_render_line(line: str) -> Optional[dict]:
    """
    Parse a complete @render line including framwork hint detection.

    Handles:
        @render my_function(args)
        @render:react my_function(args)
        @render simple_function

    Args:
        line: The full line of the story file

    Returns:
        Parsed directive dict, or None if invalid
    """
    # Must start with @render
    if not line.strip().startswith("@render"):
        return None

    # Extract everything after "@render"
    after_render = line.strip()[7:]  # Skip '@render'

    framework_hint = None
    directive_str = None

    if after_render.startswith(":"):
        # Pattern: :framework directive_name(args)
        match = re.match(r"^:(\w+)\s+(.+)$", after_render)
        if match:
            framework_hint = match.group(1)
            directive_str = match.group(2)
        else:
            print(f"Warning: Invalid @render:framework syntax: {line.strip()}")
            return None
    elif after_render.strip():
        # No framework hint, just the directive
        directive_str = after_render.strip()
    else:
        print(f"Warning: Empty @render directive: {line.strip()}")
        return None

    # Parse the directive string and arguments
    directive = parse_render_directive(directive_str)
    if not directive:
        return None

    # Add framework hint
    directive["framework_hint"] = framework_hint

    return directive


def parse_render_directive(directive_str: str) -> Optional[dict]:
    """
    Parse a render directive with optional framework hint.

    Syntax:
        @render directive_name(args) # generic
        @render:react directive_name(args) # react convenience
        @render:unity directive_name(args) # unity convenience

    Examples:
        render_spread(cards, layout="celtic") # generic
        :react render_card_detail(card, pos="past") # react-optimized
        :unity spawn_card(card) # unity-optimized

    Args:
        directive_str: The text after '@render' or '@render:'

    Returns:
        Dict with type='render_directive', name, framework_hint, and args
    """
    directive_str = directive_str.strip()

    # Pattern: function_name(args) or function_name
    match = re.match(r"^(\w+)(?:\((.*)\))?$", directive_str)

    if not match:
        print(f"Warning: Invalid directive syntax: {directive_str}")
        return None

    name = match.group(1)
    args = match.group(2) if match.group(2) else ""

    return {"type": "render_directive", "name": name, "args": args.strip()}


def extract_multiline_expression(
    lines: list[str], start_index: int, initial_expr: str
) -> tuple[str, int]:
    """
    Extract a multi-line expression that starts with an opening bracket.

    Handles:
    - Lists: [...]
    - Dicts: {...}
    - Tuples: (...)

    Args:
        lines: All lines in the passage
        start_index: Index of the line with the opening bracket
        initial_expr: The expression from the first line (e.g. "[")

    Returns:
        Tuple of (complete_expression, lines_consumed)
    """
    # Check if this might be a multi-line expression
    stripped = initial_expr.strip()

    if not any(stripped.endswith(c) for c in ["[", "{", "("]):
        # not a multi-line expression, return as-is
        return initial_expr, 1

    # Track bracket nesting
    bracket_stack = []
    bracket_pairs = {"[": "]", "{": "}", "(": ")"}
    reverse_pairs = {"]": "[", "}": "{", ")": "("}

    # Add opening brackets from initial expression
    for char in stripped:
        if char in bracket_pairs:
            bracket_stack.append(char)

    # Start collecting lines
    expr_lines = [initial_expr]
    i = start_index + 1

    # Continue until brackets are balanced
    while i < len(lines) and bracket_stack:
        line = lines[i]

        # Track brackets in this line
        for char in line:
            if char in bracket_pairs:
                bracket_stack.append(char)
            elif char in reverse_pairs:
                # Closing bracket
                if bracket_stack and bracket_stack[-1] == reverse_pairs[char]:
                    bracket_stack.pop()
                else:
                    # Mismatched bracket - stop here
                    break

        expr_lines.append(line)
        i += 1

        # If brackets are balanced, we're done
        if not bracket_stack:
            break

    # Join all lines preserving structure
    complete_expr = "\n".join(expr_lines)
    lines_consumed = i - start_index

    return complete_expr, lines_consumed


def parse_input_line(line: str) -> Optional[dict]:
    """
    Parse an @input directive for text input.

    Syntax:
        @input name="variable_name"
        @input name="variable_name" placeholder="hint text"
        @input name="variable_name" placeholder="hint" label="Display Label"

    Args:
        line: The full line containing @input directive

    Returns:
        Dict with type='input', name, optional placeholder and label, or None if invalid
    """
    # Must start with @input
    if not line.strip().startswith("@input"):
        return None

    # Extract everything after "@input"
    after_input = line.strip()[6:].strip()  # Skip '@input'

    if not after_input:
        print(f"Warning: Empty @input directive: {line.strip()}")
        return None

    # Parse name="value" style attributes
    # Pattern: name="variable" placeholder="text" label="Label"
    input_spec = {"type": "input"}

    # Extract all key="value" pairs
    attr_pattern = r'(\w+)="([^"]*)"'
    matches = re.findall(attr_pattern, after_input)

    for key, value in matches:
        input_spec[key] = value

    # Validate that 'name' is present (required)
    if 'name' not in input_spec:
        print(f"Warning: @input directive missing 'name' attribute: {line.strip()}")
        return None

    # Set defaults
    if 'label' not in input_spec:
        # Default label to capitalized name
        input_spec['label'] = input_spec['name'].replace('_', ' ').title()

    if 'placeholder' not in input_spec:
        input_spec['placeholder'] = ''

    return input_spec
