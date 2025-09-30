"""
Command-line interface for Bardic.
"""

import click
import sys
from pathlib import Path

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    Bardic: Python-first interactive fiction engine

    Create branching narratives with the elegance of Ink
    and the power of Python.
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


if __name__ == "__main__":
    cli()