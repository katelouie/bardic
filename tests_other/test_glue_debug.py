"""Debug glue test"""

from bardic.runtime.engine import BardEngine
import traceback

try:
    # Load test story
    engine = BardEngine.from_file("test_glue.json")

    output = engine.current()
    print("FULL CONTENT:")
    print(repr(output.content))
    print("\n" + "="*70 + "\n")
    print(output.content)
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
