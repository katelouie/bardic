"""Bardic parsing modules - organized by functionality."""

# Error handling
from .errors import format_error

# Preprocessing
from .preprocessing import (
    extract_imports,
    extract_metadata,
    resolve_includes,
    strip_inline_comment,
)

# Indentation handling
from .indentation import detect_and_strip_indentation

# Block extraction
from .blocks import (
    extract_python_block,
    extract_conditional_block,
    extract_loop_block,
)

# Content parsing
from .content import (
    parse_content_line,
    parse_choice_line,
    parse_tags,
    parse_value,
)

# Directives
from .directives import (
    parse_render_line,
    parse_render_directive,
    parse_input_line,
    extract_multiline_expression,
)

# Validation and cleanup
from .validation import (
    check_duplicate_passages,
    _cleanup_whitespace,
    _trim_trailing_newlines,
    _determine_initial_passage,
)

# File I/O
from .io import parse_file

# Main parser
from .core import parse


__all__ = [
    # Errors
    'format_error',
    # Preprocessing
    'extract_imports',
    'extract_metadata',
    'resolve_includes',
    'strip_inline_comment',
    # Indentation
    'detect_and_strip_indentation',
    # Blocks
    'extract_python_block',
    'extract_conditional_block',
    'extract_loop_block',
    # Content
    'parse_content_line',
    'parse_choice_line',
    'parse_tags',
    'parse_value',
    # Directives
    'parse_render_line',
    'parse_render_directive',
    'parse_input_line',
    'extract_multiline_expression',
    # Validation
    'check_duplicate_passages',
    # IO
    'parse_file',
    # Main
    'parse',
]
