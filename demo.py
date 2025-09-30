"""Demonstration of the Bardic runtime engine."""

from bardic import BardEngine
import time
import sys


def typewriter_print(text: str, delay: float=0.03) -> None:
    """Print text with a typewriter effect."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def demo():
    """Run an interactive demo."""

    # Load the story
    print("Loading story...")
    engine = BardEngine.from_file("test_story.json")

    # Show story info
    info = engine.get_story_info()
    print(f"\nStory loaded: {info['passage_count']} passages")
    print(f"Starting at: {info['initial_passage']}\n")

    time.sleep(1)

    # Play through
    while True:
        output = engine.current()

        # Display passage
        print("=" * 60)
        typewriter_print(output.content)
        print("=" * 60)
        print()

        # Check for ending
        if engine.is_end():
            print("THE END")
            break

        # Show choices
        print("What do you do?\n")
        choices = output.choices
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice['text']}")

        print()

        # Get user input
        while True:
            try:
                choice_input = input("Enter your choice (1-{})".format(len(choices)))
                choice_num = int(choice_input)

                if 1 <= choice_num <= len(choices):
                    engine.choose(choice_num - 1)
                    print()
                    break
                else:
                    print(f"Please enter a number between 1 and {len(choices)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                sys.exit(0)

if __name__ == "__main__":
    print("=" * 60)
    print("  BARDIC ENGINE DEMO")
    print("=" * 60)
    print()

    demo()