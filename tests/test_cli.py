"""Tests for the Bardic CLI commands using Click's CliRunner."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from bardic.cli.graph import extract_connections
from bardic.cli.main import cli


MINIMAL_STORY = """\
:: Start
Hello world!

+ [Continue] -> End

:: End
The end.
"""

STORY_WITH_METADATA = """\
@metadata
  title: Test Story
  author: Test Author
  version: 1.0.0

:: Start
Welcome to the test story.

+ [Begin] -> Chapter1

:: Chapter1
Chapter one content.
"""

STORY_WITH_ERROR = """\
:: Start
Hello world!

+ [Go nowhere] -> NonexistentPassage
"""

STORY_WITH_VARIABLES = """\
:: Start
~ gold = 100
~ name = "Hero"
You have {gold} gold, {name}.
"""

STORY_WITH_INCLUDE = """\
@include chapter2.bard

:: Start
The beginning.

+ [Next] -> Chapter2
"""

STORY_WITH_BROKEN_LINK = """\
:: Start
Hello world!

+ [Go nowhere] -> NonexistentPassage
"""

STORY_WITH_ORPHAN = """\
:: Start
Hello!

+ [Continue] -> End

:: End
The end.

:: Orphan
Nobody links here.
"""

STORY_WITH_DEAD_END = """\
:: Start
Hello!

+ [Go] -> DeadEnd

:: DeadEnd
Stuck here forever with no choices and no ending.

+ [Back] -> Start
"""

STORY_WITH_DUPLICATE = """\
:: Start
First start.

:: Start
Second start.
"""

STORY_WITH_EMPTY_PASSAGE = """\
:: Start
Hello!

+ [Go] -> Empty

