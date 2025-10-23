"""Generate visual graphs of Bardic story structure."""

import json
from pathlib import Path
from typing import Dict, Set, List, Tuple
import graphviz


def extract_connections(story_data: dict) -> Tuple[Dict[str, List[str]], Set[str], Set[str]]:
    """Extract passage connections from compiled story.

    Returns:
        (connections_dict, all_referenced_passages, all_defined_passages)
    """
    connections = {}  # passage_id -> list of (target, choice_text, is_jump)
    defined_passages = set()
    referenced_passages = set()

    passages = story_data.get("passages", {})

    for passage_id, passage_data in passages.items():
        defined_passages.add(passage_id)
        connections[passage_id] = []

        # Extract choice targets
        for choice in passage_data.get("choices", []):
            target = choice.get("target")
            if target:
                referenced_passages.add(target)
                choice_text = choice.get("text", "")
                # Truncate long choice text
                if len(choice_text) > 30:
                    choice_text = choice_text[:27] + "..."
                connections[passage_id].append((target, choice_text, False))

        # Extract jump targets from content
        def extract_jumps_from_content(content_tokens):
            """Recursively extract jumps from content."""
            for token in content_tokens:
                if isinstance(token, dict):
                    if token.get("type") == "jump":
                        target = token.get("target")
                        if target:
                            referenced_passages.add(target)
                            connections[passage_id].append((target, "→", True))
                    elif token.get("type") == "conditional":
                        # Check branches
                        for branch in token.get("branches", []):
                            extract_jumps_from_content(branch.get("content", []))
                    elif token.get("type") == "for_loop":
                        extract_jumps_from_content(token.get("content", []))

        content = passage_data.get("content", [])
        if isinstance(content, list):
            extract_jumps_from_content(content)

    return connections, referenced_passages, defined_passages


def generate_graph(
    story_file: Path,
    output_file: Path,
    format: str = "png",
    show_tags: bool = True
) -> None:
    """Generate a visual graph of the story structure.

    Args:
        story_file: Path to compiled JSON story
        output_file: Path for output graph file (without extension)
        format: Output format (png, svg, pdf)
        show_tags: Whether to show passage tags
    """
    # Load story
    with open(story_file, 'r') as f:
        story_data = json.load(f)

    # Extract connections
    connections, referenced, defined = extract_connections(story_data)

    # Find missing passages
    missing = referenced - defined

    # Create graph
    dot = graphviz.Digraph(comment='Bardic Story Graph')
    dot.attr(rankdir='TB')  # Top to bottom layout
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # Get start passage
    start_passage = story_data.get("initial_passage", "Start")

    passages = story_data.get("passages", {})

    # Add passage nodes
    for passage_id in defined:
        passage_data = passages.get(passage_id, {})

        # Build label
        label = passage_id
        if show_tags and passage_data.get("tags"):
            tags_str = " ".join([f"^{tag}" for tag in passage_data["tags"]])
            label = f"{passage_id}\\n{tags_str}"

        # Color code
        fillcolor = 'lightblue'
        if passage_id == start_passage:
            fillcolor = 'lightgreen'
        elif passage_data.get("tags"):
            if "CLIENT" in passage_data["tags"]:
                fillcolor = 'lightcoral'
            elif "SPECIAL" in passage_data["tags"]:
                fillcolor = 'gold'

        dot.node(passage_id, label, fillcolor=fillcolor)

    # Add missing passage nodes (in red)
    for passage_id in missing:
        dot.node(passage_id, f"{passage_id}\\n[MISSING]",
                fillcolor='red', fontcolor='white')

    # Add connections
    for source, targets in connections.items():
        for target, label, is_jump in targets:
            # Different style for jumps vs choices
            if is_jump:
                dot.edge(source, target, label=label, style='dashed', color='gray')
            else:
                dot.edge(source, target, label=label)

    # Render
    output_path = str(output_file)
    dot.render(output_path, format=format, cleanup=True)

    # Print summary
    print(f"\n✓ Generated story graph: {output_path}.{format}")
    print(f"  Passages: {len(defined)}")
    print(f"  Connections: {sum(len(targets) for targets in connections.values())}")

    if missing:
        print(f"\n⚠ Missing passages ({len(missing)}):")
        for passage_id in sorted(missing):
            print(f"  - {passage_id}")

    # Find orphans (passages with no incoming connections except start)
    has_incoming = set()
    for targets in connections.values():
        for target, _, _ in targets:
            has_incoming.add(target)

    orphans = defined - has_incoming - {start_passage}
    if orphans:
        print(f"\n⚠ Orphaned passages ({len(orphans)}):")
        for passage_id in sorted(orphans):
            print(f"  - {passage_id}")
