#!/usr/bin/env python3
"""
Runtime tests for augmented assignment operators.
"""

import sys
sys.path.insert(0, '/Users/katelouie/code/bardic')

from bardic.runtime.engine import BardEngine

def test_basic_operators():
    """Test all 7 augmented assignment operators."""
    print("=" * 60)
    print("TEST 1: Basic Augmented Assignment Operators")
    print("=" * 60)

    engine = BardEngine.from_file("test_augmented_assignment.json")
    output = engine.goto("Start")

    # Expected state after all operations:
    # count: 0 -> +1=1 -> //2=0
    # health: 100 -> -25=75 -> %10=5
    # multiplier: 2 -> *3=6 -> **2=36
    # price: 100.0 -> /4=25.0

    expected = {
        "count": 0,          # (0 + 1) // 2 = 0
        "health": 5,         # (100 - 25) % 10 = 5
        "multiplier": 36,    # (2 * 3) ** 2 = 36
        "price": 25.0        # 100.0 / 4 = 25.0
    }

    print("\nFinal state:")
    for var, expected_val in expected.items():
        actual_val = engine.state.get(var)
        status = "✓" if actual_val == expected_val else "✗"
        print(f"  {status} {var:12} = {actual_val:6} (expected {expected_val})")

    # Check all match
    all_match = all(engine.state.get(var) == val for var, val in expected.items())
    print(f"\n{'✓ ALL TESTS PASSED' if all_match else '✗ SOME TESTS FAILED'}")
    return all_match

def test_complex_expressions():
    """Test augmented assignment with complex expressions."""
    print("\n" + "=" * 60)
    print("TEST 2: Complex Expressions")
    print("=" * 60)

    engine = BardEngine.from_file("test_augmented_complex.json")
    output = engine.goto("Start")

    # Expected state:
    # base: 10 -> +(5*2+3)=23 -> +(5*2)=33 -> -(3+5)=25 -> *(2+1)=75
    # bonus: 5
    # penalty: 3

    expected = {
        "base": 75,
        "bonus": 5,
        "penalty": 3
    }

    print("\nFinal state:")
    for var, expected_val in expected.items():
        actual_val = engine.state.get(var)
        status = "✓" if actual_val == expected_val else "✗"
        print(f"  {status} {var:12} = {actual_val:6} (expected {expected_val})")

    all_match = all(engine.state.get(var) == val for var, val in expected.items())
    print(f"\n{'✓ ALL TESTS PASSED' if all_match else '✗ SOME TESTS FAILED'}")
    return all_match

def test_multiline():
    """Test augmented assignment with multiline expressions."""
    print("\n" + "=" * 60)
    print("TEST 3: Multiline Expressions")
    print("=" * 60)

    engine = BardEngine.from_file("test_augmented_multiline.json")
    output = engine.goto("Start")

    # Expected state:
    # total: 0 -> +(10+20+30)=60 -> *(2+3)=300

    expected_total = 300
    actual_total = engine.state.get("total")

    status = "✓" if actual_total == expected_total else "✗"
    print(f"\n  {status} total = {actual_total} (expected {expected_total})")

    all_match = actual_total == expected_total
    print(f"\n{'✓ ALL TESTS PASSED' if all_match else '✗ SOME TESTS FAILED'}")
    return all_match

def main():
    """Run all tests."""
    print("\nAUGMENTED ASSIGNMENT OPERATOR RUNTIME TESTS")
    print("=" * 60)

    results = []
    results.append(test_basic_operators())
    results.append(test_complex_expressions())
    results.append(test_multiline())

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} test suites passed")

    if all(results):
        print("\n✓ ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
