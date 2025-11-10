from bardic.compiler.parser import parse

# Test with a simple story
test_story = """
:: Start
Hello world!
This is the first passage.

+ [Go next] -> Next

:: Next
This is the second passage.
"""

result = parse(test_story)
import json
print(json.dumps(result, indent=2))