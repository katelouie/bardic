"""Example lint plugin — delete or modify this file for your own checks.

This plugin runs automatically when you use `bardic lint`. Add your own
check_* functions to validate game-specific data, naming conventions,
or anything the built-in linter doesn't cover.

See: https://github.com/katelouie/bardic/blob/main/docs/lint-plugins.md
"""

from pathlib import Path

from bardic.cli.lint import LintReport


def check_example(story_data: dict, report: LintReport, project_root: Path):
    """Example check — counts passages and reports a summary.

    Replace this with your own game-specific checks. Some ideas:
    - Validate item/spell/character names against a data file
    - Check that stat values stay within expected bounds
    - Verify that all required story variables are initialized
    - Ensure naming conventions are followed
    """
    passages = story_data.get("passages", {})
    passage_count = len(passages)

    # Info diagnostics only show with --verbose
    report.info(
        "GI001",
        f"Story has {passage_count} passages (example plugin working!)",
    )
