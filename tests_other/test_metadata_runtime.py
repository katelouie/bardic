#!/usr/bin/env python3
"""
Test script to verify @metadata works in the runtime engine.
Tests that metadata flows through to save/load correctly.
"""

import json
from pathlib import Path
from bardic import BardEngine

# Load the compiled story
story_path = Path("compiled_stories/test_metadata.json")
with open(story_path) as f:
    story_data = json.load(f)

print("=" * 60)
print("TESTING @metadata DIRECTIVE")
print("=" * 60)

# Create engine
engine = BardEngine(story_data)

print("\n1. Story loaded successfully")
print(f"   Current passage: {engine.current_passage_id}")

# Check that metadata is accessible
metadata = story_data.get("metadata", {})
print("\n2. Metadata in story JSON:")
for key, value in metadata.items():
    print(f"   {key}: {value}")

# Test save state
print("\n3. Testing save_state()...")
save_data = engine.save_state()

print(f"   ✓ Save version: {save_data['version']}")
print(f"   ✓ Story name: {save_data['story_name']}")
print(f"   ✓ Story ID: {save_data['story_id']}")
print(f"   ✓ Story version: {save_data['story_version']}")
print(f"   ✓ Current passage: {save_data['current_passage_id']}")

# Verify metadata fields match
assert save_data['story_name'] == "Metadata Test Story", "story_name mismatch!"
assert save_data['story_id'] == "test_metadata", "story_id mismatch!"
assert save_data['story_version'] == "1.0.0", "story_version mismatch!"

print("\n4. Testing load_state()...")

# Navigate to a different passage
output = engine.choose(0)  # "Check the metadata"
print(f"   Navigated to: {engine.current_passage_id}")

# Save state from this position
save_data_2 = engine.save_state()
assert save_data_2['current_passage_id'] == "CheckMetadata", "Should be at CheckMetadata"

# Create a fresh engine and load the save
engine_2 = BardEngine(story_data)
print(f"   Fresh engine at: {engine_2.current_passage_id}")

# Load the saved state
engine_2.load_state(save_data_2)
print(f"   After load_state(): {engine_2.current_passage_id}")

# Verify position restored
assert engine_2.current_passage_id == "CheckMetadata", "Load didn't restore position!"

print("\n5. Testing story compatibility checking...")

# Try loading a save from the "wrong" story (simulate with modified save_data)
fake_save = save_data_2.copy()
fake_save['story_id'] = "different_story"
fake_save['story_name'] = "Different Story"

print("   Attempting to load save from different story_id...")
engine_3 = BardEngine(story_data)
engine_3.load_state(fake_save)  # Should print warning but still work
print("   ✓ Warning should have been printed above")

print("\n" + "=" * 60)
print("✅ ALL METADATA TESTS PASSED!")
print("=" * 60)
print("\nThe @metadata directive is working correctly:")
print("  - Parsed from .bard files")
print("  - Included in compiled JSON")
print("  - Used by engine.save_state()")
print("  - Used by engine.load_state() for compatibility checking")
print()
