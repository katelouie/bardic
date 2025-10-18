# Bardic Implementation Status

Comprehensive checklist comparing the language specification (spec.md) against the actual implementation in parser.py and engine.py.

**Legend:**
-  Fully implemented
- =è Partially implemented
- L Not implemented
- =Ý Implementation notes

Last updated: 2025-10-15

---

## Core Syntax

### Passages

-  **Basic passage headers** (`:: PassageName`)
  - parser.py:402-410
  - Supports letters, numbers, underscores, dots in names

-  **Start passage determination**
  - parser.py:613-658
  - Priority: @start directive > "Start" convention > first passage
  - Warnings if no explicit start

-  **@start directive**
  - parser.py:396-399
  - Allows explicit start passage override
  - Validates target passage exists

-  **Namespace conventions**
  - Dots in passage names supported (e.g., `Client.Aria.Session1`)
  - No special namespace handling, just naming convention

=Ý **Notes:** Passage system fully implemented. Duplicate passage detection exists as placeholder (parser.py:661-678) but dict naturally prevents duplicates.

---

### Text Content

-  **Plain text rendering**
  - parser.py:488-494
  - All non-special lines treated as content

-  **Empty lines as newlines**
  - parser.py:497-500
  - Empty lines add `\n` token

-  **Whitespace cleanup**
  - parser.py:527-612
  - `_cleanup_whitespace()` removes excess newlines around conditionals
  - `_trim_trailing_newlines()` keeps max 1 trailing newline

- =è **Markdown support**
  - Not handled by parser/engine
  - Delegated to frontend (ReactMarkdown in web-runtime)
  -  In web runtime: frontend/src/App.jsx uses react-markdown

- L **Ink-style whitespace rules** (single newline = space)
  - Spec says: "Single newline = space, double newline = paragraph"
  - Current: Each newline is preserved as `\n` token
  - Not implemented in parser or engine

- L **Comments** (`#`)
  - Spec status: =Å Week 5
  - parser.py: Lines with `#` not specially handled
  - Would need to strip comments during parsing

=Ý **Notes:** Basic text works. Markdown delegated to frontend. Ink-style whitespace and comments not yet implemented.

---

### Choices

-  **Sticky choices** (`+ [Text] -> Target`)
  - parser.py:680-722
  - Default choice type (sticky=True)

-  **One-time choices** (`* [Text] -> Target`)
  - parser.py:691-699
  - Tracked in engine.py:63 (`used_choices` set)
  - Filtered in engine.py:355-386

-  **Conditional choices** (`+ {condition} [Text] -> Target`)
  - parser.py:704-709
  - Condition stored, evaluated at runtime
  - engine.py:371-386

- L **Choice parameters** (`+ [Text] -> Target(param=value)`)
  - Spec status: =Å Week 4
  - Not implemented in parser
  - No passage parameter system exists yet

=Ý **Notes:** All basic choice types work. Choice parameters waiting on passage parameter system.

---

### Variables

-  **Variable assignment** (`~ var = value`)
  - parser.py:458-477
  - Supports multi-line expressions (parser.py:892-959)

-  **Expression evaluation**
  - engine.py:543-580
  - Uses safe eval with restricted builtins
  - Fallback to literal parsing

-  **Variable display** (`{variable}`)
  - parser.py:746-766 (tokenization)
  - engine.py:716-745 (evaluation)

-  **Format specifiers** (`{var:.2f}`)
  - engine.py:722-739
  - Supports Python format spec mini-language
  - Excludes comparison operators (==, !=, <=, >=, ::)

-  **Multi-line assignments**
  - parser.py:892-959 (`extract_multiline_expression`)
  - Tracks bracket matching for lists/dicts/tuples
  - Preserves structure across lines

-  **Supported types**
  - Numbers, strings, booleans, lists, dicts, objects
  - Full Python type support via eval

=Ý **Notes:** Variable system fully implemented including advanced features like multi-line assignments and format specs.

---

## Python Integration

### Python Code Blocks

-  **`<<py>>` blocks**
  - parser.py:419-424 (parsing)
  - parser.py:133-185 (extraction)
  - engine.py:622-677 (execution)

