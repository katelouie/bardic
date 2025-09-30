"""
Compile .bard files to JSON intermediate representation.
"""

import json
from pathlib import Path
from .parser import parse_file


class BardCompiler:
    """Compiles .bard story files to JSON."""

    def compile_file(self, input_path: str, output_path: str = None) -> str:
        """
        Compile a .bard file to JSON.

        Args:
            input_path (str): Path to input .bard file
            output_path (str, Optional): Path to output .json file (defaults to same name)

        Returns:
            Path to the output file
        """
        # Parse the source file
        result = parse_file(input_path)

        # Determine output path
        if output_path is None:
            input_path_obj = Path(input_path)
            output_path = str(input_path_obj.with_suffix(".json"))

        # Write JSON output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        return output_path

    def compile_string(self, source: str) -> dict:
        """
        Compile a .bard source string directly to dict.

        Args:
            source: .bard source code as string

        Returns:
            Compiled story as dictionary
        """
        from .parser import parse
        return parse(source)