"""
Browser bundle creation for Bardic games.

Creates a self-contained package that can be uploaded to itch.io
or any static hosting platform. Includes local Pyodide runtime
for faster loading.
"""

import json
import re
import shutil
from pathlib import Path
from typing import Optional


def create_browser_bundle(
    story_file: Path,
    output_dir: Path,
    game_name: Optional[str] = None,
    theme: str = "dark",
    minimal: bool = False,
) -> Path:
    """
    Bundle a .bard story for browser distribution.

    Creates a directory containing all files needed to run the game
    in a web browser using local Pyodide (no CDN required).

    Args:
        story_file: Path to the .bard story file
        output_dir: Directory to create the bundle in
        game_name: Display name for the game (from metadata if not specified)
        theme: Theme to use (dark, light, retro)
        minimal: If True, only include Pyodide core (no extra packages)

    Returns:
        Path to the created bundle directory
    """
    from bardic.compiler.compiler import BardCompiler

    # Resolve paths
    story_file = Path(story_file).resolve()
    output_dir = Path(output_dir).resolve()
    story_dir = story_file.parent

    # Get template directory
    templates_dir = Path(__file__).parent.parent / "templates" / "browser"

    # Step 1: Compile the story if it's a .bard file
    if story_file.suffix == ".bard":
        compiler = BardCompiler()
        # Compile to a temporary location first
        temp_json = output_dir / "game.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        compiler.compile_file(str(story_file), str(temp_json))
        story_data = json.loads(temp_json.read_text())
    else:
        # Already compiled JSON
        story_data = json.loads(story_file.read_text())
        output_dir.mkdir(parents=True, exist_ok=True)
        # Copy to output
        (output_dir / "game.json").write_text(json.dumps(story_data, indent=2))

    # Step 2: Get game name from metadata if not provided
    if not game_name:
        metadata = story_data.get("metadata", {})
        game_name = metadata.get("title", story_file.stem)

    # Step 3: Copy engine_browser.py
    shutil.copy(templates_dir / "engine_browser.py", output_dir / "engine_browser.py")

    # Step 4: Copy and customize index.html
    html_content = (templates_dir / "index.html").read_text()
    html_content = html_content.replace("{{GAME_NAME}}", game_name)
    (output_dir / "index.html").write_text(html_content)

    # Step 5: Copy base CSS and apply theme
    base_css = (templates_dir / "style.css").read_text()
    theme_file = templates_dir / "themes" / f"{theme}.css"
    if theme_file.exists():
        theme_css = theme_file.read_text()
        # Prepend theme variables to override defaults
        final_css = theme_css + "\n\n" + base_css
    else:
        final_css = base_css
    (output_dir / "style.css").write_text(final_css)

    # Step 6: Copy Pyodide runtime and packages
    pyodide_source = templates_dir / "pyodide"
    pyodide_dest = output_dir / "pyodide"
    if pyodide_source.exists():
        if minimal:
            # Only copy core Pyodide files (no extra packages)
            pyodide_dest.mkdir(parents=True, exist_ok=True)
            core_files = [
                "pyodide.asm.wasm",
                "pyodide.asm.js",
                "pyodide.js",
                "pyodide.mjs",
                "python_stdlib.zip",
                "pyodide-lock.json",
            ]
            for filename in core_files:
                src = pyodide_source / filename
                if src.exists():
                    shutil.copy(src, pyodide_dest / filename)
            # Also copy micropip for runtime package installation
            for whl in pyodide_source.glob("micropip*.whl"):
                shutil.copy(whl, pyodide_dest / whl.name)
        else:
            # Copy everything (core + all packages)
            shutil.copytree(pyodide_source, pyodide_dest, dirs_exist_ok=True)

    # Step 7: Copy stdlib modules
    stdlib_dir = output_dir / "bardic" / "stdlib"
    stdlib_dir.mkdir(parents=True, exist_ok=True)

    stdlib_source = Path(__file__).parent.parent / "stdlib"
    for py_file in stdlib_source.glob("*.py"):
        shutil.copy(py_file, stdlib_dir / py_file.name)

    # Step 8: Detect and copy user modules from imports
    user_modules = detect_user_modules(story_data, story_dir)
    if user_modules:
        for module_path in user_modules:
            if module_path.exists():
                # Preserve directory structure relative to story_dir
                try:
                    rel_path = module_path.relative_to(story_dir)
                    dest = output_dir / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(module_path, dest)
                except ValueError:
                    # Module is outside story_dir, copy to root
                    shutil.copy(module_path, output_dir / module_path.name)

    return output_dir


def detect_user_modules(story_data: dict, story_dir: Path) -> list[Path]:
    """
    Detect user-defined modules from story imports.

    Parses import statements and resolves them to file paths.

    Args:
        story_data: Compiled story dictionary
        story_dir: Directory containing the story file

    Returns:
        List of paths to user module files
    """
    imports = story_data.get("imports", [])
    modules = []

    for import_stmt in imports:
        # Skip stdlib imports
        if "bardic.stdlib" in import_stmt:
            continue

        # Parse import statement to get module path
        # Handle: "from game_logic.cards import TarotDeck"
        # Handle: "import game_logic.utils"
        module_path = parse_import_to_path(import_stmt, story_dir)
        if module_path and module_path.exists():
            modules.append(module_path)

    return modules


def parse_import_to_path(import_stmt: str, base_dir: Path) -> Optional[Path]:
    """
    Convert an import statement to a file path.

    Args:
        import_stmt: Python import statement
        base_dir: Base directory for relative imports

    Returns:
        Path to the module file, or None if not resolvable
    """
    import_stmt = import_stmt.strip()

    # Handle "from X import Y" style
    from_match = re.match(r"from\s+([\w.]+)\s+import", import_stmt)
    if from_match:
        module_name = from_match.group(1)
    else:
        # Handle "import X" style
        import_match = re.match(r"import\s+([\w.]+)", import_stmt)
        if import_match:
            module_name = import_match.group(1)
        else:
            return None

    # Skip standard library and bardic stdlib
    if module_name.startswith(("bardic.", "os", "sys", "json", "re", "random", "typing")):
        return None

    # Convert module name to path
    # game_logic.cards -> game_logic/cards.py
    parts = module_name.split(".")
    rel_path = Path(*parts[:-1]) / f"{parts[-1]}.py" if len(parts) > 1 else Path(f"{parts[0]}.py")

    # Try as file first
    candidate = base_dir / rel_path
    if candidate.exists():
        return candidate

    # Try as package (__init__.py)
    package_path = base_dir / Path(*parts) / "__init__.py"
    if package_path.exists():
        return package_path

    # Try just the directory (collect all .py files)
    dir_path = base_dir / Path(*parts)
    if dir_path.is_dir():
        # Return the __init__.py or first .py file
        init_file = dir_path / "__init__.py"
        if init_file.exists():
            return init_file

    return None


def list_available_themes() -> list[str]:
    """
    List available themes.

    Returns:
        List of theme names (without .css extension)
    """
    themes_dir = Path(__file__).parent.parent / "templates" / "browser" / "themes"
    if themes_dir.exists():
        return [f.stem for f in themes_dir.glob("*.css")]
    return ["dark"]  # Default fallback