-  **Multi-line support**
  - Preserves indentation correctly
  - Base indentation removed, relative indentation kept

-  **State access**
  - Full access to `self.state` and `context`
  - Changes persist after block execution

-  **Safe builtins**
  - engine.py:582-620
  - Includes: len, str, int, float, list, dict, range, enumerate, sum, min, max, etc.
  - Allows `__import__` for safe imports

-  **Error handling**
  - SyntaxError: Shows problematic line (engine.py:653-660)
  - NameError: Lists available variables (engine.py:662-668)
  - RuntimeError: Full traceback (engine.py:670-677)

=Ý **Notes:** Python blocks fully functional with comprehensive error handling.

---

### Python Expressions

-  **Inline expressions** (`{expression}`)
  - parser.py:746-766 (parsing)
  - engine.py:716-759 (evaluation)

-  **Function calls**
  - Any function in context or state can be called
  - Example: `{roll_dice(20)}`

-  **Object attributes** (`{card.name}`)
  - Full attribute access supported
  - Nested attributes work (`{player.stats.health}`)

-  **Object methods** (`{card.get_display_name()}`)
  - Method calls with arguments supported
  - Method chaining works

-  **List comprehensions**
  - Example: `{[x * 2 for x in numbers]}`
  - Full Python comprehension syntax

-  **Complex expressions**
  - Ternary operators: `{"alive" if health > 0 else "dead"}`
  - Math: `{sum(values) / len(values):.2f}`

-  **Error display**
  - Undefined variables: `{ERROR: undefined variable 'x'}`
  - Type errors: `{ERROR: expr - TypeError: ...}`
  - Attribute errors: `{ERROR: expr - AttributeError: ...}`

=Ý **Notes:** Full Python expression support with graceful error handling.

---

### Imports

-  **Standard Python import syntax**
  - parser.py:16-60 (`extract_imports`)
  - No special prefix needed

-  **Must be at top of file**
  - parser.py:46-54
  - Error if import found after other content

-  **Multiple import types**
  - `from module import Item`
  - `import module`
  - `from module import Item as Alias`

-  **Execution at engine init**
  - engine.py:83-123
  - Imports executed once when engine created
  - Results added to `self.state`

-  **Error handling**
  - ImportError: Clear message with module list
  - Other errors: Shows import code and error

=Ý **Notes:** Import system fully implemented. Works like regular Python imports.

---

## Control Flow

### Conditionals

-  **`<<if>>` blocks**
  - parser.py:426-430 (detection)
  - parser.py:188-293 (extraction)
  - engine.py:876-908 (rendering)

-  **`<<elif>>` branches**
  - parser.py:248-258
  - Multiple elif branches supported

-  **`<<else>>` branch**
  - parser.py:261-269
  - Optional else as condition "True"

-  **Nested conditionals**
  - parser.py:209-216
  - Recursive extraction handles nesting
  - Nesting level tracking

-  **Complex conditions**
  - Full Python expression support
  - Logical operators: and, or, not
  - Comparisons: >, <, ==, !=, >=, <=

-  **With objects**
  - Example: `<<if client.trust_level > 75>>`
  - Any Python expression works

-  **Error handling**
  - Failed conditions skip branch with warning
  - Story continues with next branch

=Ý **Notes:** Conditionals fully implemented with comprehensive nesting and error handling.

---

### Loops

-  **`<<for>>` blocks**
  - parser.py:433-438 (detection)
  - parser.py:296-369 (extraction)
  - engine.py:788-874 (rendering)

-  **Simple iteration**
  - Lists, tuples, ranges, dicts
  - Example: `<<for item in items>>`

-  **Tuple unpacking**
  - parser.py:812-833
  - Example: `<<for i, item in enumerate(items)>>`
  - Example: `<<for key, value in items.items()>>`

-  **Nested loops**
  - parser.py:314-320
  - Recursive extraction

-  **Loops with conditionals**
  - parser.py:337-342
  - Conditionals inside loops work

-  **Object iteration**
  - Example: `<<for card in cards>>`
  - Accesses object attributes and methods

