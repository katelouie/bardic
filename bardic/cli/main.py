"""
Command-line interface for Bardic.
"""

import click
import sys
from pathlib import Path
import json
import subprocess
import time
import webbrowser
from bardic.runtime.engine import BardEngine


@click.group()
@click.version_option(version="0.1.0")
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
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path")
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

        click.echo(click.style("✓", fg="green", bold=True) + f" Compiled {input_file}")
        click.echo(f"  → {output_path}")
        click.echo(f"  ({input_size} bytes → {output_size} bytes)")

    except Exception as e:
        click.echo(click.style("✗ Error: ", fg="red", bold=True) + str(e), err=True)
        sys.exit(1)


@cli.command()
@click.argument("story_file", type=click.Path(exists=True))
@click.option("--no-color", is_flag=True, help="Disable colored output")
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
        click.echo(
            click.style("✗ Error: ", fg="red", bold=True) + f"Invalid JSON: {e}",
            err=True,
        )
        sys.exit(1)
    except Exception as e:
        click.echo(
            click.style("✗ Error: ", fg="red", bold=True)
            + f"Could not load story: {e}",
            err=True,
        )
        sys.exit(1)

    # Create engine
    try:
        engine = BardEngine(story)
    except Exception as e:
        click.echo(
            click.style("✗ Error: ", fg="red", bold=True)
            + f"Could not initialize story: {e}",
            err=True,
        )
        sys.exit(1)

    # Show header
    click.echo()
    click.echo("=" * 70)
    click.echo(click.style("  BARDIC STORY PLAYER", fg="cyan", bold=True))
    click.echo("=" * 70)
    click.echo()

    # Show story info
    info = engine.get_story_info()
    click.echo(click.style("Story: ", fg="white", dim=True) + f"{info['version']}")
    click.echo(
        click.style("Passages: ", fg="white", dim=True) + f"{info['passage_count']}"
    )
    click.echo()
    click.echo(click.style("Press Ctrl+C to quit at any time", fg="white", dim=True))
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
            click.echo(click.style(f"▸ {output.passage_id}", fg="yellow", bold=True))
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
                click.echo(click.style("  ◆ THE END ◆", fg="green", bold=True))
                click.echo()
                click.echo(
                    click.style(
                        f"  You visited {passages_visited} passages",
                        fg="white",
                        dim=True,
                    )
                )
                click.echo()
                break

            # Show choices
            click.echo("-" * 70)
            click.echo()
            click.echo("What do you do?")
            click.echo()

            for i, choice in enumerate(output.choices, 1):
                click.echo(
                    f"  {click.style(str(i), fg='cyan', bold=True)}. {choice['text']}"
                )

            click.echo()

            # Get player input
            while True:
                try:
                    choice_input = click.prompt(
                        click.style("→", fg="cyan", bold=True),
                        type=int,
                        prompt_suffix=" ",
                    )

                    if 1 <= choice_input <= len(output.choices):
                        engine.choose(choice_input - 1)
                        click.echo()
                        click.echo("-" * 70)
                        break
                    else:
                        click.echo(
                            click.style("  ⚠ ", fg="yellow")
                            + f"Please enter a number between 1 and {len(output.choices)}"
                        )
                except ValueError:
                    click.echo(
                        click.style("  ⚠ ", fg="yellow") + "Please enter a valid number"
                    )
                except EOFError:
                    # Ctrl+D pressed
                    raise KeyboardInterrupt
    except KeyboardInterrupt:
        click.echo()
        click.echo()
        click.echo("-" * 70)
        click.echo(
            click.style(
                f"  Story interrupted after {passages_visited} passages. Goodbye!",
                fg="yellow",
            )
        )
        click.echo()
        sys.exit(0)


