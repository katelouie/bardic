"""
Bardic linter — structural and quality analysis for .bard story files.

Works on the compiled passage graph (post-compilation), so it catches
issues that regex-based checkers can't: broken cross-file jump targets,
orphaned passages, dead ends, and more.
"""

import ast
import sys

# Fix Windows console encoding for Unicode symbols
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from bardic.cli.graph import extract_connections


# ============================================================================
# DIAGNOSTIC TYPES
# ============================================================================


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class Diagnostic:
    """A single lint finding."""

    severity: Severity
    code: str  # e.g., "E001", "W001", "I001"
    message: str
    file: str = ""
    line: int = 0
    hint: str = ""

    @property
    def icon(self) -> str:
        if self.severity == Severity.ERROR:
            return "✗"
        elif self.severity == Severity.WARNING:
            return "⚠"
        return "ℹ"

    @property
    def color(self) -> str:
        if self.severity == Severity.ERROR:
            return "red"
        elif self.severity == Severity.WARNING:
            return "yellow"
        return "cyan"


@dataclass
class LintReport:
    """Complete lint report for a story."""

    diagnostics: list[Diagnostic] = field(default_factory=list)
    # Metadata for the summary
    file_count: int = 0
    passage_count: int = 0
    choice_count: int = 0
    include_count: int = 0
    plugin_count: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for d in self.diagnostics if d.severity == Severity.INFO)

    @property
    def has_errors(self) -> bool:
        return self.error_count > 0

    def add(self, severity: Severity, code: str, message: str, **kwargs):
        self.diagnostics.append(Diagnostic(severity=severity, code=code, message=message, **kwargs))

    def error(self, code: str, message: str, **kwargs):
        self.add(Severity.ERROR, code, message, **kwargs)

    def warning(self, code: str, message: str, **kwargs):
        self.add(Severity.WARNING, code, message, **kwargs)

    def info(self, code: str, message: str, **kwargs):
        self.add(Severity.INFO, code, message, **kwargs)


# ============================================================================
# LINT CHECKS
# ============================================================================


def check_missing_passages(story_data: dict, report: LintReport):
    """E001: Jump targets that reference passages which don't exist."""
    connections, referenced, defined = extract_connections(story_data)
    missing = referenced - defined

    for passage_id in sorted(missing):
        # Find which passage(s) reference this missing target
        sources = []
        for source, targets in connections.items():
            for target, _, _ in targets:
                if target == passage_id:
                    sources.append(source)

        source_str = ", ".join(sources[:3])
        if len(sources) > 3:
            source_str += f" (+{len(sources) - 3} more)"

        report.error(
            "E001",
            f"Missing passage '{passage_id}' (referenced from: {source_str})",
            hint=f"Define :: {passage_id} or fix the jump target",
        )


def check_orphan_passages(story_data: dict, report: LintReport):
    """W001: Passages that can never be reached."""
    connections, referenced, defined = extract_connections(story_data)
    start_passage = story_data.get("initial_passage", "Start")

    # Build set of all passages reachable via any connection
    has_incoming = set()
    for targets in connections.values():
        for target, _, _ in targets:
            has_incoming.add(target)

    orphans = defined - has_incoming - {start_passage}

    for passage_id in sorted(orphans):
        report.warning(
            "W001",
            f"Orphaned passage '{passage_id}' — no incoming connections",
            hint="This passage is defined but never jumped to. Is it unreachable?",
        )