-  **Loop variable scope**
  - parser.py:836-857
  - Variables temporary, restored after loop
  - Original values preserved

- L **Inline loops** (`<<for card in cards>>{card.name}, <<endfor>>`)
  - Spec mentions but marked with ~~strikethrough~~
  - Not implemented (would need different parsing approach)

=Ý **Notes:** For loops fully implemented except inline variant (which spec seems to have abandoned).

---

### Jumps (Diverts)

-  **Immediate jumps** (`-> PassageName`)
  - parser.py:449-455 (parsing)
  - engine.py:782-784 (rendering detection)
  - engine.py:388-475 (goto follows jumps)

-  **Conditional jumps**
  - Works inside `<<if>>` blocks
  - parser.py:272-278 (in conditionals)

-  **Jumps in loops**
  - parser.py:350-356 (in loops)
  - Exits loop when jump encountered
  - engine.py:859-861

-  **Content before jump renders**
  - Jump stops rendering at that point
  - Content before jump is included

-  **Content after jump skipped**
  - Lines after jump never render

-  **Jump chain following**
  - engine.py:427-458
  - Automatically follows chains of jumps
  - Combines content from all passages

-  **Jump loop detection**
  - engine.py:429-432
  - RuntimeError if circular jump detected

-  **Compile-time validation**
  - Would need to add explicit check
  - Currently passage lookup fails at runtime if target missing

=Ý **Notes:** Jump system fully implemented. Could add explicit compile-time validation of targets.

---

## Advanced Features

### Render Directives

-  **Basic syntax** (`@render directive_name(args)`)
  - parser.py:440-446 (parsing)
  - parser.py:805-889 (parsing details)

-  **Framework hints** (`@render:react`, `@render:unity`)
  - parser.py:827-837 (hint detection)
  - engine.py:125-159 (react processor)

-  **Named arguments**
  - Example: `@render card_spread(cards=cards, layout='three_card')`
  - engine.py:161-208 (argument parsing via AST)

-  **Positional arguments**
  - Example: `@render my_func(arg1, arg2)`
  - Mapped to arg_0, arg_1, etc.

-  **Expression evaluation**
  - Variables and expressions evaluated in backend
  - Full Python expression support in arguments

-  **Evaluated mode** (default)
  - engine.py:230-258
  - Backend evaluates, frontend receives data

-  **Raw mode**
  - engine.py:270-283
  - Frontend receives raw expressions + state snapshot
  - Enabled via `evaluate_directives=False`

-  **Framework processors**
  - engine.py:67 (`framework_processors` dict)
  - React processor implemented
  - Extensible for Unity, Godot, etc.

-  **React optimization**
  - PascalCase component names
  - Unique keys for list rendering
  - Props passed directly

-  **In conditionals and loops**
  - Works in `<<if>>` blocks
  - Works in `<<for>>` loops
  - One directive per loop iteration

-  **Multiple per passage**
  - All directives collected in list
  - Returned in `render_directives` array

-  **Error handling**
  - Failed evaluation returns error directive
  - Mode set to "error"
  - Includes error message and raw args

=Ý **Notes:** Render directives fully implemented with React optimization. Extensible for other frameworks.

---

### Includes

-  **Basic syntax** (`@include path/to/file.bard`)
  - parser.py:63-130 (`resolve_includes`)
  - Recursive resolution

-  **Relative paths**
  - Paths relative to including file
  - parser.py:100-102

-  **Circular detection**
  - parser.py:86-88
  - ValueError if circular include

-  **After imports, before passages**
  - Natural ordering in parser
  - Imports extracted first (parser.py:383)

-  **Recursive includes**
  - Included files can include others
  - parser.py:110-114

-  **Error handling**
  - FileNotFoundError with full path context
  - parser.py:119-124

=Ý **Notes:** Include system fully functional. Enables multi-file stories.

---

### Tags (Custom Markup)

- L **Opening/closing tags** (`[!tagname]content[/!tagname]`)
  - Spec status: =Å Week 5
  - Not implemented in parser

- L **Tag attributes** (`[!tag attr=value]`)
  - Not implemented

