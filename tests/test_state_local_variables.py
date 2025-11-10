"""
Test _state and _local special variables.

These tests verify that story writers can:
- Check if variables exist with _state
- Access variables safely with defaults
- Inspect local scope (passage parameters) with _local
- Distinguish between global state and local parameters
"""

import pytest
from textwrap import dedent
from bardic.compiler.compiler import BardCompiler
from bardic.runtime.engine import BardEngine


@pytest.fixture
def compile_and_run():
    """Helper to compile and run a story string."""
    def _compile_and_run(source):
        # Dedent to handle triple-quoted strings with indentation
        source = dedent(source).strip()
        compiler = BardCompiler()
        story = compiler.compile_string(source)
        engine = BardEngine(story)
        return engine
    return _compile_and_run


def test_state_get_with_default(compile_and_run):
    """Test that _state.get() provides safe access with defaults."""
    source = """
    :: Start
    ~ hp = 100

    HP: {_state.get('hp')}
    Missing: {_state.get('nonexistent', 'DEFAULT')}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "HP: 100" in output.content
    assert "Missing: DEFAULT" in output.content


def test_state_existence_check(compile_and_run):
    """Test checking if variables exist with 'in _state'."""
    source = """
    :: Start
    ~ gold = 500

    Has gold: {'gold' in _state}
    Has hp: {'hp' in _state}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "Has gold: True" in output.content
    assert "Has hp: False" in output.content


def test_state_keys(compile_and_run):
    """Test inspecting available state variables."""
    source = """
    :: Start
    ~ var1 = 1
    ~ var2 = 2

    Has var1: {'var1' in _state.keys()}
    Has var2: {'var2' in _state.keys()}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "Has var1: True" in output.content
    assert "Has var2: True" in output.content


def test_local_empty_without_params(compile_and_run):
    """Test that _local is empty dict in passages without parameters."""
    source = """
    :: Start

    Local empty: {len(_local) == 0}
    Local keys: {list(_local.keys())}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "Local empty: True" in output.content
    assert "Local keys: []" in output.content


def test_local_with_params(compile_and_run):
    """Test that _local contains passage parameters."""
    source = """
    :: Start

    + [Go] -> Target(42, "test")

    :: Target(x, y)

    X in local: {'x' in _local}
    Y in local: {'y' in _local}
    X value: {_local.get('x')}
    Y value: {_local.get('y')}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    engine.choose(0)  # Go to Target
    output = engine.current()

    assert "X in local: True" in output.content
    assert "Y in local: True" in output.content
    assert "X value: 42" in output.content
    assert "Y value: test" in output.content


def test_local_with_optional_params(compile_and_run):
    """Test _local with optional parameters."""
    source = """
    :: Start

    + [Go] -> Target(100)

    :: Target(required, optional="default")

    Required: {_local.get('required')}
    Optional: {_local.get('optional')}
    Keys: {sorted(_local.keys())}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    engine.choose(0)
    output = engine.current()

    assert "Required: 100" in output.content
    assert "Optional: default" in output.content
    assert "Keys: ['optional', 'required']" in output.content


def test_params_not_in_state(compile_and_run):
    """Test that local parameters don't leak into global state."""
    source = """
    :: Start
    ~ global_var = "global"

    + [Go] -> Target(42)

    :: Target(param)

    Param in local: {'param' in _local}
    Param in state: {'param' in _state}
    Global in state: {'global_var' in _state}
    Global in local: {'global_var' in _local}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    engine.choose(0)
    output = engine.current()

    assert "Param in local: True" in output.content
    assert "Param in state: False" in output.content  # Params don't leak!
    assert "Global in state: True" in output.content
    assert "Global in local: False" in output.content  # Globals not in local!


def test_state_in_conditionals(compile_and_run):
    """Test using _state in @if conditionals."""
    source = """
    :: Start
    ~ hp = 100

    @if _state.get('hp', 0) > 50:
        HP is high!
    @endif

    @if 'missing' in _state:
        This should not appear
    @else:
        Missing variable not found
    @endif

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "HP is high!" in output.content
    assert "Missing variable not found" in output.content
    assert "This should not appear" not in output.content


