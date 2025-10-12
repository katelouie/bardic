from bardic import BardEngine
import json

# Load the compiled story
with open("compiled_stories/test_render_directives.json") as f:
    story = json.load(f)

# Create engine with context
# from game_logic.test_tarot_objects import Card

# context = {"Card": Card}

engine = BardEngine(story)

# Get the first passage
output = engine.current()

print("=== PASSAGE OUTPUT ===")
print(f"Content: {output.content[:100]}...")
print(f"\nChoices: {output.choices}")
print(f"\nRender Directives: {len(output.render_directives)} found")

for i, directive in enumerate(output.render_directives):
    print(f"\nDirective {i + 1}:")
    print(f"  Name: {directive['name']}")
    print(f"  Mode: {directive['mode']}")
    if "data" in directive:
        print(f"  Data keys: {list(directive['data'].keys())}")
    if "react" in directive:
        print(f"  React component: {directive['react']['componentName']}")
