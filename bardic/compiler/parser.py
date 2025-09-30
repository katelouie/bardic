"""
Parse .bard files into intermediate representation.

Supports:
- :: PassageName (passage headers)
- Regular Text
- + [Choice Text] -> Target Passage (choices)
"""

import re
from typing import Dict, List, Any


def parse(source: str) -> Dict[str, Any]:
    """
    Parse a .bard source string into structured data.

    Args:
        source: The .bard file content as a string

    Returns:
        Dict containing version, initial_passage, and passages
    """
    passages = {}
    current_passage = None

    lines = source.split("\n")

    for line in lines:
        # Passage Header: :: PassageName
        if line.startswith(":: "):
            passage_name = line[3:].strip()
            current_passage = {
                "id": passage_name,
                "content": [],
                "choices": []
            }
            passages[passage_name] = current_passage
            continue

        # Choice: + [Text] -> Target
        if line.startswith("+ ") and current_passage:
            # Match pattern: + [choice text] -> TargetPassage
            match = re.match(r'\+\s*\[(.*?)\]\s*->\s*(\w+)', line)
            if match:
                choice_text, target = match.groups()
                current_passage["choices"].append(
                    {
                        "text": choice_text,
                        "target": target
                    }
                )
            continue

        # Regular content line
        if line.strip() and current_passage:
            current_passage["content"].append(line)

    # Post-process: join content lines into single string per passage
    for passage in passages.values():
        passage["content"] = "\n".join(passage["content"])

    # Build final structure
    return {
        'version': '0.1.0',
        'initial_passage': list(passages.keys())[0] if passages else None,
        'passages': passages
    }


def parse_file(filepath: str) -> Dict[str, Any]:
    """
    Parse a .bard file from disk.

    Args:
        filepath: Path to the .bard file

    Returns:
        Parsed story structure
    """
    with open(filepath, "r", encoding="utf-8") as f:
        return parse(f.read())