def test_local_in_conditionals(compile_and_run):
    """Test using _local in conditionals."""
    source = """
    :: Start

    + [Go] -> Target(100)

    :: Target(hp)

    @if _local.get('hp', 0) > 50:
        HP parameter is high
    @endif

    @if 'hp' in _local:
        HP parameter exists
    @endif

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    engine.choose(0)
    output = engine.current()

    assert "HP parameter is high" in output.content
    assert "HP parameter exists" in output.content


def test_state_in_inline_conditionals(compile_and_run):
    """Test _state in inline conditionals."""
    source = """
    :: Start
    ~ hp = 75

    Status: {_state.get('hp', 0) > 50 ? Healthy | Injured}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "Status: Healthy" in output.content


def test_local_in_inline_conditionals(compile_and_run):
    """Test _local in inline conditionals."""
    source = """
    :: Start

    + [Go] -> Target(25)

    :: Target(damage)

    Impact: {_local.get('damage', 0) > 50 ? Critical | Normal}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    engine.choose(0)
    output = engine.current()

    assert "Impact: Normal" in output.content


def test_state_in_loops(compile_and_run):
    """Test _state in for loops."""
    source = """
    :: Start
    ~ items = ["sword", "shield", "potion"]

    @if 'items' in _state:
        @for item in _state.get('items', []):
            - {item}
        @endfor
    @endif

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "- sword" in output.content
    assert "- shield" in output.content
    assert "- potion" in output.content


def test_state_with_complex_objects(compile_and_run):
    """Test _state with complex objects (dicts, lists)."""
    source = """
    :: Start
    ~ player = {"name": "Hero", "level": 5}
    ~ inventory = ["sword", "shield"]

    Player exists: {'player' in _state}
    Player name: {_state.get('player', {}).get('name', 'Unknown')}
    Inventory count: {len(_state.get('inventory', []))}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "Player exists: True" in output.content
    assert "Player name: Hero" in output.content
    assert "Inventory count: 2" in output.content


def test_state_defensive_coding(compile_and_run):
    """Test defensive coding patterns with _state."""
    source = """
    :: Start

    # Safe access - no crash if missing
    HP: {_state.get('hp', 100)}
    Name: {_state.get('name', 'Stranger')}

    # Conditional rendering based on existence
    @if _state.get('has_sword'):
        You wield a mighty sword!
    @else:
        You are unarmed.
    @endif

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    # Variables don't exist, should use defaults
    assert "HP: 100" in output.content
    assert "Name: Stranger" in output.content
    assert "You are unarmed." in output.content


def test_local_defensive_coding(compile_and_run):
    """Test defensive coding with _local in reusable passages."""
    source = """
    :: Start

    + [With item] -> ShowItem("Sword")
    + [Without item] -> ShowItem()

    :: ShowItem(item=None)

    @if _local.get('item'):
        You examine the {item}.
    @else:
        You have nothing to examine.
    @endif

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)

    # Test with item
    engine.choose(0)
    output = engine.current()
    assert "You examine the Sword." in output.content

    # Reset and test without item
    engine2 = compile_and_run(source)
    engine2.choose(1)
    output2 = engine2.current()
    assert "You have nothing to examine." in output2.content


def test_state_and_local_together(compile_and_run):
    """Test using both _state and _local together."""
    source = """
    :: Start
    ~ global_hp = 100

    + [Attack] -> Combat(25)

    :: Combat(damage)

    # Note: Can check state and local, but modification happens in execute
    Local damage: {_local.get('damage')}
    State has global_hp: {'global_hp' in _state}

    ~ new_hp = _state.get('global_hp', 0) - _local.get('damage', 0)

    Result: {new_hp}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    engine.choose(0)
    output = engine.current()

    assert "Local damage: 25" in output.content
    assert "State has global_hp: True" in output.content
    assert "Result: 75" in output.content


def test_state_always_available(compile_and_run):
    """Test that _state is always available, even in first passage."""
    source = """
    :: Start
    ~ test_var = 42

    State available: {_state is not None}
    Can access keys: {'test_var' in _state.keys()}
    Can get values: {_state.get('test_var') == 42}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "State available: True" in output.content
    assert "Can access keys: True" in output.content
    assert "Can get values: True" in output.content


def test_local_always_available(compile_and_run):
    """Test that _local is always available (empty if no params)."""
    source = """
    :: Start

    Local available: {_local is not None}
    Local empty: {len(_local) == 0}
    Local keys empty: {list(_local.keys()) == []}

    + [Done] -> End

    :: End
    Complete
    """

    engine = compile_and_run(source)
    output = engine.current()

    assert "Local available: True" in output.content
    assert "Local empty: True" in output.content
    assert "Local keys empty: True" in output.content
