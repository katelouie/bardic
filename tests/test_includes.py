from bardic.compiler.parser import parse_file
import json

result = parse_file("test_includes/main.bard")
print(json.dumps(result, indent=2))

# Check that all passages are present
passages = result["passages"]
print("\nPassages found:")
for name in passages.keys():
    print(f"  - {name}")

try:
    result = parse_file("test_includes/circular_a.bard")
    print("ERROR: Should have detected circular include!")
except ValueError as e:
    print(f"✓ Circular include detected: {e}")