@cli.command()
@click.option("--port", default=8000, help="Backend port (default: 8000)")
@click.option("--frontend-port", default=5173, help="Frontend port (default: 5173)")
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
def serve(port, frontend_port, no_browser):
    """
    Start the Bardic web runtime (backend + frontend).

    Starts both FastAPI backend and React frontend development servers, then opens
    your browser to the story player.

    Example:
        bardic serve
        bardic serve --port 8080
        bardic serve --no-browser
    """
    # Find the web-runtime directory
    # Assume it's in the same parent directory as bardic
    bardic_path = Path(__file__).parent.parent.parent
    web_runtime = bardic_path / "web-runtime"

    if not web_runtime.exists():
        click.echo(
            click.style("✗ Error: ", fg="red", bold=True)
            + f"web-runtime directory not found at {web_runtime}"
        )
        click.echo("\nExpected structure:")
        click.echo("  project/")
        click.echo("    ├── bardic/")
        click.echo("    └── web-runtime/")
        click.echo("        ├── backend/")
        click.echo("        └── frontend/")
        sys.exit(1)

    backend_dir = web_runtime / "backend"
    frontend_dir = web_runtime / "frontend"

    click.echo(click.style("Starting Bardic Web Runtime...\n", fg="cyan", bold=True))

    # Start backend
    click.echo(click.style("Starting backend server...", fg="yellow"))
    click.echo()
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--port", str(port)],
        cwd=backend_dir,
        # Don't capture output - let it flow to terminal for debugging
    )

    # Wait for backend to start
    time.sleep(2)

    # Check if backend started successfully
    if backend_process.poll() is not None:
        click.echo(click.style("✗ Backend failed to start", fg="red"))
        sys.exit(1)

    click.echo(
        click.style("✓ Backend running", fg="green") + f" on http://127.0.0.1:{port}"
    )

    # Start frontend
    click.echo(click.style("Starting frontend server...", fg="yellow"))
    click.echo()

    # Check if node_modules exist
    if not (frontend_dir / "node_modules").exists():
        click.echo(click.style("Installing frontend dependencies...", fg="yellow"))
        npm_install = subprocess.run(
            ["npm", "install"], cwd=frontend_dir, capture_output=True
        )
        if npm_install.returncode != 0:
            click.echo(click.style("X npm install failed", fg="red"))
            backend_process.terminate()
            sys.exit(1)

    frontend_process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(frontend_port)],
        cwd=frontend_dir,
        # Don't capture output - let it flow to terminal for debugging
    )

    # Wait for frontend to start
    time.sleep(2)

    if frontend_process.poll() is not None:
        click.echo(click.style("✗ Frontend failed to start", fg="red"))
        backend_process.terminate()
        sys.exit(1)

    click.echo(
        click.style("✓ Frontend running", fg="green")
        + f" on http://localhost:{frontend_port}"
    )

    # Open browser
    if not no_browser:
        click.echo(click.style("\n🌐 Opening browser...\n", fg="cyan"))
        time.sleep(1)
        webbrowser.open(f"http://localhost:{frontend_port}")

    click.echo("=" * 60)
    click.echo(click.style("✓ Bardic Web Runtime is running!", fg="green", bold=True))
    click.echo("=" * 60)
    click.echo()
    click.echo(f"  Frontend: http://localhost:{frontend_port}")
    click.echo(f"  Backend:  http://127.0.0.1:{port}")
    click.echo()
    click.echo(click.style("Press Ctrl+C to stop all servers", fg="yellow"))
    click.echo()

    try:
        # Wait for user interrupt
        while True:
            time.sleep(1)
            # Check if processes are still running
            if backend_process.poll() is not None:
                click.echo(click.style("\n✗ Backend stopped unexpectedly", fg="red"))
                break
            if frontend_process.poll() is not None:
                click.echo(click.style("\n✗ Frontend stopped unexpectedly", fg="red"))
                break
    except KeyboardInterrupt:
        click.echo(click.style("\n\n🛑 Stopping servers...", fg="yellow"))
        backend_process.terminate()
        frontend_process.terminate()

        # Wait for graceful shutdown
        time.sleep(1)

        # Force kill if still running
        backend_process.kill()
        frontend_process.kill()

        click.echo(click.style("✓ Servers stopped", fg="green"))
        click.echo()


if __name__ == "__main__":
    cli()
