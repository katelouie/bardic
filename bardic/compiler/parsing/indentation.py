"""Indentation detection and stripping for content blocks."""


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