def check_dead_ends(story_data: dict, report: LintReport):
    """W002: Passages with no exits (no choices, no jumps) that aren't obvious endings."""
    connections, _, defined = extract_connections(story_data)
    passages = story_data.get("passages", {})

    for passage_id in sorted(defined):
        targets = connections.get(passage_id, [])
        if targets:
            continue  # Has at least one exit

        passage_data = passages.get(passage_id, {})

        # Check if this passage has choices defined at the top level
        if passage_data.get("choices"):
            continue  # Has choices (even if extract_connections didn't find jump targets)

        # Check if it has hooks that might redirect
        # (passages with @hook directives may have implicit exits)
        has_hook = False
        for cmd in passage_data.get("execute", []):
            if isinstance(cmd, dict) and cmd.get("type") in ("hook", "unhook"):
                has_hook = True
                break
        if has_hook:
            continue

        # Some dead ends are intentional (endings, completion passages)
        # Flag them as info rather than warning if they look like endings
        name_lower = passage_id.lower()
        is_likely_ending = any(
            keyword in name_lower
            for keyword in ["end", "complete", "finale", "epilogue", "gameover", "credits"]
        )

        if is_likely_ending:
            report.info(
                "I001",
                f"Dead-end passage '{passage_id}' (likely an intentional ending)",
            )
        else:
            report.warning(
                "W002",
                f"Dead-end passage '{passage_id}' — no choices or jumps",
                hint="This passage has no way forward. Intentional ending, or missing -> jump?",
            )


def check_duplicate_passages(story_data: dict, report: LintReport):
    """E002: Duplicate passage names (caught by compiler too, but included for completeness)."""
    # The compiler already catches this during compilation, so if we get here
    # the story compiled successfully. This check is a no-op but included
    # for the diagnostic code registry.
    pass


def check_empty_passages(story_data: dict, report: LintReport):
    """W003: Passages with no content."""
    passages = story_data.get("passages", {})

    for passage_id, passage_data in sorted(passages.items()):
        content = passage_data.get("content", [])
        choices = passage_data.get("choices", [])
        execute = passage_data.get("execute", [])

        # A passage is "empty" if it has no content, no choices, and no code
        # But passages with only a jump (-> Target) are fine — the jump is in content
        has_content = bool(content)
        has_choices = bool(choices)
        has_code = bool(execute)

        if not has_content and not has_choices and not has_code:
            report.warning(
                "W003",
                f"Empty passage '{passage_id}' — no content, choices, or code",
            )


def check_passage_choice_count(story_data: dict, report: LintReport):
    """I002: Passages with unusually many choices (readability concern).

    For conditional branches (@if/@elif/@else), counts the MAX across branches
    rather than the SUM, since the player only ever sees one branch.
    """
    passages = story_data.get("passages", {})
    THRESHOLD = 8

    for passage_id, passage_data in sorted(passages.items()):
        # Count all choices (top-level + inside conditionals)
        choices = passage_data.get("choices", [])

        # Count the max-visible choices in content
        # For conditionals: take the MAX branch (mutually exclusive)
        # For loops: add the choices (they accumulate)
        def max_visible_choices(content_tokens):
            count = 0
            for token in content_tokens:
                if isinstance(token, dict):
                    if token.get("type") == "conditional":
                        # Branches are mutually exclusive — take the max
                        branch_counts = []
                        for branch in token.get("branches", []):
                            bc = len(branch.get("choices", []))
                            bc += max_visible_choices(branch.get("content", []))
                            branch_counts.append(bc)
                        count += max(branch_counts) if branch_counts else 0
                    elif token.get("type") == "for_loop":
                        count += len(token.get("choices", []))
                        count += max_visible_choices(token.get("content", []))
            return count

        total = len(choices) + max_visible_choices(passage_data.get("content", []))

        if total > THRESHOLD:
            report.info(
                "I002",
                f"Passage '{passage_id}' has {total} visible choices (threshold: {THRESHOLD})",
                hint="Consider splitting into sub-passages for readability",
            )


def check_self_loops(story_data: dict, report: LintReport):
    """W004: Choices that jump back to the same passage (potential infinite loop)."""
    passages = story_data.get("passages", {})

    for passage_id, passage_data in sorted(passages.items()):
        for choice in passage_data.get("choices", []):
            if choice.get("target") == passage_id and choice.get("sticky", True):
                # Sticky choice that loops to itself — potential infinite loop
                choice_text = choice.get("text", "")
                if isinstance(choice_text, list):
                    choice_text = "[choice]"
                elif len(choice_text) > 40:
                    choice_text = choice_text[:37] + "..."
                report.warning(
                    "W004",
                    f"Sticky self-loop in '{passage_id}': [{choice_text}] -> {passage_id}",
                    hint="A sticky (+) choice that jumps to its own passage will always be available. Use * (one-time) instead?",
                )


