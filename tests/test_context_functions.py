"""Test calling context functions from expressions"""

import json
import random
from bardic import BardEngine


def roll_dice(sides=6):
    """Roll a die with given number of sides"""
    return random.randint(1, sides)


def greet(name):
    """Generate a greeting"""
    return f"Hello, {name}!"


def calculate_damage(attack, defense):
    """Calculate combat damage"""
    base_damage = max(0, attack - defense)
    return base_damage + random.randint(0, 5)


def main():
    # Load compiled story
    with open("test_functions.json") as f:
        story = json.load(f)

    # Create context with functions
    context = {
        "roll_dice": roll_dice,
        "greet": greet,
        "calculate_damage": calculate_damage,
    }

    # Create engine with context
    engine = BardEngine(story, context=context)

    # Test
    output = engine.current()
    print(output.content)
    print()

    # Show choices
    for i, choice in enumerate(output.choices):
        print(f"{i + 1}. {choice['text']}")


if __name__ == "__main__":
    main()