:: Empty
"""


@pytest.fixture
def runner():
    """Create a Click CliRunner."""
    return CliRunner()


class TestCompileCommand:
    """Tests for `bardic compile`."""

    def test_compile_basic(self, runner):
        """Compiling a valid .bard file should produce a .json file."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["compile", "story.bard"])

            assert result.exit_code == 0
            assert "Compiled story.bard" in result.output
            # Default output should be story.json
            assert Path("story.json").exists()

    def test_compile_output_is_valid_json(self, runner):
        """The compiled output should be valid, loadable JSON."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            runner.invoke(cli, ["compile", "story.bard"])

            data = json.loads(Path("story.json").read_text())
            assert "passages" in data
            assert "initial_passage" in data
            assert data["initial_passage"] == "Start"
            assert "Start" in data["passages"]
            assert "End" in data["passages"]

    def test_compile_custom_output_path(self, runner):
        """The -o flag should control the output file path."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["compile", "story.bard", "-o", "custom_output.json"])

            assert result.exit_code == 0
            assert Path("custom_output.json").exists()
            assert not Path("story.json").exists()

    def test_compile_output_to_existing_subdirectory(self, runner):
        """Compiling to an existing subdirectory should work."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)
            Path("dist").mkdir()

            result = runner.invoke(cli, ["compile", "story.bard", "-o", "dist/game.json"])

            assert result.exit_code == 0
            assert Path("dist/game.json").exists()

    def test_compile_creates_parent_directories(self, runner):
        """Compiling to a nonexistent subdirectory should create it."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["compile", "story.bard", "-o", "dist/sub/game.json"])

            assert result.exit_code == 0
            assert Path("dist/sub/game.json").exists()

    def test_compile_shows_byte_sizes(self, runner):
        """Output should include input and output byte sizes."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["compile", "story.bard"])

            assert "bytes" in result.output

    def test_compile_preserves_metadata(self, runner):
        """Metadata from the .bard file should be in the compiled JSON."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_METADATA)

            runner.invoke(cli, ["compile", "story.bard"])

            data = json.loads(Path("story.json").read_text())
            assert data.get("metadata", {}).get("title") == "Test Story"
            assert data.get("metadata", {}).get("author") == "Test Author"

    def test_compile_nonexistent_file(self, runner):
        """Compiling a file that doesn't exist should fail with exit code 2."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["compile", "nonexistent.bard"])

            # Click returns exit code 2 for bad arguments (file doesn't exist)
            assert result.exit_code == 2

    def test_compile_with_variables(self, runner):
        """Stories with variables should compile successfully."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_VARIABLES)

            result = runner.invoke(cli, ["compile", "story.bard"])

            assert result.exit_code == 0
            data = json.loads(Path("story.json").read_text())
            assert "Start" in data["passages"]

    def test_compile_with_include(self, runner):
        """Stories with @include should resolve the included file."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_INCLUDE)
            Path("chapter2.bard").write_text(":: Chapter2\nChapter two!\n")

            result = runner.invoke(cli, ["compile", "story.bard"])

            assert result.exit_code == 0
            data = json.loads(Path("story.json").read_text())
            assert "Chapter2" in data["passages"]

    def test_compile_with_missing_include(self, runner):
        """Stories with @include pointing to a missing file should fail."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_INCLUDE)
            # Don't create chapter2.bard

            result = runner.invoke(cli, ["compile", "story.bard"])

            assert result.exit_code == 1
            assert "Error" in result.output or result.exit_code != 0

    def test_compile_overwrites_existing_output(self, runner):
        """Compiling should overwrite an existing output file."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)
            Path("story.json").write_text('{"old": "data"}')

            result = runner.invoke(cli, ["compile", "story.bard"])

            assert result.exit_code == 0
            data = json.loads(Path("story.json").read_text())
            assert "old" not in data
            assert "passages" in data


class TestLintCommand:
    """Tests for `bardic lint`."""

    def test_lint_clean_story(self, runner):
        """A well-formed story should produce no errors or warnings."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert result.exit_code == 0
            assert "No issues found" in result.output

    def test_lint_shows_summary_line(self, runner):
        """Lint output should include passage and choice counts."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert "passages" in result.output
            assert "choices" in result.output

    def test_lint_broken_target_fails_compilation(self, runner):
        """A broken jump target should fail at compile time before lint runs."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_BROKEN_LINK)

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert result.exit_code == 1
            assert "Compilation failed" in result.output
            assert "NonexistentPassage" in result.output

    def test_lint_orphan_passage_W001(self, runner):
        """An unreachable passage should produce W001."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_ORPHAN)

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert "W001" in result.output
            assert "Orphan" in result.output

    def test_lint_duplicate_passage_E002(self, runner):
        """Duplicate passage names should produce E002."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_DUPLICATE)

            result = runner.invoke(cli, ["lint", "story.bard"])

            # Duplicate may be caught at compile time or lint time
            assert result.exit_code != 0

    def test_lint_nonexistent_file(self, runner):
        """Linting a file that doesn't exist should fail with exit code 2."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["lint", "nonexistent.bard"])

            assert result.exit_code == 2

    def test_lint_json_output(self, runner):
        """The --json-output flag should produce valid JSON."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["lint", "story.bard", "--json-output"])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "summary" in data
            assert "diagnostics" in data
            assert "passages" in data["summary"]

    def test_lint_json_output_with_warnings(self, runner):
        """JSON output should include warning diagnostic codes."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_ORPHAN)

            result = runner.invoke(cli, ["lint", "story.bard", "--json-output"])

            data = json.loads(result.output)
            codes = [d["code"] for d in data["diagnostics"]]
            assert "W001" in codes

    def test_lint_errors_only_flag(self, runner):
        """The --errors-only flag should hide warnings."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_ORPHAN)

            result = runner.invoke(cli, ["lint", "story.bard", "--errors-only"])

            # Orphan is a warning (W001), should be hidden
            assert "W001" not in result.output

    def test_lint_verbose_flag(self, runner):
        """The --verbose flag should show hints and info diagnostics."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_ORPHAN)

            result = runner.invoke(cli, ["lint", "story.bard", "--verbose"])

            # Verbose shows info-level diagnostics too
            assert "W001" in result.output

    def test_lint_with_include(self, runner):
        """Lint should follow @include directives."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_INCLUDE)
            Path("chapter2.bard").write_text(":: Chapter2\nChapter two!\n")

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert result.exit_code == 0

    def test_lint_with_missing_include(self, runner):
        """Lint should fail if @include points to missing file."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(STORY_WITH_INCLUDE)

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert result.exit_code == 1

    def test_lint_word_count_in_summary(self, runner):
        """Lint should report word count and play time."""
        with runner.isolated_filesystem():
            Path("story.bard").write_text(MINIMAL_STORY)

            result = runner.invoke(cli, ["lint", "story.bard"])

            assert "words" in result.output


class TestInitCommand:
    """Tests for `bardic init`."""

    def test_init_creates_project_directory(self, runner):
        """Init should create a project directory with the given name."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game"])

            assert result.exit_code == 0
            assert Path("my-game").is_dir()

    def test_init_creates_example_story(self, runner):
        """Init should create an example .bard file."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game"])

            assert result.exit_code == 0
            assert Path("my-game/example.bard").exists()

    def test_init_nicegui_template(self, runner):
        """Default (nicegui) template should include player.py and requirements.txt."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game", "--template", "nicegui"])

            assert result.exit_code == 0
            assert Path("my-game/player.py").exists()
            assert Path("my-game/requirements.txt").exists()

    def test_init_browser_template(self, runner):
        """Browser template should create project without compiled_stories/."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game", "--template", "browser"])

            assert result.exit_code == 0
            assert Path("my-game").is_dir()
            # Browser template doesn't create compiled_stories/
            assert not Path("my-game/compiled_stories").exists()

    def test_init_existing_directory_fails(self, runner):
        """Init should fail if the project directory already exists."""
        with runner.isolated_filesystem():
            Path("my-game").mkdir()

            result = runner.invoke(cli, ["init", "my-game"])

            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_with_custom_path(self, runner):
        """The --path flag should control where the project is created."""
        with runner.isolated_filesystem():
            Path("projects").mkdir()

            result = runner.invoke(cli, ["init", "my-game", "--path", "projects"])

            assert result.exit_code == 0
            assert Path("projects/my-game").is_dir()

    def test_init_nonexistent_parent_path(self, runner):
        """Init should fail if the parent path doesn't exist."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game", "--path", "nonexistent"])

            assert result.exit_code == 1
            assert "does not exist" in result.output

    def test_init_shows_next_steps(self, runner):
        """Init should print next steps instructions."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game"])

            assert result.exit_code == 0
            assert "Next steps" in result.output

    def test_init_web_template(self, runner):
        """Web template should include backend and frontend directories."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game", "--template", "web"])

            assert result.exit_code == 0
            assert Path("my-game").is_dir()
            # Web template doesn't create compiled_stories/
            assert not Path("my-game/compiled_stories").exists()

    def test_init_invalid_template(self, runner):
        """An invalid template name should fail with exit code 2."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["init", "my-game", "--template", "invalid"])

            # Click returns exit code 2 for invalid Choice values
            assert result.exit_code == 2


class TestExtractConnections:
    """Unit tests for extract_connections() — the pure graph analysis function."""

    def test_basic_connections(self):
        """Should extract choice targets from passages."""
        story = {
            "passages": {
                "Start": {
                    "content": [{"type": "text", "text": "Hello"}],
                    "choices": [{"text": "Go", "target": "End"}],
                },
                "End": {
                    "content": [{"type": "text", "text": "Done"}],
                    "choices": [],
                },
            }
        }

        connections, referenced, defined = extract_connections(story)

        assert defined == {"Start", "End"}
        assert "End" in referenced
        assert len(connections["Start"]) == 1
        assert connections["Start"][0][0] == "End"  # target
        assert connections["Start"][0][2] is False  # not a jump

    def test_jump_targets(self):
        """Should extract jump targets from content tokens."""
        story = {
            "passages": {
                "Start": {
                    "content": [{"type": "jump", "target": "Next"}],
                    "choices": [],
                },
                "Next": {
                    "content": [],
                    "choices": [],
                },
            }
        }

        connections, referenced, defined = extract_connections(story)

        assert "Next" in referenced
        assert len(connections["Start"]) == 1
        assert connections["Start"][0][0] == "Next"
        assert connections["Start"][0][2] is True  # is a jump

    def test_missing_passage_detection(self):
        """Referenced but undefined passages should appear in referenced but not defined."""
        story = {
            "passages": {
                "Start": {
                    "content": [],
                    "choices": [{"text": "Go", "target": "Missing"}],
                },
            }
        }

        connections, referenced, defined = extract_connections(story)

        assert "Missing" in referenced
        assert "Missing" not in defined

    def test_long_choice_text_truncated(self):
        """Choice text longer than 30 chars should be truncated."""
        story = {
            "passages": {
                "Start": {
                    "content": [],
                    "choices": [
                        {
                            "text": "This is a very long choice text that should be truncated",
                            "target": "End",
                        }
                    ],
                },
                "End": {"content": [], "choices": []},
            }
        }

        connections, _, _ = extract_connections(story)

        choice_label = connections["Start"][0][1]
        assert len(choice_label) <= 30
        assert choice_label.endswith("...")

    def test_token_list_choice_text(self):
        """List-based choice text (new format) should use placeholder."""
        story = {
            "passages": {
                "Start": {
                    "content": [],
                    "choices": [{"text": [{"type": "text", "text": "Go"}], "target": "End"}],
                },
                "End": {"content": [], "choices": []},
            }
        }

        connections, _, _ = extract_connections(story)

        assert connections["Start"][0][1] == "[choice]"

    def test_conditional_branch_choices(self):
        """Should extract choices from conditional branches."""
        story = {
            "passages": {
                "Start": {
                    "content": [
                        {
                            "type": "conditional",
                            "branches": [
                                {
                                    "content": [],
                                    "choices": [{"text": "Yes", "target": "Good"}],
                                },
                                {
                                    "content": [],
                                    "choices": [{"text": "No", "target": "Bad"}],
                                },
                            ],
                        }
                    ],
                    "choices": [],
                },
                "Good": {"content": [], "choices": []},
                "Bad": {"content": [], "choices": []},
            }
        }

        connections, referenced, _ = extract_connections(story)

        assert "Good" in referenced
        assert "Bad" in referenced
        assert len(connections["Start"]) == 2

    def test_for_loop_choices(self):
        """Should extract choices from for loop content."""
        story = {
            "passages": {
                "Start": {
                    "content": [
                        {
                            "type": "for_loop",
                            "content": [],
                            "choices": [{"text": "Pick", "target": "Item"}],
                        }
                    ],
                    "choices": [],
                },
                "Item": {"content": [], "choices": []},
            }
        }

        connections, referenced, _ = extract_connections(story)

        assert "Item" in referenced

    def test_empty_story(self):
        """Should handle a story with no passages gracefully."""
        story = {"passages": {}}

        connections, referenced, defined = extract_connections(story)

        assert defined == set()
        assert referenced == set()
        assert connections == {}


class TestGraphCommand:
    """Tests for `bardic graph` CLI command."""

    def _compile_story(self, runner, source, bard_name="story.bard"):
        """Helper: compile a .bard file and return the JSON path."""
        Path(bard_name).write_text(source)
        result = runner.invoke(cli, ["compile", bard_name])
        assert result.exit_code == 0
        return bard_name.replace(".bard", ".json")

    def test_graph_generates_png(self, runner):
        """Graph should generate a PNG file by default."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, MINIMAL_STORY)

            result = runner.invoke(cli, ["graph", json_path])

            assert result.exit_code == 0
            assert Path("story_graph.png").exists()

    def test_graph_generates_svg(self, runner):
        """Graph should support SVG output format."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, MINIMAL_STORY)

            result = runner.invoke(cli, ["graph", json_path, "-f", "svg"])

            assert result.exit_code == 0
            assert Path("story_graph.svg").exists()

    def test_graph_custom_output_path(self, runner):
        """The -o flag should control the output path."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, MINIMAL_STORY)

            result = runner.invoke(cli, ["graph", json_path, "-o", "my_graph"])

            assert result.exit_code == 0
            assert Path("my_graph.png").exists()

    def test_graph_shows_passage_count(self, runner):
        """Graph output should report the number of passages."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, MINIMAL_STORY)

            result = runner.invoke(cli, ["graph", json_path])

            assert "Passages:" in result.output

    def test_graph_shows_connection_count(self, runner):
        """Graph output should report the number of connections."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, MINIMAL_STORY)

            result = runner.invoke(cli, ["graph", json_path])

            assert "Connections:" in result.output

    def test_graph_nonexistent_file(self, runner):
        """Graphing a nonexistent file should fail with exit code 2."""
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["graph", "nonexistent.json"])

            assert result.exit_code == 2

    def test_graph_with_metadata_story(self, runner):
        """Graph should work with stories that have metadata."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, STORY_WITH_METADATA)

            result = runner.invoke(cli, ["graph", json_path])

            assert result.exit_code == 0
            assert Path("story_graph.png").exists()

    def test_graph_pdf_format(self, runner):
        """Graph should support PDF output format."""
        with runner.isolated_filesystem():
            json_path = self._compile_story(runner, MINIMAL_STORY)

            result = runner.invoke(cli, ["graph", json_path, "-f", "pdf"])

            assert result.exit_code == 0
            assert Path("story_graph.pdf").exists()