# ============================================================================
# CLASS-AWARE ATTRIBUTE RESOLUTION (Level 2)
# ============================================================================


def _extract_class_definitions(
    python_source: str,
) -> dict[str, tuple[set[str], list[str]]]:
    """Parse a Python source file and extract class attributes and base classes.

    Returns {ClassName: (set_of_attributes, [base_class_names])}.

    Extracts:
    - Annotated fields (dataclass pattern): name: type = default
    - Class-level assignments: name = value
    - @property decorated methods
    - Private field → public name mapping (_trust → trust)
    """
    try:
        tree = ast.parse(python_source)
    except SyntaxError:
        return {}

    class_defs = {}

    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        attrs = set()
        bases = []

        # Get base class names
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(base.attr)

        # Scan class body (direct children only — not nested methods)
        for item in node.body:
            # Annotated field: name: type = default
            if isinstance(item, ast.AnnAssign) and isinstance(
                item.target, ast.Name
            ):
                name = item.target.id
                attrs.add(name)
                # _private → public (bounded property pattern)
                if name.startswith("_") and not name.startswith("__"):
                    attrs.add(name.lstrip("_"))

            # Class-level assignment: name = value
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        attrs.add(name)
                        if name.startswith("_") and not name.startswith("__"):
                            attrs.add(name.lstrip("_"))

            # @property method
            elif isinstance(item, ast.FunctionDef):
                for dec in item.decorator_list:
                    if isinstance(dec, ast.Name) and dec.id == "property":
                        attrs.add(item.name)
                        break

        class_defs[node.name] = (attrs, bases)

    return class_defs


def _resolve_class_attrs(
    code_snippets: list[tuple[str, str]],
    search_paths: list[Path] | None = None,
) -> dict[str, set[str]]:
    """Resolve class-defined attributes for objects used in the story.

    1. Finds 'from X.Y import Class1, Class2' in story code
    2. Locates the Python source files on disk
    3. Parses class definitions (fields, properties)
    4. Resolves inheritance chains (e.g., BlackthornManor inherits Client's attrs)
    5. Maps story variable names to classes via instantiation patterns
    6. Returns {object_name: {known_attributes}} for each mapped object
    """
    if search_paths is None:
        search_paths = [Path.cwd()]

    # Step 1: Find 'from X.Y import ...' statements in story code
    imports: dict[str, list[str]] = {}  # {module_path: [names]}
    for code, ctx in code_snippets:
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [alias.name for alias in node.names]
                if names:
                    imports.setdefault(node.module, []).extend(names)

    if not imports:
        return {}

    # Step 2: Resolve module paths to files and parse class definitions
    all_class_defs: dict[str, tuple[set[str], list[str]]] = {}
    parsed_files: set[str] = set()

    for module_path in imports:
        rel_path = Path(module_path.replace(".", "/") + ".py")
        for search_path in search_paths:
            full_path = search_path / rel_path
            if full_path.exists() and str(full_path) not in parsed_files:
                parsed_files.add(str(full_path))
                try:
                    source = full_path.read_text(encoding="utf-8")
                    file_classes = _extract_class_definitions(source)
                    all_class_defs.update(file_classes)
                except Exception:
                    pass
                break

    if not all_class_defs:
        return {}

    # Step 3: Resolve inheritance chains
    resolved: dict[str, set[str]] = {}

    def resolve_class(name: str, seen: set[str] | None = None) -> set[str]:
        if name in resolved:
            return resolved[name]
        if seen is None:
            seen = set()
        if name in seen:
            return set()  # circular
        seen.add(name)

        if name not in all_class_defs:
            return set()

        attrs, bases = all_class_defs[name]
        full_attrs = set(attrs)
        for base in bases:
            full_attrs |= resolve_class(base, seen)

        resolved[name] = full_attrs
        return full_attrs

    for class_name in all_class_defs:
        resolve_class(class_name)

    # Step 4: Map story variable names to classes
    obj_class_map: dict[str, str] = {}

    # 4a: Direct instantiation — var = ClassName(...)
    for code, ctx in code_snippets:
        try:
            tree = ast.parse(code, mode="exec")
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if (
                    isinstance(target, ast.Name)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id in resolved
                ):
                    obj_class_map[target.id] = node.value.func.id

    # 4b: Fuzzy match for remaining objects — "session" → "Session", "the_kind" → "TheKind"
    known_objects_in_story = set()
    for code, ctx in code_snippets:
        writes, reads, methods = parse_attribute_access(code)
        for obj, attr in writes:
            known_objects_in_story.add(obj)
        for obj, attr in reads:
            known_objects_in_story.add(obj)

    for obj_name in known_objects_in_story:
        if obj_name in obj_class_map:
            continue
        normalized = obj_name.lower().replace("_", "")
        for class_name in resolved:
            if class_name.lower() == normalized:
                obj_class_map[obj_name] = class_name
                break

    # Step 5: Build final object → attributes map
    obj_attrs: dict[str, set[str]] = {}
    for var_name, class_name in obj_class_map.items():
        if class_name in resolved:
            obj_attrs[var_name] = resolved[class_name]

    return obj_attrs


