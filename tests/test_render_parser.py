from bardic.compiler.parser import parse
import json

test_story = """
:: Start
~ cards = ["Fool", "Magician", "Priestess"]

Here are some cards:

@render spread(cards, layout='simple')

And with React convenience:

@render:react card_detail(cards[0], position='past')

+ [Continue] -> End

:: End
Done!
"""

result = parse(test_story)
print(json.dumps(result, indent=2))