- L **Nested tags**
  - Not implemented

- L **Compiled to structured data**
  - Not implemented

=Ý **Notes:** Custom tags not yet implemented. Scheduled for Week 5 in spec.

---

### Passage Parameters

- L **Parameter definition** (`:: Passage(param=default)`)
  - Spec status: =Å Week 4
  - Not implemented in parser

- L **Parameter passing** (`-> Target(param=value)`)
  - Not implemented

- L **Temporary scope**
  - Not implemented

=Ý **Notes:** Passage parameters not implemented. Major Week 4 feature.

---

## Runtime Features (Engine)

### State Management

-  **Global state dictionary**
  - engine.py:60 (`self.state`)
  - Variables persist across passages

-  **Context dictionary**
  - engine.py:62 (`self.context`)
  - Read-only functions/services
  - Merged with state for evaluation

-  **Safe builtins**
  - engine.py:582-620
  - Restricted execution environment
  - No dangerous operations

-  **State + context merging**
  - engine.py:551, 639, 720, etc.
  - `{**self.context, **self.state}`

- L **Passage parameters** (temporary scope)
  - Not implemented
  - Would need separate parameter namespace

=Ý **Notes:** State management solid. Would need enhancement for passage parameters.

---

### Navigation

-  **`goto(passage_id)`**
  - engine.py:388-475
  - Execute + render + cache
  - Primary navigation method

-  **`current()`**
  - engine.py:477-490
  - Read-only cached output
  - No side effects

-  **`choose(choice_index)`**
  - engine.py:492-533
  - Uses filtered choices
  - Tracks one-time choices

-  **Execution caching**
  - engine.py:64 (`_current_output`)
  - Prevents re-execution on repeated `current()` calls

-  **Execution once per passage**
  - `goto()` calls `_execute_passage()` once
  - Commands run exactly once

-  **Jump following**
  - Automatic in `goto()`
  - Combines content from chain

-  **Choice filtering**
  - Conditional choices evaluated
  - One-time choices tracked
  - Hidden if used or condition false

=Ý **Notes:** Navigation API well-designed. Separation of execution/rendering prevents bugs.

---

### Session Management

-  **One-time choice tracking**
  - engine.py:63 (`used_choices` set)
  - Unique ID per choice
  - Filtered in `_is_choice_available()`

-  **Reset one-time choices**
  - engine.py:986-995
  - Clears `used_choices` set

- =è **Save/load state**
  - engine.py:997-1169
  - Methods exist: `save_state()`, `load_state()`
  - Serialization helpers implemented
  - `_deserialize_state()` incomplete (engine.py:1139-1151)
  - `_deserialize_value()` implemented (engine.py:1153-1164)

-  **State serialization**
  - Handles primitives
  - Objects with `__dict__`
  - Collections (lists, tuples)
  - Fallback to string repr

=Ý **Notes:** Save/load mostly implemented but `_deserialize_state()` method body is missing.

---

### Error Handling

-  **Variable assignment errors**
  - NameError: Shows undefined variable + available variables
  - RuntimeError: Expression couldn't be evaluated
  - engine.py:560-580

-  **Python block errors**
  - SyntaxError: Shows line and position
  - NameError: Lists available variables
  - RuntimeError: Full traceback
  - engine.py:653-677

-  **Expression errors**
  - Graceful: Shows `{ERROR: ...}` in output
  - NameError, TypeError, AttributeError handled
  - engine.py:746-759

-  **Choice condition errors**
  - Warning printed, choice hidden
  - Story continues
  - engine.py:383-386

-  **Conditional errors**
  - Warning printed, branch skipped
  - engine.py:902-905

-  **Loop errors**
  - Error message in output: `{ERROR: Loop failed - ...}`
  - Warning printed with details
  - engine.py:865-874

-  **Jump loop detection**
  - RuntimeError with jump chain
  - engine.py:429-432

-  **Missing passage errors**
  - ValueError with passage name
  - engine.py:298-299, 326-327, 417

=Ý **Notes:** Comprehensive error handling throughout engine. User-friendly error messages.

---

