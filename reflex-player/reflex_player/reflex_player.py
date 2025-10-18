import reflex as rx
from typing import Any

# Story data structure (same as NiceGUI version)
STORY = {
    "Start": {
        "text": "You wake up in a dimly lit room. A door to your left, window to your right.",
        "choices": [
            {"text": "Check the door", "target": "Door"},
            {"text": "Look out window", "target": "Window"},
        ],
    },
    "Door": {
        "text": "The door is locked. A keyhole glints.",
        "choices": [
            {"text": "Pick the lock", "target": "Ending1"},
            {"text": "Go back", "target": "Start"},
        ],
    },
    "Window": {
        "text": "Through the window: a moonlit garden. Window is ajar.",
        "choices": [
            {"text": "Climb out", "target": "Ending2"},
            {"text": "Go back", "target": "Start"},
        ],
    },
    "Ending1": {"text": "Lock clicks open! Freedom!", "choices": []},
    "Ending2": {"text": "You slip into the cool night air.", "choices": []},
}


# State class - this is reflex's pattern
class StoryState(rx.State):
    current_passage_id: str = "Start"

    @rx.var
    def current_passage(self) -> dict[str, Any]:
        """Get the current passage data"""
        return STORY[self.current_passage_id]

    @rx.var
    def current_choices(self) -> list[dict[str, str]]:
        """Get the choices for the current passage"""
        return STORY[self.current_passage_id]["choices"]

    def navigate_to(self, target_id: str):
        """Navigate to a new passage."""
        self.current_passage_id = target_id


def index() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                # Title
                rx.heading("Locked Room Escape", size="8"),
                # Passage text
                rx.text(
                    StoryState.current_passage["text"], size="5", color_scheme="gray"
                ),
                # Choices or THE END
                rx.cond(
                    StoryState.current_choices.length() > 0,
                    # Show buttons if there are choices
                    rx.vstack(
                        rx.foreach(
                            StoryState.current_choices,
                            lambda choice: rx.button(
                                choice["text"],
                                on_click=lambda: StoryState.navigate_to(
                                    choice["target"]
                                ),
                                size="3",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    # Show THE END if no choices
                    rx.text(
                        "THE END",
                        size="5",
                        color_scheme="gray",
                        style={"font_style": "italic"},
                    ),
                ),
                spacing="6",
                width="100%",
            ),
            max_width="600px",
        ),
        padding="8",
    )


app = rx.App()
app.add_page(index)