# ============================================================================
# ATTRIBUTE TRACKING (Level 1 static analysis + Level 2 class-aware)
# ============================================================================


def extract_python_code(story_data: dict) -> list[tuple[str, str]]:
    """
    Extract all Python code from a compiled story.

    Returns list of (code_string, context_description) tuples.
    Context is like "passage 'Chen.Session1' execute block" for diagnostics.
    """
    results = []

    # Top-level imports (stored separately from passages)
    for imp in story_data.get("imports", []):
        if isinstance(imp, str):
            results.append((imp, "top-level import"))

    passages = story_data.get("passages", {})

    for passage_id, passage_data in passages.items():
        ctx = f"passage '{passage_id}'"

        # Execute blocks (python_block and python_statement)
        for cmd in passage_data.get("execute", []):
            if isinstance(cmd, dict):
                code = cmd.get("code", "")
                if code:
                    results.append((code, ctx))

        # Choice conditions
        for choice in passage_data.get("choices", []):
            cond = choice.get("condition")
            if cond and isinstance(cond, str):
                # Wrap in expression context so ast can parse it
                results.append((cond, f"{ctx} choice condition"))

        # Recursively extract from content tokens
        _extract_from_content(passage_data.get("content", []), ctx, results)

    return results


def _extract_from_content(tokens: list, ctx: str, results: list):
    """Recursively extract Python expressions from content tokens."""
    for token in tokens:
        if not isinstance(token, dict):
            continue

        token_type = token.get("type")

        if token_type in ("python_block", "python_statement"):
            code = token.get("code", "")
            if code:
                results.append((code, ctx))

        elif token_type == "expression":
            expr = token.get("expression", "")
            if expr:
                results.append((expr, f"{ctx} expression"))

        elif token_type == "inline_conditional":
            cond = token.get("condition", "")
            if cond:
                results.append((cond, f"{ctx} inline conditional"))
            true_val = token.get("true_value", "")
            if true_val and isinstance(true_val, str):
                results.append((true_val, f"{ctx} inline conditional"))
            false_val = token.get("false_value", "")
            if false_val and isinstance(false_val, str):
                results.append((false_val, f"{ctx} inline conditional"))

        elif token_type == "conditional":
            for branch in token.get("branches", []):
                cond = branch.get("condition", "")
                if cond and isinstance(cond, str):
                    results.append((cond, f"{ctx} conditional"))
                _extract_from_content(branch.get("content", []), ctx, results)
                # Choices inside conditional branches
                for choice in branch.get("choices", []):
                    cond2 = choice.get("condition")
                    if cond2 and isinstance(cond2, str):
                        results.append((cond2, f"{ctx} choice condition"))

        elif token_type == "for_loop":
            iterable = token.get("iterable", "")
            if iterable and isinstance(iterable, str):
                results.append((iterable, f"{ctx} for loop"))
            _extract_from_content(token.get("content", []), ctx, results)
            for choice in token.get("choices", []):
                cond = choice.get("condition")
                if cond and isinstance(cond, str):
                    results.append((cond, f"{ctx} choice condition"))

        elif token_type == "render_directive":
            expr = token.get("expression", "")
            if expr:
                results.append((expr, f"{ctx} render"))


