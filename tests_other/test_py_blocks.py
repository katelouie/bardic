from bardic.compiler.parser import parse
import json

test_story = """
:: Start
<<py
x = 5
y = 10
result = x + y
>>

Result is {result}
"""

result = parse(test_story)
print(json.dumps(result, indent=2))
