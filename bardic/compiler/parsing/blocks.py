"""Block extraction: conditionals, loops, and Python code blocks."""

import re
from typing import Tuple, Optional

from .errors import format_error
from .indentation import detect_and_strip_indentation
from .content import parse_content_line, parse_choice_line
from .directives import parse_input_line, parse_render_line
from .preprocessing import strip_inline_comment


def extract_python_block(lines: list[str], start_index: int) -> tuple[str, int]:
    """
    Extract Python block - supports <<py>> or @py: syntax.

    Args:
        lines: List of all lines
        start_index: Index of the <<py or @py: line

    Returns:
        Tuple of (python code, lines consumed)
    """
    line = lines[start_index]
    stripped = line.strip()

    # Detect which syntax
    if stripped.startswith("<<py"):
        # Old syntax: <<py ... >>
        return _extract_py_old_syntax(lines, start_index)
    elif stripped.startswith("@py"):
        # New syntax: @py: ... @endpy
        return _extract_py_new_syntax(lines, start_index)
    else:
        raise ValueError("extract_python_block called on non-python line")


def _extract_py_new_syntax(lines: list[str], start_index: int) -> tuple[str, int]:
    """Extract @py: ... @endpy block."""
    line = lines[start_index]

    # Validate @py: has colon
    if line.strip() != "@py:":
        raise SyntaxError(
            f"Line {start_index}: @py statement missing colon\n"
            f"  Expected: @py:\n"
            f"  Got: {line.strip()}"
        )

    code_lines = []
    i = start_index + 1

    while i < len(lines):
        line = lines[i]
        if line.strip() == "@endpy":
            # Found closer
            code = "\n".join(code_lines)
            lines_consumed = i - start_index + 1
            return code, lines_consumed
        else:
            code_lines.append(line)
            i += 1

    # Reached end without finding @endpy
    raise SyntaxError(
        f"Line {start_index}: @py block not closed\n"
        f"  Expected @endpy before end of passage"
    )


def _extract_py_old_syntax(lines: list[str], start_index: int) -> tuple[str, int]:
    """Extract <<py ... >> block (existing logic)."""
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