def parse_attribute_access(code: str) -> tuple[set[tuple[str, str]], set[tuple[str, str]], set[tuple[str, str]]]:
    """
    Parse a Python code string and extract attribute writes, reads, and method calls.

    Returns (writes, reads, method_calls) where each is a set of (object_name, attribute_name) tuples.

    Handles:
    - obj.attr = value   (write)
    - obj.attr += value  (augmented write — counts as both read and write)
    - obj.attr           (read)
    - obj.method()       (method call — tracked separately)
    """
    import textwrap

    writes = set()
    reads = set()
    method_calls = set()

    # Dedent code — compiled @py: blocks inside @if branches may have
    # leading whitespace that causes SyntaxError
    code = textwrap.dedent(code)

    # Try parsing as a module (statements)
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError:
        # Try as single expression
        try:
            tree = ast.parse(code, mode="eval")
        except SyntaxError:
            return writes, reads, method_calls

    for node in ast.walk(tree):
        # Assignment: obj.attr = value
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                    writes.add((target.value.id, target.attr))

        # Augmented assignment: obj.attr += value (both read and write)
        elif isinstance(node, ast.AugAssign):
            if isinstance(node.target, ast.Attribute) and isinstance(node.target.value, ast.Name):
                writes.add((node.target.value.id, node.target.attr))
                reads.add((node.target.value.id, node.target.attr))

        # Method call: obj.method(args)
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                method_calls.add((func.value.id, func.attr))
                # Don't add to reads — methods are defined on the class,
                # not written in .bard files

        # Attribute read: obj.attr (but not if it's an assignment target or method call)
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if isinstance(node.ctx, ast.Load):
                reads.add((node.value.id, node.attr))

    # Remove method calls from reads (ast.walk visits the Call AND
    # the inner Attribute separately, so we need to subtract)
    reads -= method_calls

    return writes, reads, method_calls


# Objects whose attributes we should NOT track (builtins, framework internals)
_IGNORE_OBJECTS = {
    # Python builtins and common modules
    "len", "range", "str", "int", "float", "bool", "list", "dict", "set",
    "print", "type", "isinstance", "hasattr", "getattr", "setattr",
    "math", "random", "json", "os", "sys", "re",
    # Common attribute access patterns that aren't game state
    "self", "cls",
}

# Attributes that are too common / generic to track meaningfully
_IGNORE_ATTRIBUTES = {
    # Python dunder/special
    "__init__", "__str__", "__repr__", "__dict__", "__class__",
    # Common method names that could be on anything
    "append", "extend", "pop", "remove", "get", "items", "keys", "values",
    "copy", "clear", "update", "add", "format", "join", "split", "strip",
    "lower", "upper", "replace", "startswith", "endswith", "count",
}


