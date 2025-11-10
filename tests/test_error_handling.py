"""Test that parser errors are caught and reported correctly."""

import pytest
from pathlib import Path
from bardic.compiler.parser import parse

ERROR_TEST_DIR = Path(__file__).parent / "error_handling"

# Map error test files to the expected error type and message
ERROR_CASES = {
    "test_if_missing_colon.bard": {
        "error_type": Exception,  # We'll refine this as we improve error handling
        "error_pattern": r"(?i)colon|:",  # Case-insensitive regex
        "description": "Missing colon after @if should raise error",
    },
    "test_duplicate_passage.bard": {
        "error_type": ValueError,
        "error_pattern": r"(?i)duplicate.*passage",
        "description": "Duplicate passage names should raise error",
    },
    "test_choice_missing_arrow.bard": {
        "error_type": Exception,
        "error_pattern": r"(?i)arrow|->",
        "description": "Choice without -> should raise error",
    },
    "test_choice_missing_opening_bracket.bard": {
        "error_type": Exception,
        "error_pattern": r"(?i)bracket|\[",
        "description": "Choice without [ should raise error",
    },
    "test_choice_missing_closing_bracket.bard": {
        "error_type": Exception,
        "error_pattern": r"(?i)bracket|\]",
        "description": "Choice without ] should raise error",
    },
    "test_unclosed_if.bard": {
        "error_type": Exception,
        "error_pattern": r"(?i)unclosed|endif|@endif",
        "description": "@if without @endif should raise error",
    },
    "test_unclosed_py.bard": {
        "error_type": Exception,
        "error_pattern": r"(?i)unclosed|@endpy|endpy",
        "description": "@py: without @endpy should raise error",
    },
    "test_empty_name.bard": {
        "error_type": ValueError,
        "error_pattern": r"(?i)no passages",
        "description": "Passage with empty name should raise error",
    },
    "test_hyphen_in_name.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)invalid|passage.*name|hyphen",
        "description": "Passage name with hyphen should raise error",
    },
    "test_missing_colon_errors.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|:",
        "description": "Missing colon after @if directive should raise error",
    },
    "test_unclosed_block_errors.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed|@endif|endif",
        "description": "@if block without @endif should raise error",
    },
    "test_endif_colon.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|unexpected.*:|@endif.*colon",
        "description": "@endif should not have a colon",
    },
    "test_endfor_colon.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|unexpected.*:|@endfor.*colon",
        "description": "@endfor should not have a colon",
    },
    # TODO: Parser currently silently ignores unknown directives - should error instead
    # "test_typo_directive.bard": {
    #     "error_type": Exception,
    #     "error_pattern": r"(?i)unknown.*directive|invalid.*directive|@iff",
    #     "description": "Typo in directive name (@iff instead of @if) should raise error",
    # },
    # "test_typo_directive2.bard": {
    #     "error_type": Exception,
    #     "error_pattern": r"(?i)unknown.*directive|invalid.*directive|@endiff|unexpected",
    #     "description": "Typo in directive name (@endiff instead of @endif) should raise error",
    # },
    "test_space_in_name.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)invalid.*passage.*name|space|whitespace",
        "description": "Passage name with spaces should raise error",
    },
    "test_starts_with_number.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)invalid.*passage.*name|start.*number|digit",
        "description": "Passage name starting with number should raise error",
    },
    "test_special_char.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)invalid.*passage.*name|special.*char|@",
        "description": "Passage name with special characters should raise error",
    },
    "test_choice_unclosed_conditional.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed|brace|\}|conditional",
        "description": "Choice with unclosed conditional brace should raise error",
    },
    "test_choice_empty_text.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)empty.*choice|choice.*text|blank",
        "description": "Choice with empty text in brackets should raise error",
    },
    "test_choice_missing_target.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)missing.*target|target.*required|->",
        "description": "Choice missing target after arrow should raise error",
    },
    "test_py_missing_colon.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|@py.*:|expected.*:",
        "description": "@py directive should have a colon",
    },
    "test_elif_missing_colon.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|@elif.*:|expected.*:",
        "description": "@elif directive missing colon should raise error",
    },
    "test_else_missing_colon.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|@else.*:|expected.*:",
        "description": "@else directive missing colon should raise error",
    },
    "test_for_missing_colon.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)colon|@for.*:|expected.*:",
        "description": "@for directive missing colon should raise error",
    },
    "test_python_unclosed_paren.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed|parenthes|paren|\(|syntax",
        "description": "Python expression with unclosed parenthesis should raise error",
    },
    "test_python_unclosed_string.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed.*string|unterminated.*string|quote|syntax",
        "description": "Python expression with unclosed string should raise error",
    },
    "test_python_invalid_syntax.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)invalid.*syntax|syntax.*error|statement",
        "description": "Invalid Python syntax in variable assignment should raise error",
    },
    "test_python_unclosed_call.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed|parenthes|paren|\(|syntax",
        "description": "Python function call with unclosed parenthesis should raise error",
    },
    "test_render_no_directive.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)render directive missing directive name",
        "description": "@render directive without component name should raise error",
    },
    "test_input_no_params.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)@input.*requires|missing.*parameter|directive.*incomplete",
        "description": "@input directive without parameters should raise error",
    },
    # TODO: Parser currently silently ignores @include with no file - should error instead
    # "test_include_no_file.bard": {
    #     "error_type": Exception,
    #     "error_pattern": r"(?i)@include.*requires|missing.*file|filename.*required",
    #     "description": "@include directive without filename should raise error",
    # },
    "test_unclosed_expression.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed.*expression|missing.*\}|brace",
        "description": "Unclosed curly brace in expression should raise error",
    },
    "test_extra_closing_brace.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unexpected.*\}|extra.*brace|unmatched",
        "description": "Extra closing brace without opening should raise error",
    },
    "test_mismatched_braces.bard": {
        "error_type": SyntaxError,
        "error_pattern": r"(?i)unclosed|mismatched.*brace|missing.*\}",
        "description": "Mismatched/nested braces in expression should raise error",
    },
}


@pytest.mark.parametrize(
    "filename,expected", ERROR_CASES.items(), ids=list(ERROR_CASES.keys())
)
def test_parser_error_is_caught(filename, expected):
    """
    Test that parser errors are caught and have helpful messages.

    This ensures that when users make mistakes in their .bard files,
    they get clear error messages to help them fix it.
    """
    # Given: An error test file
    test_file = ERROR_TEST_DIR / filename

    # Handle case where file doesn't exist yet
    if not test_file.exists():
        pytest.skip(f"Error test file not found: {filename}")

    source = test_file.read_text()

    # When/Then: Parsing should raise the expected error
    with pytest.raises(expected["error_type"]) as exc_info:
        parse(source)

    # And: The error message should be helpful
    error_message = str(exc_info.value)
    import re

    assert re.search(expected["error_pattern"], error_message), (
        f"Error message should mention {expected['error_pattern']}, "
        f"but got: {error_message}"
    )