def extract_conditional_block(
    lines: list[str],
    start_index: int,
    filename: Optional[str] = None,
    line_map: Optional[list] = None
) -> tuple[dict, int]:
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
    found_closer = False  # Track whether we found @endif

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
                    # Check for glue operator <>
                    if line.rstrip().endswith("<>"):
                        # Remove <> and parse (glue: no newline after)
                        content_line = line.rstrip()[:-2]
                        content_tokens = parse_content_line(content_line)
                        current_branch["content"].extend(content_tokens)
                    else:
                        # Normal: add newline after content
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

        # Check for Python block (both syntaxes)
        if (stripped.startswith("<<py") or stripped.startswith("@py")) and current_branch is not None:
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

        # Check for expression statement (~ var = value) inside conditional
        if stripped.startswith("~ ") and current_branch is not None:
            # Dedent lines collected so far
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Parse the assignment (use stripped since line may be indented)
            assignment = stripped[2:].strip()
            # Strip inline comment first
            assignment, _ = strip_inline_comment(assignment)

            # Check for augmented assignment operators
            augmented_op = None
            for op in ["//=", "**=", "+=", "-=", "*=", "/=", "%="]:
                if op in assignment:
                    augmented_op = op
                    break

            if augmented_op:
                # Augmented assignment: expand to regular form
                var_name, value_expr = assignment.split(augmented_op, 1)
                var_name = var_name.strip()
                value_expr = value_expr.strip()

                # Expand to regular assignment
                base_op = augmented_op[:-1]
                expanded_expr = f"{var_name} {base_op} ({value_expr})"

                # Add as set_var token
                current_branch["content"].append(
                    {"type": "set_var", "var": var_name, "expression": expanded_expr}
                )
            elif "=" in assignment:
                # Regular assignment
                var_name, value_expr = assignment.split("=", 1)
                var_name = var_name.strip()
                value_expr = value_expr.strip()

                # Add as set_var token
                current_branch["content"].append(
                    {"type": "set_var", "var": var_name, "expression": value_expr}
                )
            else:
                # Expression statement without assignment (like function call)
                current_branch["content"].append(
                    {"type": "expression_statement", "code": assignment}
                )

            i += 1
            continue

        # Check for nested <<if>> or @if: (not the opening one)
        if (stripped.startswith("<<if ") or stripped.startswith("@if ")) and i != start_index:
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
                nested_conditional, nested_lines = extract_conditional_block(lines, i, filename, line_map)
                current_branch["content"].append(nested_conditional)
                i += nested_lines
                continue

        # Check for nested <<for>> or @for: loop
        if (stripped.startswith("<<for ") or stripped.startswith("@for ")) and current_branch is not None:
            # Dedent lines collected so far before adding nested loop
            if current_branch_lines:
                dedented = detect_and_strip_indentation(current_branch_lines)
                for dedented_line in dedented:
                    content_tokens = parse_content_line(dedented_line)
                    current_branch["content"].extend(content_tokens)
                    current_branch["content"].append({"type": "text", "value": "\n"})
                current_branch_lines = []  # Reset

            # Extract nested loop
            nested_loop, nested_lines = extract_loop_block(lines, i, filename, line_map)
            current_branch["content"].append(nested_loop)
            i += nested_lines
            continue

        # Check for opening <<if>> or @if: (only at start_index)
        if (stripped.startswith("<<if ") or stripped.startswith("@if ")) and i == start_index:
            if stripped.startswith("@if "):
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # New syntax: @if condition:
                match = re.match(r"@if\s+(.+?):", stripped)
                if not match:
                    raise SyntaxError(
                        f"Line {i}: @if statement missing colon\n"
                        f"  Expected: @if condition:\n"
                        f"  Got: {stripped}"
                    )
                condition = match.group(1).strip()
            else:
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # Old syntax: <<if condition>>
                match = re.match(r"<<if\s+(.+?)>>", stripped)
                if match:
                    condition = match.group(1).strip()
            current_branch = {"condition": condition, "content": []}
            current_branch_lines = []
            i += 1
            continue

        # Check for common typo: @endif: (with colon)
        if stripped == "@endif:":
            raise SyntaxError(format_error(
                error_type="Syntax Error",
                line_num=i,
                lines=lines,
                message="@endif should not have a colon",
                pointer_length=7,
                suggestion="Only opening tags (@if, @elif, @else) use colons. Closing tags (@endif, @endfor, @endpy) do not.",
                filename=filename,
                line_map=line_map,
            ))

        # Check for <<endif>> or @endif - might be closing nested or *this* conditional
        if stripped.startswith("<<endif>>") or stripped == "@endif":
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
                            # Check for glue operator <>
                            if dedented_line.rstrip().endswith("<>"):
                                # Remove <> and parse (glue: no newline after)
                                content_line = dedented_line.rstrip()[:-2]
                                content_tokens = parse_content_line(content_line)
                                current_branch["content"].extend(content_tokens)
                            else:
                                # Normal: add newline after content
                                content_tokens = parse_content_line(dedented_line)
                                current_branch["content"].extend(content_tokens)
                                current_branch["content"].append({"type": "text", "value": "\n"})
                    # Always append branch (even if it only has directives, no text)
                    conditional["branches"].append(current_branch)
                found_closer = True
                i += 1
                break

        # Check for <<elif condition>> or @elif condition: at our level
        if (stripped.startswith("<<elif ") or stripped.startswith("@elif ")) and nesting_level == 0:
            if stripped.startswith("@elif "):
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # New syntax: @elif condition:
                match = re.match(r"@elif\s+(.+?):", stripped)
                if not match:
                    raise SyntaxError(
                        f"Line {i}: @elif statement missing colon\n"
                        f"  Expected: @elif condition:\n"
                        f"  Got: {stripped}"
                    )
                condition = match.group(1).strip()
            else:
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # Old syntax: <<elif condition>>
                match = re.match(r"<<elif\s+(.+?)>>", stripped)
                if match:
                    condition = match.group(1).strip()
            finalize_and_start_new_branch(condition)
            i += 1
            continue

        # Check for <<else>> or @else: at our level
        if (stripped.startswith("<<else>>") or stripped.startswith("@else")) and nesting_level == 0:
            if stripped.startswith("@else"):
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # New syntax: @else: (with colon)
                if stripped.strip() != "@else:":
                    raise SyntaxError(
                        f"Line {i}: @else statement missing colon\n"
                        f"  Expected: @else:\n"
                        f"  Got: {stripped}"
                    )
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
            choice = parse_choice_line(stripped, {})  # Use stripped line (no indentation)
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

    # Check that we found the closing @endif
    if not found_closer:
        raise SyntaxError(format_error(
            error_type="Unclosed Block",
            line_num=start_index,
            lines=lines,
            message="@if block never closed",
            pointer_length=len(lines[start_index].strip()) if start_index < len(lines) else 1,
            suggestion="Every @if must have a matching @endif before the end of the passage",
            filename=filename,
            line_map=line_map,
        ))

    # Calculate lines consumed
    lines_consumed = i - start_index

    return conditional, lines_consumed