def check_attribute_consistency(
    story_data: dict,
    report: LintReport,
    python_search_paths: list[Path] | None = None,
):
    """W005: Track attribute reads and writes across all Python code in the story.

    Flags:
    - W005: Attributes that are READ but never WRITTEN anywhere in the story
            (likely typos or missing initialization)

    Smart about:
    - Method calls (obj.method()) are not flagged as missing attributes
    - Properties that have a corresponding add_X() method are assumed valid
      (e.g., nyx.trust is OK if nyx.add_trust() is called)
    - Attributes on unknown objects (no writes at all) are skipped
    - Level 2: Class-defined attributes (from Python source files) are treated
      as known writes — fields, properties, and inherited attributes
    """
    # Collect all Python code from the story
    code_snippets = extract_python_code(story_data)

    # Track all attribute access globally
    all_writes: dict[tuple[str, str], list[str]] = defaultdict(list)
    all_reads: dict[tuple[str, str], list[str]] = defaultdict(list)
    all_methods: dict[tuple[str, str], list[str]] = defaultdict(list)

    for code, context in code_snippets:
        writes, reads, methods = parse_attribute_access(code)
        for key in writes:
            all_writes[key].append(context)
        for key in reads:
            all_reads[key].append(context)
        for key in methods:
            all_methods[key].append(context)

    # Build per-object known attribute/method sets
    obj_known_attrs: dict[str, set[str]] = defaultdict(set)
    obj_known_methods: dict[str, set[str]] = defaultdict(set)
    for (obj, attr) in all_writes:
        obj_known_attrs[obj].add(attr)
    for (obj, method) in all_methods:
        obj_known_methods[obj].add(method)

    # Level 2: Add class-defined attributes from Python source files
    class_attrs = _resolve_class_attrs(code_snippets, python_search_paths)
    for obj_name, attrs in class_attrs.items():
        obj_known_attrs[obj_name].update(attrs)

    # Find reads without writes (W005)
    for (obj, attr), read_contexts in sorted(all_reads.items()):
        if obj in _IGNORE_OBJECTS or attr in _IGNORE_ATTRIBUTES:
            continue

        # Skip if this attribute is written somewhere in .bard code
        if (obj, attr) in all_writes:
            continue

        # Skip if attribute is defined on the object's Python class
        # (class fields, properties, inherited attributes)
        if attr in obj_known_attrs.get(obj, set()):
            continue

        # Skip if the object has no writes at all (unknown object — could be
        # a function return value, loop variable, etc.)
        if obj not in obj_known_attrs:
            continue

        # Skip if there's a corresponding add_X() / set_X() method
        # (indicates a property backed by a method, like trust / add_trust)
        methods = obj_known_methods.get(obj, set())
        if f"add_{attr}" in methods or f"set_{attr}" in methods:
            continue

        # Skip if the attr itself is a known method (method referenced
        # without calling it — rare but possible)
        if attr in methods:
            continue

        # This looks like a genuinely unknown attribute — report it
        known_attrs = sorted(obj_known_attrs[obj])
        hint = f"'{obj}' has these written attributes: {', '.join(known_attrs[:8])}"

        # Check for close matches (typo detection)
        import difflib
        # Search both written attrs AND methods for close matches
        all_known = known_attrs + sorted(methods)
        close = difflib.get_close_matches(attr, all_known, n=1, cutoff=0.7)
        if close:
            hint = f"Did you mean '{obj}.{close[0]}'?"

        ctx_str = read_contexts[0]
        if len(read_contexts) > 1:
            ctx_str += f" (+{len(read_contexts) - 1} more)"

        report.warning(
            "W005",
            f"'{obj}.{attr}' is read but never written (in {ctx_str})",
            hint=hint,
        )


# ============================================================================
# MAIN LINT FUNCTION
# ============================================================================


# Structural checks (standard signature: story_data, report)
_STRUCTURAL_CHECKS = [
    check_missing_passages,
    check_orphan_passages,
    check_dead_ends,
    check_empty_passages,
    check_passage_choice_count,
    check_self_loops,
]


def lint_story(
    story_data: dict,
    python_search_paths: list[Path] | None = None,
) -> LintReport:
    """
    Run all lint checks on a compiled story.

    Args:
        story_data: Compiled story dict (output of BardCompiler.compile_string()
                    or loaded from compiled JSON)
        python_search_paths: Directories to search when resolving Python imports
                             for class-aware attribute checking. Defaults to CWD.

    Returns:
        LintReport with all findings
    """
    report = LintReport()

    # Gather metadata
    passages = story_data.get("passages", {})
    report.passage_count = len(passages)
    report.choice_count = sum(
        len(p.get("choices", []))
        for p in passages.values()
    )

    # Run structural checks
    for check_fn in _STRUCTURAL_CHECKS:
        check_fn(story_data, report)

    # Run attribute consistency check (with class-aware resolution)
    check_attribute_consistency(story_data, report, python_search_paths)

    return report


