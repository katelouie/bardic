# Save/Load System Improvement: @metadata Directive

**Date:** October 15, 2025
**Status:** ✅ COMPLETE
**Implementation:** CLI-Claude & Kate

---

## Summary

Successfully implemented the `@metadata` directive for Bardic story files, enabling authors to specify story metadata (title, author, version, story_id, description) at the top of their .bard files. This metadata is now automatically used by the save/load system for better story identification and version compatibility checking.

---

## Problem

Previously, the save/load system couldn't reliably identify which story a save file belonged to:
- Story JSON files had no built-in metadata
- Backend manually tracked story_id separately from engine
- No version information for compatibility checking
- No human-readable story names in save files
- Authors had no way to specify story information

---

## Solution

Added `@metadata` directive to Bardic language with:
- Clean, YAML-like syntax
- Optional and extensible fields
- Automatic integration with save/load system
- Backward compatibility (stories without metadata still work)
- Consistent with existing directive pattern (@start, @include)

---

## Implementation

### 1. Parser (`bardic/compiler/parser.py`)

**Added `extract_metadata()` function (lines 63-121):**
```python
def extract_metadata(source: str) -> tuple[dict[str, str], str]:
    """
    Extract @metadata block from the beginning of the file.

    Returns:
        Tuple of (metadata_dict, remaining_source)
    """
```

**Parsing rules:**
- Metadata must appear after imports but before passages
- Uses simple key-value pairs with indentation
- Empty lines allowed within block
- Block ends at first non-indented line
- All fields optional and extensible

**Updated `parse()` to:**
- Call `extract_metadata()` after import extraction (line 447)
- Include metadata in returned story structure (line 586)

---

### 2. Runtime Engine (`bardic/runtime/engine.py`)

**Updated `save_state()` (lines 1025-1041):**
```python
# Get metadata from story
story_metadata = self.story.get("metadata", {})

return {
    "version": "0.1.0",
    "story_version": story_metadata.get("version", "unknown"),
    "story_name": story_metadata.get("title", "unknown"),
    "story_id": story_metadata.get("story_id", "unknown"),
    # ... rest of save data
}
```

**Updated `load_state()` (lines 1067-1085):**
- Validates save compatibility using metadata
- Checks `story_id` first (primary identifier)
- Falls back to `story_name` check
- Prints warnings for mismatches but allows loading

---

### 3. Backend API (`web-runtime/backend/main.py`)

**Simplified `/api/story/save` (lines 261-268):**
- Removed manual story_id override
- Now uses story_id from `engine.save_state()` (via metadata)
- Single source of truth

**Enhanced `/api/stories` (lines 97-133):**
- Reads metadata from story JSON files
- Uses `metadata.title` for display name
- Uses `metadata.story_id` for identifier
- Returns full metadata in API response
- Graceful fallback if metadata missing

---

### 4. Documentation (`spec.md`)

**Added comprehensive "Metadata" section (lines 788-900):**
- Syntax explanation with examples
- Rules and structure
- Common metadata fields (title, author, version, story_id, description)
- Complete usage examples
- Compiled JSON output format
- Backend integration examples
- Benefits list

---

## Syntax

### Basic Metadata

```bard
@metadata
  title: The Oracle's Journey
  author: Kate Louie
  version: 1.0.0
  story_id: tarot_game
  description: A mystical tarot reading adventure

:: Start
Your story begins...
```

### File Structure Order

```bard
# 1. Imports (if needed)
from models.card import Card

# 2. Metadata (optional)
@metadata
  title: My Story
  version: 1.0.0

# 3. Includes (if needed)
@include shared/helpers.bard

# 4. Passages
@start Chapter1

:: Chapter1
Content here...
```

---

## Common Metadata Fields

| Field | Description | Used For |
|-------|-------------|----------|
| `title` | Human-readable story name | Display, save files, API |
| `author` | Story creator | Credits, attribution |
| `version` | Story version (e.g., "1.0.0") | Compatibility checking |
| `story_id` | Unique identifier | Save/load matching |
| `description` | Brief story description | Story browser, menus |

**All fields are optional.** Add custom fields as needed - the system is fully extensible.

---

## Compiled Output

### Story JSON Structure

```json
{
  "version": "0.1.0",
  "initial_passage": "Start",
  "metadata": {
    "title": "Metadata Test Story",
    "author": "CLI-Claude & Kate",
    "version": "1.0.0",
    "story_id": "test_metadata",
    "description": "A test story to verify @metadata directive works"
  },
  "imports": [],
  "passages": {
    "Start": { ... }
  }
}
```

### Save File Format

```json
{
  "version": "0.1.0",
  "story_version": "1.0.0",
  "story_name": "Metadata Test Story",
  "story_id": "test_metadata",
  "timestamp": "2025-10-15T...",
  "current_passage_id": "Chapter2",
  "state": { ... },
  "used_choices": [],
  "metadata": {
    "passage_count": 15,
    "initial_passage": "Start"
  }
}
```

