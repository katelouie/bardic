"""
Command-line interface for Bardic.
"""

import click
import sys
from pathlib import Path
import json
from bardic.runtime.engine import BardEngine

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Bardic: Python-first interactive fiction engine

    Create branching narratives with Python integration for
    modern web applications.

    \b
    Common workflow:
      1. Write your story in a .bard file
      2. Compile it: bardic compile story.bard
      3. Play it: bardic play story.json

    \b
    For more help on a command:
      bardic COMMAND --help
    """
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help="Output file path")
def compile(input_file, output):
    """
    Compile a .bard file to JSON.

    Example:
        bardic compile story.bard
        bardic compile story.bard -o story.json
    """
    from bardic.compiler.compiler import BardCompiler

    try:
        compiler = BardCompiler()
        output_path = compiler.compile_file(input_file, output)

        # Show success message
        input_size = Path(input_file).stat().st_size
        output_size = Path(output_path).stat().st_size

        click.echo(click.style('✓', fg="green", bold=True) + f" Compiled {input_file}")
        click.echo(f'  → {output_path}')
        click.echo(f'  ({input_size} bytes → {output_size} bytes)')

    except Exception as e:
        click.echo(click.style('✗ Error: ', fg="red", bold=True) + str(e), err=True)
        sys.exit(1)

@cli.command()
@click.argument("story_file", type=click.Path(exists=True))
@click.option('--no-color', is_flag=True, help='Disable colored output')
def play(story_file: str, no_color: bool):
    """
    Play a compiled story in the terminal.

    Loads a compiled JSON story file and presents it as an interactive text adventure.
    Navigate using numbered choices.

    The story file must be a completed Bardic story (use 'bardic compile' first).

    \b
    Example:
        bardic play story.json
        bardic play story.json --no-color

    \b
    Controls:
        - Enter a number to make a choice
        - Ctrl+C to quit
    """
    # Disable colors if requested
    if no_color:
        click.style = lambda text, **kwargs: text

    # Load the story
    try:
        with open(story_file) as f:
            story = json.load(f)
    except json.JSONDecodeError as e:
        click.echo(click.style('✗ Error: ', fg="red",  bold=True) + f"Invalid JSON: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style('✗ Error: ', fg='red', bold=True) + f'Could not load story: {e}', err=True)
        sys.exit(1)

    # Create engine
    try:
        engine = BardEngine(story)
    except Exception as e:
        click.echo(click.style('✗ Error: ', fg='red', bold=True) + f'Could not initialize story: {e}', err=True)
        sys.exit(1)

    # Show header
    click.echo()
    click.echo("=" * 70)
    click.echo(click.style("  BARDIC STORY PLAYER", fg='cyan', bold=True))
    click.echo("=" * 70)
    click.echo()

    # Show story info
    info = engine.get_story_info()
    click.echo(click.style("Story: ", fg='white', dim=True) + f"{info['version']}")
    click.echo(click.style("Passages: ", fg='white', dim=True) + f"{info['passage_count']}")
    click.echo()
    click.echo(click.style("Press Ctrl+C to quit at any time", fg='white', dim=True))
    click.echo()
    click.echo("-" * 70)

    # Track passage count for stats
    passages_visited = 0

    # Main game loop
    try:
        while True:
            # Get current passage
            output = engine.current()
            passages_visited += 1

            # Display passage content
            click.echo()
            click.echo(click.style(f"▸ {output.passage_id}", fg='yellow', bold=True))
            click.echo()

            # Format content (preserve blank lines)
            for line in output.content.split("\n"):
                if line.strip():
                    click.echo(click.style("  ", fg="white") + line)
                else:
                    click.echo()

            click.echo()

            # Check if this is an ending
            if engine.is_end():
                click.echo("-" * 70)
                click.echo()
                click.echo(click.style("  ◆ THE END ◆", fg='green', bold=True))
                click.echo()
                click.echo(click.style(f"  You visited {passages_visited} passages", fg='white', dim=True))
                click.echo()
                break

            # Show choices
            click.echo("-" * 70)
            click.echo()
            click.echo("What do you do?")
            click.echo()

            for i, choice in enumerate(output.choices, 1):
                click.echo(f"  {click.style(str(i), fg='cyan', bold=True)}. {choice['text']}")

            click.echo()

            # Get player input
            while True:
                try:
                    choice_input = click.prompt(
                        click.style("→", fg='cyan', bold=True),
                        type=int,
                        prompt_suffix=" "
                    )

                    if 1 <= choice_input <= len(output.choices):
                        engine.choose(choice_input - 1)
                        click.echo()
                        click.echo("-" * 70)
                        break
                    else:
                        click.echo(
                            click.style("  ⚠ ", fg='yellow') +
                            f"Please enter a number between 1 and {len(output.choices)}"
                        )
                except ValueError:
                    click.echo(click.style("  ⚠ ", fg='yellow') + "Please enter a valid number")
                except EOFError:
                    # Ctrl+D pressed
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        click.echo()
        click.echo()
        click.echo("-" * 70)
        click.echo(click.style(f"  Story interrupted after {passages_visited} passages. Goodbye!", fg='yellow'))
        click.echo()
        sys.exit(0)

if __name__ == "__main__":
    cli()