# ============================================================================
# PLUGIN SYSTEM
# ============================================================================


def _discover_plugins(
    start_dir: Path,
) -> tuple[list[tuple[callable, str]], Path | None]:
    """Find a linter/ directory and collect check_* functions from .py files.

    Walks up from start_dir looking for a directory named 'linter/'.
    Loads all .py files that don't start with '_' (those are shared helpers).
    Collects all check_* functions from each module.

    Args:
        start_dir: Directory to start searching from (typically the .bard file's parent)

    Returns:
        (list of (check_function, module_name) tuples, project_root or None)
    """
    import importlib.util

    # Walk up to find linter/ directory
    linter_dir = None
    project_root = None
    current = start_dir.resolve()
    for _ in range(6):  # Don't walk too far
        candidate = current / "linter"
        if candidate.is_dir():
            linter_dir = candidate
            project_root = current
            break
        if current == current.parent:
            break
        current = current.parent

    if linter_dir is None:
        # Also check CWD
        candidate = Path.cwd() / "linter"
        if candidate.is_dir():
            linter_dir = candidate
            project_root = Path.cwd()

    if linter_dir is None:
        return [], None

    # Load plugin modules
    checks = []
    for py_file in sorted(linter_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue  # Skip private/helper files

        module_name = py_file.stem
        try:
            spec = importlib.util.spec_from_file_location(
                f"bardic_lint_plugin.{module_name}", py_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Collect check_* functions
            for attr_name in sorted(dir(module)):
                if attr_name.startswith("check_") and callable(
                    getattr(module, attr_name)
                ):
                    checks.append((getattr(module, attr_name), module_name))

        except Exception as e:
            # Don't crash the linter if a plugin fails to load
            import sys

            print(
                f"  Warning: Failed to load lint plugin '{module_name}': {e}",
                file=sys.stderr,
            )

    return checks, project_root


def lint_file(
    input_path: str | Path,
    no_plugins: bool = False,
) -> LintReport:
    """
    Lint a .bard file by compiling it first, then running structural checks.

    Args:
        input_path: Path to a .bard file
        no_plugins: If True, skip project-specific lint plugins

    Returns:
        LintReport with all findings

    Raises:
        Exception: If the file fails to compile (compilation errors are
                   reported by the compiler, not the linter)
    """
    from bardic.compiler.compiler import BardCompiler
    from bardic.compiler.parsing.preprocessing import resolve_includes

    input_path = Path(input_path)
    source = input_path.read_text(encoding="utf-8")

    # Count included files by inspecting SourceLocation entries in line_map
    resolved_source, line_map = resolve_includes(source, str(input_path.resolve()))
    include_files = set()
    for entry in line_map:
        if hasattr(entry, "file_path"):
            include_files.add(entry.file_path)

    # Compile
    compiler = BardCompiler()
    story_data = compiler.compile_string(resolved_source)

    # Determine search paths for Python imports (class-aware checking)
    # Include CWD and parent directories of the input file
    search_paths = [Path.cwd()]
    current = input_path.parent.resolve()
    for _ in range(5):  # Walk up to find project root
        if current not in search_paths:
            search_paths.append(current)
        if current == current.parent:
            break
        current = current.parent

    # Lint (built-in checks)
    report = lint_story(story_data, python_search_paths=search_paths)
    report.file_count = max(1, len(include_files))
    report.include_count = report.file_count - 1

    # Run project-specific lint plugins
    if not no_plugins:
        plugins, project_root = _discover_plugins(input_path.parent)
        if plugins:
            report.plugin_count = len(plugins)
            if project_root is None:
                project_root = Path.cwd()
            for check_fn, module_name in plugins:
                try:
                    check_fn(story_data, report, project_root)
                except Exception as e:
                    report.warning(
                        "P000",
                        f"Plugin '{module_name}.{check_fn.__name__}' failed: {e}",
                    )

    return report
