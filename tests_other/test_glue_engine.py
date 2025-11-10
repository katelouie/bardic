"""Test glue operator and empty line handling"""

from bardic.runtime.engine import BardEngine

# Load test story
engine = BardEngine.from_file("test_glue.json")

print("=" * 70)
print("GLUE OPERATOR & EMPTY LINE TESTS")
print("=" * 70)

output = engine.current()
print(output.content)

print("\n" + "=" * 70)
print("EXPECTED OUTPUT:")
print("=" * 70)
print("""Test 1: Glue with conditional

The cards whisper, and you feel their meaning in your bones.

---

Test 2: Pluralization

You have 3 items.

---

Test 3: Loop glue

The spread contains Fool Magician Priestess.

---

Test 4: Empty lines (paragraph breaks)

Paragraph 1.

Paragraph 2.

Paragraph 3.

---

Test 5: Literal <> in middle of line

The formula is x <> y (this should show the <>).
""")

print("=" * 70)
print("✓ TEST COMPLETED!")
print("=" * 70)
