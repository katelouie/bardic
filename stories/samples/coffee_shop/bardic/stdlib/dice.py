"""Dice rolling and probability helpers for game mechanics.

Usage:
    from bardic.stdlib.dice import roll, skill_check, weighted_choice

    # Simple rolls
    result = roll('1d20')      # 1-20
    damage = roll('3d6+5')   # 3d6 plus 5

    # Skill checks
    if skill_check(player.dexterity, dc=15):
        print("Success!")

    # Weighted random choice
    outcome = weighted_choice(['win', 'lose'], [0.7, 0.3])
"""

import random
import re


def roll(notation: str = "1d6") -> int:
    """Roll dice using standard notation (e.g., '3d6', '1d20+5').

    Args:
        notation: Dice notation like '2d6', '1d20+3', '4d8-2'

    Returns:
        Total result of the roll

    Examples:
        >>> roll('1d6')      # 1-6
        >>> roll('3d6+5')    # 3d6 plus 5
        >>> roll('2d10-3')   # 2d10 minus 3
    """
    # Parse notation: XdY+Z or XdY-Z
    match = re.match(r"(\d+)d(\d+)([+-]\d+)?", notation.strip())
    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")

    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0

    # Roll the dice
    total = sum(random.randint(1, num_sides) for _ in range(num_dice))
    return total + modifier


def skill_check(stat: int, dc: int, bonus: int = 0) -> bool:
    """Perform a d20 skill check.

    Args:
        stat: Character's stat value (added to roll)
        dc: Difficulty class to beat
        bonus: Optional bonus/penalty to roll

    Returns:
        True if check succeeds (roll + stat + bonus >= dc)

    Example:
        >>> if skill_check(player.dexterity, dc=15):
        ...     print("You dodge the trap!")
    """
    result = roll("1d20") + stat + bonus
    return result >= dc


def weighted_choice(options: list, weights: list):
    """Choose randomly from options with given weights.

    Args:
        options: List of possible outcomes
        weights: List of probabilities (must sum to 1.0 or be relative)

    Returns:
        One randomly chosen option

    Example:
        >>> outcome = weighted_choice(['crit', 'hit', 'miss'], [0.1, 0.6, 0.3])
    """
    return random.choices(options, weights=weights, k=1)[0]


def advantage() -> int:
    """Roll 2d20, take the higher (D&D advantage)."""
    return max(roll("1d20"), roll("1d20"))


def disadvantage() -> int:
    """Roll 2d20, take the lower (D&D disadvantage)."""
    return min(roll("1d20"), roll("1d20"))