---

## Benefits

✅ **Story Identification:** Save files now include story_id and story_name
✅ **Version Tracking:** Can check compatibility between save and story version
✅ **Better UX:** Human-readable story names in load menus
✅ **Author Control:** Writers specify their own metadata
✅ **Extensible:** Custom fields supported without code changes
✅ **Backward Compatible:** Stories without metadata still work
✅ **Single Source of Truth:** Backend uses metadata from story JSON
✅ **Clean Architecture:** Metadata separate from game state

---

## Test Results

All tests passed ✅:

**1. Parser Test**
- Metadata extracted correctly from .bard files
- Compilation successful

**2. Compilation Test**
- Metadata included in compiled JSON
- Correct structure and field values

**3. Engine Test: save_state()**
```
✓ Save version: 0.1.0
✓ Story name: Metadata Test Story
✓ Story ID: test_metadata
✓ Story version: 1.0.0
```

**4. Engine Test: load_state()**
- Fresh engine successfully loaded saved state
- Current passage restored correctly

**5. Compatibility Warning Test**
```
Warning: Save is from a different story ID:
  'different_story' vs 'test_metadata'
```
- Warning printed as expected
- Load still succeeded (graceful handling)

**6. CLI Playthrough Test**
- Story played correctly in terminal
- All passages rendered properly

---

## Files Modified

### Core Engine
- `bardic/compiler/parser.py`
  - Added: `extract_metadata()` function
  - Modified: `parse()` to use extract_metadata()

- `bardic/runtime/engine.py`
  - Modified: `save_state()` to use metadata
  - Modified: `load_state()` to validate with metadata

### Backend
- `web-runtime/backend/main.py`
  - Modified: `/api/story/save` endpoint
  - Modified: `/api/stories` endpoint

### Documentation
- `spec.md`
  - Added: Comprehensive "Metadata" section

### Test Files (New)
- `tests/test_metadata.bard`
- `compiled_stories/test_metadata.json`
- `test_metadata_runtime.py`

---

## Usage Example

### Creating a Story with Metadata

```bard
@metadata
  title: The Midnight Library
  author: Sarah Chen
  version: 2.1.0
  story_id: midnight_library
  description: Navigate an infinite library between life and death
  genre: Philosophical Fiction
  estimated_playtime: 45 minutes

@start Entrance

:: Entrance
Between life and death, there is a library.

You stand at the threshold, books stretching endlessly in all directions.

+ [Enter the library] -> FirstVisit
+ [Turn back] -> Return
```

### Backend API Usage

```python
# List stories - automatically uses metadata
response = await client.get("/api/stories")
# Returns:
# {
#   "stories": [
#     {
#       "id": "midnight_library",
#       "name": "The Midnight Library",
#       "metadata": {
#         "title": "The Midnight Library",
#         "author": "Sarah Chen",
#         "version": "2.1.0",
#         ...
#       }
#     }
#   ]
# }

# Save game - story_id automatically included
save_data = engine.save_state()
# {
#   "story_id": "midnight_library",
#   "story_name": "The Midnight Library",
#   "story_version": "2.1.0",
#   ...
# }
```

---

## Backward Compatibility

Stories without `@metadata` still work perfectly:

```bard
:: Start
A simple story with no metadata.

+ [Continue] -> Next
```

Compiled with defaults:
```json
{
  "metadata": {},
  ...
}
```

Save file uses defaults:
```json
{
  "story_name": "unknown",
  "story_id": "unknown",
  "story_version": "unknown",
  ...
}
```

---

## Next Steps (Optional Enhancements)

1. **Update Existing Stories**
   - Add metadata to test stories
   - Add metadata to real game stories (tarot, etc.)

2. **Frontend Integration**
   - Display story metadata in story browser
   - Show author and description in load menu
   - Display version in debug info

3. **Validation**
   - Add semantic version format validation
   - Check required fields in strict mode
   - Warn about unknown common fields (typos)

4. **Extended Metadata**
   - Support tags array
   - Support thumbnail URL
   - Support content warnings
   - Support estimated playtime

5. **CLI Enhancement**
   - Show metadata in `bardic play` header
   - Add `bardic info story.json` command to display metadata

---

## Related Documentation

- `spec.md` - Lines 788-900 (Metadata section)
- `docs/engine-api.md` - Save/load API documentation
- `CLAUDE.md` - Project overview and workflow
- `claude_info/CLI-Claude Thread 4.md` - Previous save/load work

---

**Implementation Status:** ✅ COMPLETE

All 7 steps of the implementation plan finished:
1. ✅ Parser: extract_metadata() function
2. ✅ Parser: parse() integration
3. ✅ Engine: save_state() uses metadata
4. ✅ Engine: load_state() validation
5. ✅ Backend: Uses metadata.story_id
6. ✅ Documentation: spec.md updated
7. ✅ Testing: test_metadata.bard verified

---

*Built with care by CLI-Claude & Kate, October 15, 2025*