def extract_loop_block(
    lines: list[str],
    start_index: int,
    filename: Optional[str] = None,
    line_map: Optional[list] = None
) -> tuple[dict, int]:
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
    found_closer = False  # Track whether we found @endfor

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for opening <<for>> or @for: (only at start_index)
        if (stripped.startswith("<<for ") or stripped.startswith("@for ")) and i == start_index:
            if stripped.startswith("@for "):
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # New syntax: @for variable in collection:
                match = re.match(r"@for\s+(.+?)\s+in\s+(.+?):", stripped)
                if not match:
                    raise SyntaxError(
                        f"Line {i}: @for statement missing colon\n"
                        f"  Expected: @for item in list:\n"
                        f"  Got: {stripped}"
                    )
                loop["variable"] = match.group(1).strip()
                loop["collection"] = match.group(2).strip()
            else:
                # Strip inline comment first
                stripped, _ = strip_inline_comment(stripped)
                # Old syntax: <<for variable in collection>>
                match = re.match(r"<<for\s+(.+?)\s+in\s+(.+?)>>", stripped)
                if match:
                    loop["variable"] = match.group(1).strip()
                    loop["collection"] = match.group(2).strip()
                else:
                    raise ValueError(f"Invalid for loop syntax: {stripped}")

            loop_started = True
            i += 1
            continue

        # Check for common typo: @endfor: (with colon)
        if stripped == "@endfor:":
            raise SyntaxError(format_error(
                error_type="Syntax Error",
                line_num=i,
                lines=lines,
                message="@endfor should not have a colon",
                pointer_length=8,
                suggestion="Only opening tags (@for) use colons. Closing tags (@endfor) do not.",
                filename=filename,
                line_map=line_map,
            ))

        # Check for <<endfor>> or @endfor
        if stripped.startswith("<<endfor>>") or stripped == "@endfor":
            found_closer = True
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

            # Check for Python block (both syntaxes)
            if stripped.startswith("<<py") or stripped.startswith("@py"):
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

            # Check for expression statement (~ var = value) inside loop
            if line.startswith("~ "):
                # Parse the assignment
                assignment = line[2:].strip()
                # Strip inline comment first
                assignment, _ = strip_inline_comment(assignment)

                # Check for augmented assignment operators
                augmented_op = None
                for op in ["//=", "**=", "+=", "-=", "*=", "/=", "%="]:
                    if op in assignment:
                        augmented_op = op
                        break

                if augmented_op:
                    # Augmented assignment: expand to regular form
                    var_name, value_expr = assignment.split(augmented_op, 1)
                    var_name = var_name.strip()
                    value_expr = value_expr.strip()

                    # Expand to regular assignment
                    base_op = augmented_op[:-1]
                    expanded_expr = f"{var_name} {base_op} ({value_expr})"

                    # Add as set_var token
                    loop["content"].append(
                        {"type": "set_var", "var": var_name, "expression": expanded_expr}
                    )
                elif "=" in assignment:
                    # Regular assignment
                    var_name, value_expr = assignment.split("=", 1)
                    var_name = var_name.strip()
                    value_expr = value_expr.strip()

                    # Add as set_var token
                    loop["content"].append(
                        {"type": "set_var", "var": var_name, "expression": value_expr}
                    )
                else:
                    # Expression statement without assignment (like function call)
                    loop["content"].append(
                        {"type": "expression_statement", "code": assignment}
                    )

                j += 1
                continue

            # Check for nested <<for>> or @for: loop
            if stripped.startswith("<<for ") or stripped.startswith("@for "):
                # Recursively extract nested loop from dedented context
                # NOTE: dedented_lines is a subset, can't use line_map directly
                nested_loop, nested_lines_consumed = extract_loop_block(dedented_lines, j, filename, None)
                loop["content"].append(nested_loop)
                j += nested_lines_consumed
                continue

            # Check for nested <<if>> or @if: inside loop
            if stripped.startswith("<<if ") or stripped.startswith("@if "):
                # Recursively extract nested conditional from dedented context
                # NOTE: dedented_lines is a subset, can't use line_map directly
                nested_conditional, nested_lines_consumed = extract_conditional_block(
                    dedented_lines, j, filename, None
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
                choice = parse_choice_line(stripped, {})  # Use stripped line (no indentation)
                if choice:
                    if "choices" not in loop:
                        loop["choices"] = []
                    loop["choices"].append(choice)
                j += 1
                continue

            # Regular content line
            # Check for glue operator <>
            if line.rstrip().endswith("<>"):
                # Remove <> and parse (glue: no newline after)
                content_line = line.rstrip()[:-2]
                content_tokens = parse_content_line(content_line)
                loop["content"].extend(content_tokens)
            else:
                # Normal: add newline after content
                content_tokens = parse_content_line(line)
                loop["content"].extend(content_tokens)
                loop["content"].append({"type": "text", "value": "\n"})
            j += 1

    # Check that we found the closing @endfor
    if not found_closer:
        raise SyntaxError(format_error(
            error_type="Unclosed Block",
            line_num=start_index,
            lines=lines,
            message="@for block never closed",
            pointer_length=len(lines[start_index].strip()) if start_index < len(lines) else 1,
            suggestion="Every @for must have a matching @endfor before the end of the passage",
            filename=filename,
            line_map=line_map,
        ))

    # Calculate lines consumed
    lines_consumed = i - start_index

    return loop, lines_consumed