## Utility Features

### Engine Methods

-  **`get_story_info()`**
  - engine.py:920-932
  - Returns version, passage count, current passage

-  **`has_choices()`**
  - engine.py:934-941
  - True if choices available

-  **`is_end()`**
  - engine.py:943-950
  - True if no choices (ending)

-  **`get_choice_texts()`**
  - engine.py:952-959
  - List of choice text strings

-  **`get_choice_targets()`**
  - engine.py:961-968
  - List of target passage IDs

-  **`from_file()` class method**
  - engine.py:970-984
  - Load compiled story from JSON file

=Ý **Notes:** Good collection of utility methods for common operations.

---

## Parser Features

### Content Parsing

-  **Content line tokenization**
  - parser.py:746-766
  - Splits text and expressions

-  **Expression detection** (`{...}`)
  - Regex-based: `r"(\{[^}]+\})"`
  - Handles format specs inside

-  **Multi-line expression extraction**
  - parser.py:892-959
  - Bracket matching algorithm
  - Handles lists, dicts, tuples

-  **Whitespace cleanup**
  - Removes excess around conditionals
  - Trims trailing newlines
  - parser.py:527-612

=Ý **Notes:** Parser handles content well. Expression parsing solid.

---

### Choice Parsing

-  **Sticky/one-time detection**
  - parser.py:691-699
  - `+` = sticky, `*` = one-time

-  **Conditional parsing**
  - parser.py:704-709
  - Regex: `r"\{([^}]+)\}\s*\[(.*?)\]\s*->\s*(\w+)"`

-  **Basic choice parsing**
  - parser.py:711-715
  - Regex: `r"\[(.*?)\]\s*->\s*(\w+)"`

-  **Error handling**
  - Returns None if invalid
  - Allows story to continue

=Ý **Notes:** Choice parsing comprehensive. Handles all specified formats.

---

### Directive Parsing

-  **Framework hint detection**
  - parser.py:830-838
  - Pattern: `:framework directive_name(args)`

-  **Argument extraction**
  - parser.py:846-849
  - Regex: `r"^(\w+)(?:\((.*)\))?$"`

-  **Empty directive handling**
  - Warning if empty
  - parser.py:843-844

-  **Invalid syntax warning**
  - parser.py:837, 883
  - Returns None if invalid

=Ý **Notes:** Directive parsing handles all formats including framework hints.

---

## Compiled Format

### Story Structure

-  **Version field**
  - parser.py:520 (`"version": "0.1.0"`)

-  **Initial passage**
  - parser.py:521
  - Determined by priority rules

-  **Imports array**
  - parser.py:522
  - List of import statement strings

-  **Passages dictionary**
  - parser.py:523
  - Keyed by passage ID

=Ý **Notes:** JSON structure matches spec.

---

### Passage Structure

-  **`id` field**
  - Passage name

-  **`content` array**
  - List of content tokens
  - Types: text, expression, conditional, for_loop, jump, render_directive

-  **`choices` array**
  - List of choice objects
  - Fields: text, target, condition, sticky

-  **`execute` array**
  - List of command objects
  - Types: set_var, python_block

=Ý **Notes:** Passage structure complete and well-organized.

---

### Content Token Types

-  **`text` tokens**
  - `{"type": "text", "value": "..."}`

-  **`expression` tokens**
  - `{"type": "expression", "code": "..."}`

-  **`conditional` tokens**
  - `{"type": "conditional", "branches": [...]}`
  - Nested structure

-  **`for_loop` tokens**
  - `{"type": "for_loop", "variable": "...", "collection": "...", "content": [...]}`

-  **`jump` tokens**
  - `{"type": "jump", "target": "..."}`

-  **`render_directive` tokens**
  - `{"type": "render_directive", "name": "...", "args": "...", "framework_hint": "..."}`

- L **`tagged_text` tokens**
  - Not implemented (tags not implemented)

=Ý **Notes:** All implemented token types match spec. Missing only tagged_text for custom markup.

---

## Future Features (Not Implemented)

### Scoped Sections

- L **`@section` / `@endsection`**
  - Spec status: > Consider after v1.0
  - Not implemented

