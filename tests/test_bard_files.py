"""Test that all .bard files in stories/test compile successfully."""

import pytest
from pathlib import Path
from bardic.compiler.compiler import BardCompiler


# Collect all .bard test files
TEST_DIR = Path(__file__).parent.parent / "stories" / "test"
BARD_FILES = list(TEST_DIR.glob("*.bard"))

# Filter out any files you know are intentionally broken
# (We'll handle those separately in error tests)
BARD_FILES = [f for f in BARD_FILES if "errors" not in f.name]


@pytest.mark.smoke
@pytest.mark.parametrize("bard_file", BARD_FILES, ids=lambda p: p.name)
def test_bard_file_compiles(bard_file, tmp_path):
    """
    Test that a .bard file compiles without errors.

    This is a "smoke test" - we're just checking it doesn't crash.
    We're not verifying the compiled output is correct (yet).
    """
    # Given: A .bard test file
    # When: We compile it
    compiler = BardCompiler()
    output_path = tmp_path / f"{bard_file.stem}.json"

    # Then: It should compile without raising an exception
    result_path = compiler.compile_file(str(bard_file), str(output_path))

    # And: The output file should exist
    assert Path(result_path).exists()

    # And: The file should have content
    assert Path(result_path).stat().st_size > 0


@pytest.mark.smoke
@pytest.mark.parametrize("bard_file", BARD_FILES, ids=lambda p: p.name)
def test_compiled_story_can_run(bard_file, tmp_path):
    """
    Test that a compiled story can be loaded by the engine.

    This verifies the compilation output is valid JSON and
    has the required structure.
    """
    # Given: A compiled story
    compiler = BardCompiler()
    output_path = tmp_path / f"{bard_file.stem}.json"
    result_path = compiler.compile_file(str(bard_file), str(output_path))

    # When: We try to create an engine with it
    import json
    from bardic.runtime.engine import BardEngine

    with open(result_path) as f:
        story_data = json.load(f)

    # Then: It should load without error
    engine = BardEngine(story_data)

    # And: We should be able to get the current passage
    output = engine.current()
    assert output.passage_id is not None
