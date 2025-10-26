"""File I/O for parsing."""

from typing import Dict, Any

from .preprocessing import resolve_includes


def parse_file(filepath: str) -> Dict[str, Any]:
    """
    Parse a .bard file from disk, resolving includes.

    Args:
        filepath: Path to the .bard file

    Returns:
        Parsed story structure
    """
    # Import here to avoid circular dependency
    from .core import parse

    # Read the source file
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    # Resolve any includes first
    resolved_source = resolve_includes(source, filepath)

    # Then parse everything else normally
    return parse(resolved_source)
