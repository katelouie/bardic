from bardic.compiler.parser import parse
import json

test_story = """
:: Start
~ items = ["sword", "shield"]

<<for item in items>>
- {item}
<<endfor>>
"""

result = parse(test_story)
print(json.dumps(result, indent=2))
