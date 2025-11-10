from bardic import BardEngine
import json
import random

# Load story
with open("test_python_blocks.json") as f:
    story = json.load(f)


# Create context with helper functions
def greet(name):
    return f"Hello, {name}!"


def roll_dice(sides=6):
    return random.randint(1, sides)


context = {
    "greet": greet,
    "roll_dice": roll_dice,
}

# Create engine with context
engine = BardEngine(story, context=context)

# Test
output = engine.current()
print(output.content)