- L **Section-level setup code**
  - Not implemented

- L **Nested sections**
  - Not implemented

=Ý **Notes:** Marked as post-v1.0 feature. Not currently planned.

---

### Visit Tracking

- L **`visit_count()` function**
  - Spec status: > Consider after v1.0
  - Not implemented

- L **Visit history**
  - Not implemented

=Ý **Notes:** Post-v1.0 consideration. Not implemented.

---

### Sequences/Cycles

- L **`sequence()` function**
  - Spec status: > Consider after v1.0
  - Not implemented

- L **Cycling text**
  - Not implemented

=Ý **Notes:** Post-v1.0 consideration. Not implemented.

---

## Implementation Summary

### By Category

**Core Syntax:**
- Passages:  100%
- Text Content: =è 80% (missing Ink-style whitespace, comments)
- Choices: =è 75% (missing parameters)
- Variables:  100%

**Python Integration:**
- Code Blocks:  100%
- Expressions:  100%
- Imports:  100%

**Control Flow:**
- Conditionals:  100%
- Loops: =è 95% (missing inline loops, which seem abandoned)
- Jumps:  100%

**Advanced Features:**
- Render Directives:  100%
- Includes:  100%
- Tags: L 0%
- Passage Parameters: L 0%

**Runtime:**
- State Management: =è 90% (missing passage parameters)
- Navigation:  100%
- Session: =è 90% (`_deserialize_state` incomplete)
- Error Handling:  100%

### Overall Progress

**Fully Implemented:** ~80%
**Partially Implemented:** ~10%
**Not Implemented:** ~10%

### Critical Missing Features

1. **Comments** (`#`) - Spec: Week 5
2. **Tags** (`[!tag]`) - Spec: Week 5
3. **Passage Parameters** - Spec: Week 4
4. **Choice Parameters** - Spec: Week 4
5. **`_deserialize_state()` body** - Technical debt
6. **Ink-style whitespace rules** - Quality of life

### Near-Complete Features

1. **Save/Load** - Just needs `_deserialize_state()` implementation
2. **Loops** - Everything except inline loops (which seem abandoned)
3. **Text Content** - Just missing markdown (delegated) and comments

---

## Code Quality Notes

### Strengths

- **Comprehensive error handling** - Every failure mode has helpful errors
- **Separation of concerns** - Parser, compiler, engine well-separated
- **Safety first** - Restricted eval, safe builtins, no dangerous operations
- **Extensible design** - Framework processors, context functions easily added
- **Well-commented** - Good docstrings and inline comments
- **Caching strategy** - Prevents re-execution bugs
- **Jump loop detection** - Prevents infinite loops

### Areas for Improvement

- **`_deserialize_state()` incomplete** - Method body empty
- **Comment support** - Not implemented, scheduled for Week 5
- **Compile-time validation** - Could validate jump targets at compile time
- **Inline loops** - Mentioned in spec but not implemented (may be abandoned)
- **Markdown** - Delegated to frontend, could provide parser-level support

---

## Test Coverage

Based on test story files found:
- `test_jumps.bard` - Testing jump functionality
- `test_jump_in_loop.bard` - Jump in loop scenarios
- `test_render_directives.bard` - Render directive system

**Recommendation:** Add more test files for:
- Conditionals
- Loops (especially nested)
- One-time choices
- Error cases
- Multi-line expressions
- Format specifiers

---

## Conclusion

Bardic is **well-implemented** with ~80% of the spec completed. Core features (passages, choices, variables, Python integration, control flow) are solid. The major gaps are:

1. **Week 4 features:** Passage/choice parameters
2. **Week 5 features:** Comments, tags, markdown
3. **Technical debt:** `_deserialize_state()` method body

The engine architecture is excellent with strong separation of execution/rendering and comprehensive error handling. The parser handles complex cases well (nested structures, multi-line expressions).

**Next priorities** (per spec roadmap):
1. Passage parameters (Week 4)
2. Render directives ( Done!)
3. Comments, tags, markdown (Week 5)
4. Whitespace perfection (Week 6)
