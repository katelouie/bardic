from bardic.compiler.parser import parse
import json

test_story = """
:: Start
~ health = 0

You check your health...

-> Death

You're alive!

:: Death
You died.
"""

result = parse(test_story)
print(json.dumps(result["passages"]["Start"]["content"], indent=2))
