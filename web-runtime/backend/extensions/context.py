"""
Custom context functions for your game.

These functions will be available in your Bardic stories.
"""

import sys
from pathlib import Path

import random

# Add game_logic to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_game_context():
    """
    Return custom context functions for your game.

    Add your game-specific functions here.
    They'll be available in stories as {my_function(...)}
    """
    # Import your game logic
    return {
        # Utility functions
        "random_int": lambda min_val, max_val: random.randint(min_val, max_val),
        "random_choice": lambda items: random.choice(items),
        "chance": lambda probability: random.random < probability,
    }
