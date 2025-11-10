from bardic.compiler.parser import parse
import json

test_story = """
:: Start
~ health = 45

<<if health > 75>>
Strong!
<<elif health > 25>>
Okay.
<<else>>
Weak!
<<endif>>
"""

result = parse(test_story)
print(json.dumps(result, indent=2))
