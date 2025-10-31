"""Preprocessing: imports, metadata, includes, and comment stripping."""

from pathlib import Path
from typing import Optional

from .errors import SourceLocation


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


def strip_inline_comment(line: str) -> tuple[str, str]:
    """
    Remove inline // comment from a line.

    Handles escaped \\// (literal //).

    Args:
        line: The line to process

    Returns:
        Tuple of (content_without_comment, comment_text)

    Examples:
        >>> strip_inline_comment("text // comment")
        ('text ', '// comment')
        >>> strip_inline_comment("text \\\\// not")
        ('text // not', '')
        >>> strip_inline_comment("// just comment")
        ('', '// just comment')
    """
    result = []
    comment = ""
    i = 0

    while i < len(line):
        # Check for escaped \\//
        if i < len(line) - 2 and line[i:i+3] == '\\//':
            # Escaped: add literal //
            result.append('//')
            i += 3
            continue

        # Check for //= operator (NOT a comment!)
        if i < len(line) - 2 and line[i:i+3] == '//=':
            # Floor division assignment operator - not a comment
            result.append('//=')
            i += 3
            continue

        # Check for comment start //
        if i < len(line) - 1 and line[i:i+2] == '//':
            # Found comment - rest of line is comment
            comment = line[i:]
            break

        # Regular character
        result.append(line[i])
        i += 1

    content = ''.join(result)
    return content, comment


def resolve_includes(
    source: str, base_path: str, seen: Optional[set] = None
) -> tuple[str, list[SourceLocation]]:
    """
    Resolve @include directives recursively and build source line mapping.

    Args:
        source: The source text with potential @include directives
        base_path: Path to the file being processed (for relative includes)
        seen: Set of already-included files (to detect circular includes)

    Returns:
        Tuple of (resolved_source, line_map) where line_map[i] maps concatenated
        line i to its original source file and line number

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
    line_map = []

    for line_idx, line in enumerate(lines):
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
                resolved_content, included_map = resolve_includes(
                    included_content,
                    str(full_path),
                    seen.copy(),  # Pass a copy so each branch tracks separately
                )

                # Add the resolved content and its line mappings
                result.append(resolved_content)
                line_map.extend(included_map)

            except FileNotFoundError:
                raise FileNotFoundError(
                    f"Include file not found: {include_path}\n"
                    f"  Looking for: {full_path}\n"
                    f"  Included from: {base_path}\n"
                )

        else:
            # Regular line -- keep it and track its source location
            result.append(line)
            line_map.append(SourceLocation(
                file_path=base_path,
                line_num=line_idx  # 0-indexed
            ))

    return "\n".join(result), line_map
