"""Main parse() orchestrator - coordinates the entire parsing process."""

import re
from typing import Dict, Any

from .errors import format_error
from .preprocessing import extract_imports, extract_metadata, strip_inline_comment
from .blocks import extract_python_block, extract_conditional_block, extract_loop_block
from .content import parse_content_line, parse_choice_line, parse_tags
from .directives import parse_render_line, parse_input_line, extract_multiline_expression
from .validation import (
    BlockStack,
    _cleanup_whitespace,
    _trim_trailing_newlines,
    _determine_initial_passage,
    check_duplicate_passages,
)


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
    block_stack = BlockStack()  # Track open control blocks

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
            # Strip inline comment first
            passage_header, _ = strip_inline_comment(passage_header)
            # Extract tags from passage header
            passage_name, passage_tags = parse_tags(passage_header)

            # Check that all blocks are closed before starting new passage
            block_stack.check_empty(passage_name, i)

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

        # Python block: <<py or @py:
        if line.strip().startswith("<<py") or line.strip().startswith("@py"):
            code, lines_consumed = extract_python_block(lines, i)
            current_passage["execute"].append({"type": "python_block", "code": code})
            i += lines_consumed
            continue

        # Conditional block: <<if or @if:
        if line.strip().startswith("<<if ") or line.strip().startswith("@if "):
            conditional, lines_consumed = extract_conditional_block(lines, i)
            current_passage["content"].append(conditional)
            i += lines_consumed
            continue

        # Loop block: <<for or @for:
        if line.strip().startswith("<<for ") or line.strip().startswith("@for "):
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

        # Variable assignment: ~ var = value or ~ var += value
        if line.startswith("~ ") and current_passage:
            assignment = line[2:].strip()
            # Strip inline comment first
            assignment, _ = strip_inline_comment(assignment)

            # Check for augmented assignment operators (longest first to avoid false matches)
            augmented_op = None
            for op in ["//=", "**=", "+=", "-=", "*=", "/=", "%="]:
                if op in assignment:
                    augmented_op = op
                    break

            if augmented_op:
                # Augmented assignment: expand to regular form
                # Example: count += 1  →  count = count + (1)
                var_name, value_expr = assignment.split(augmented_op, 1)
                var_name = var_name.strip()
                value_expr = value_expr.strip()

                # Check if the VALUE expression is multi-line (before expansion)
                complete_value_expr, lines_consumed = extract_multiline_expression(
                    lines, i, value_expr
                )

                # NOW expand to regular assignment with parentheses for safety
                base_op = augmented_op[:-1]  # Remove trailing '='
                expanded_expr = f"{var_name} {base_op} ({complete_value_expr})"

                # Store as execution command
                current_passage["execute"].append(
                    {"type": "set_var", "var": var_name, "expression": expanded_expr}
                )
                i += lines_consumed

            elif "=" in assignment:
                # Regular assignment (existing logic)
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
            # Check for glue operator <>
            if line.rstrip().endswith("<>"):
                # Remove <> and parse (glue: no newline after)
                content_line = line.rstrip()[:-2]
                content_tokens = parse_content_line(content_line)
                current_passage["content"].extend(content_tokens)
            else:
                # Normal: add newline after content
                content_tokens = parse_content_line(line)
                current_passage["content"].extend(content_tokens)
                current_passage["content"].append({"type": "text", "value": "\n"})
            i += 1
            continue

        # Empty line - just add a newline
        if not line.strip() and current_passage:
            current_passage["content"].append({"type": "text", "value": "\n"})
            i += 1
            continue

        # Unrecognized syntax - likely a typo in a directive
        # Check for common directive-like patterns that don't match known syntax
        if current_passage and line.strip():
            stripped = line.strip()
            # Check for @-directives that look wrong
            if stripped.startswith("@") and not stripped.startswith("@include"):
                # Might be a typo like @iff, @elseif, @endif:, @endfor:, etc.
                raise SyntaxError(format_error(
                    error_type="Syntax Error",
                    line_num=i,
                    lines=lines,
                    message=f"Unrecognized directive: {stripped.split()[0] if ' ' in stripped else stripped}",
                    pointer_length=len(stripped.split()[0] if ' ' in stripped else stripped),
                    suggestion="Check for typos in directives. Valid directives: @if, @elif, @else, @endif, @for, @endfor, @py, @endpy, @include, @render, @input"
                ))

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
