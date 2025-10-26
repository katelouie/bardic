"""
Parse .bard files into intermediate representation.

This module re-exports all parsing functions from the parsing subpackage.
All implementation has been moved to parsing/* modules for better organization.

Supports:
- :: PassageName (passage headers)
- Regular Text
- + [Choice Text] -> Target Passage (choices)
- And much more...
"""

# Re-export everything from parsing subpackage for backward compatibility
from .parsing import *

# Explicitly re-export main functions for clarity and type hints
from .parsing import parse, parse_file


__all__ = [
    # Main functions (most commonly used)
    'parse',
    'parse_file',
    # Error handling
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
]
