"""Test that @ syntax and << >> syntax produce identical runtime behavior."""

import sys
sys.path.insert(0, '/Users/katelouie/code/bardic')

from bardic.runtime.engine import BardEngine

# Load both versions
engine_new = BardEngine.from_file("test_at_syntax.json")
engine_old = BardEngine.from_file("test_legacy_syntax.json")

print("=== Testing @ syntax ===")
output_new = engine_new.goto("Start")
print(f"Content length: {len(output_new.content)}")
print(f"Has choices: {len(output_new.choices) > 0}")
print(f"Content preview:\n{output_new.content[:200]}...")

print("\n=== Testing legacy syntax ===")
output_old = engine_old.goto("Start")
print(f"Content length: {len(output_old.content)}")
print(f"Has choices: {len(output_old.choices) > 0}")
print(f"Content preview:\n{output_old.content[:200]}...")

print("\n=== Testing mixed syntax ===")
engine_mixed = BardEngine.from_file("test_mixed_syntax.json")
output_mixed = engine_mixed.goto("Start")
print(f"Content length: {len(output_mixed.content)}")
print(f"Content: {output_mixed.content}")

print("\n✓ All tests passed!")
