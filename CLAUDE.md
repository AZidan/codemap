# CLAUDE.md - Agent Instructions for CodeMap

## Project Context

You are building **CodeMap**, a CLI tool that generates structural indexes of codebases to reduce LLM token consumption. The tool creates a `.codemap/` directory that mirrors the project structure, enabling targeted line-range reads instead of full file reads.

## Quick Start Commands

```bash
# Setup
cd codemap
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Run CLI
codemap --help
codemap init .
codemap find "ClassName"
```

## Using CodeMap to Navigate This Codebase

This project has a `.codemap/` index. **Use CodeMap before scanning files.**

### Start Watch Mode First
```bash
codemap watch . &
```
This keeps the index automatically updated as files change. Run once at the start of each session.

### Commands
```bash
codemap find "SymbolName"           # Find class/function/method/type by name
codemap find "name" --type method   # Filter by type (class|function|method|interface|type)
codemap show path/to/file.py        # Show file structure with line ranges
codemap validate                    # Check if index is fresh
codemap stats                       # View index statistics
codemap watch . &                   # Start watch mode (auto-updates index)
```

### Workflow
1. **Start watch mode**: `codemap watch . &` (run once per session)
2. **Find symbol**: `codemap find "MapStore"` → `codemap/core/map_store.py:115-507 [class]`
3. **Read targeted lines**: Read only lines 115-507 instead of the full file
4. **Explore structure**: `codemap show codemap/core/map_store.py` to see all methods with line ranges

### When to Use
- **USE CodeMap**: Finding symbol definitions, understanding file structure, locating code by name
- **READ full file**: Understanding implementation details, making edits, unindexed files

### Direct JSON Access
Symbol data is in `.codemap/<path>/.codemap.json` files - read directly for programmatic access.

## Architecture Overview

```
codemap/
├── cli.py                    # Click CLI - entry point
├── core/
│   ├── indexer.py            # Orchestrates indexing
│   ├── hasher.py             # SHA256 file hashing
│   └── map_store.py          # JSON map CRUD operations
├── parsers/
│   ├── base.py               # Abstract Parser class
│   ├── treesitter_base.py    # Config-driven tree-sitter base
│   ├── python_parser.py      # AST-based (stdlib only)
│   ├── typescript_parser.py  # tree-sitter based
│   ├── javascript_parser.py  # tree-sitter based
│   ├── kotlin_parser.py      # tree-sitter based
│   ├── swift_parser.py       # tree-sitter based
│   ├── go_parser.py          # tree-sitter based
│   ├── java_parser.py        # tree-sitter based
│   ├── csharp_parser.py      # tree-sitter based
│   ├── rust_parser.py        # tree-sitter based
│   ├── c_parser.py           # tree-sitter based
│   ├── cpp_parser.py         # tree-sitter based
│   ├── html_parser.py        # tree-sitter based
│   ├── css_parser.py         # tree-sitter based
│   ├── markdown_parser.py    # Regex-based H2/H3/H4 headers
│   └── yaml_parser.py        # Recursive key hierarchy
├── hooks/
│   ├── pre-commit            # Bash script
│   └── installer.py          # Copies hook to .git/hooks/
└── tests/
```

## Implementation Order

Build in this sequence:

### Phase 1: Core Foundation
1. `core/hasher.py` - Simple, no dependencies
2. `parsers/base.py` - Abstract interface
3. `parsers/python_parser.py` - Use stdlib `ast` module only
4. `core/map_store.py` - JSON read/write
5. `core/indexer.py` - Ties everything together

### Phase 2: CLI
6. `cli.py` - Implement commands: init, update, find, show, validate

### Phase 3: Additional Parsers
7. `parsers/typescript_parser.py` - tree-sitter
8. `parsers/javascript_parser.py` - tree-sitter

> **Adding New Language Support**: See `docs/adding-language-support.md` for the complete guide on implementing new language parsers, including architecture patterns, git workflow, and testing requirements.

### Phase 4: Git Integration
9. `hooks/pre-commit` - Bash script
10. `hooks/installer.py` - Copy hook to .git/hooks/

### Phase 5: Tests
11. Unit tests for parsers
12. Integration tests for indexer
13. CLI tests

## Key Design Decisions

### 1. Symbol Extraction
Extract only these symbol types:
- **Python**: `class`, `function`, `method`, `async_function`, `async_method`
- **TypeScript/JS**: `class`, `function`, `method`, `arrow_function` (named only)
- **Kotlin**: `class`, `interface`, `function`, `method`, `object`
- **Swift**: `class`, `struct`, `protocol`, `enum`, `function`, `method`
- **Go**: `function`, `method`, `struct`, `interface`, `type`
- **Java**: `class`, `interface`, `enum`, `method`
- **C#**: `class`, `interface`, `struct`, `enum`, `method`, `property`
- **Rust**: `function`, `struct`, `enum`, `trait`, `impl`, `module`
- **C**: `function`, `struct`, `enum`, `typedef`
- **C++**: `class`, `struct`, `function`, `method`, `namespace`, `enum`, `template`
- **PHP**: `class`, `interface`, `trait`, `enum`, `function`, `method`
- **Dart**: `class`, `enum`, `mixin`, `extension`, `function`, `method`, `constructor`, `getter`, `setter`
- **HTML**: `element` (semantic: header, nav, main, section, article, aside, footer, form), `id` (elements with id attribute)
- **CSS**: `class` (.selector), `id` (#selector), `selector` (element), `pseudo` (:root), `media` (@media), `keyframe` (@keyframes)
- **Markdown**: `section` (H2), `subsection` (H3), `subsubsection` (H4)
- **YAML**: `key`, `section` (nested mappings), `list`, `item`
- **SQL**: `table`, `view`, `materialized_view`, `index`, `function`, `trigger`, `type`, `sequence`, `schema`, `database`, `column`

Skip:
- Variables/constants (too noisy)
- Imports (not useful for navigation)
- Decorators (include in parent symbol's line range)

### 2. Line Numbers
- Always 1-indexed (matches editor conventions)
- Include decorators in the start line
- End line is the actual last line of the symbol

### 3. Signatures
- Include parameter names and type annotations
- Include return type if present
- Truncate if longer than 100 chars

### 4. Docstrings
- First 150 chars only
- Strip leading/trailing whitespace
- null if no docstring

### 5. Error Handling
- If a file fails to parse, log warning and skip
- Never crash on malformed code
- Store partial results (valid files only)

### 6. Hash Strategy
- SHA256, truncated to 12 hex chars
- Hash the raw bytes, not decoded text
- Used to detect changes without re-reading content

## Code Style

- Use type hints everywhere
- Dataclasses for data structures
- No global state
- Functions should be small (<30 lines)
- Use pathlib.Path, not os.path

## Testing Requirements

- Every parser needs tests with fixture files
- Test edge cases: empty files, syntax errors, unicode
- Integration test: index → modify file → validate detects change

## Common Pitfalls to Avoid

1. **Don't include node_modules/venv in default scan** - Use exclude patterns
2. **Handle encoding errors** - Some files may not be UTF-8
3. **Don't crash on binary files** - Skip gracefully
4. **Watch for circular imports** - Keep module dependencies clean
5. **Tree-sitter returns bytes** - Decode positions correctly

## File Patterns

Default include:
```
**/*.py
**/*.ts
**/*.tsx
**/*.js
**/*.jsx
**/*.kt
**/*.kts
**/*.swift
**/*.go
**/*.java
**/*.cs
**/*.rs
**/*.c
**/*.h
**/*.cpp
**/*.hpp
**/*.cc
**/*.hh
**/*.cxx
**/*.hxx
**/*.html
**/*.htm
**/*.css
**/*.md
**/*.yaml
**/*.yml
**/*.sql
```

Default exclude:
```
**/node_modules/**
**/__pycache__/**
**/venv/**
**/.venv/**
**/dist/**
**/build/**
**/*.min.js
**/migrations/**
```

## Example Usage Flow

```bash
# User initializes
$ codemap init ./src
Scanning ./src...
Found 47 files
Indexed 382 symbols
Saved to ./src/.codemap/

# User queries
$ codemap find "PaymentProcessor"
src/payments/processor.py:15-189 [class] PaymentProcessor
  └── process_payment:37-98 [method]
  └── validate_card:100-145 [method]

# User updates single file after edit
$ codemap update src/payments/processor.py
Updated src/payments/processor.py (3 symbols changed)

# User validates freshness
$ codemap validate
Stale entries (2):
  - src/utils/helpers.py
  - src/models/user.py
Run 'codemap update --all' to refresh
```

## Output Format Guidelines

### Directory Structure (.codemap/)
```
.codemap/
├── .codemap.json              # Root manifest (stats, config, directory list)
├── _root.codemap.json         # Files in project root
├── src/
│   ├── .codemap.json          # Files in src/
│   └── components/
│       └── .codemap.json      # Files in src/components/
```

### JSON Output
- Pretty printed with 2-space indent
- Sorted keys for stable diffs
- ISO 8601 timestamps

### CLI Output
- Use colors sparingly (click.style)
- Show progress for long operations
- Exit code 0 on success, 1 on error

## Dependencies

```
# Required
click>=8.0        # CLI framework
pyyaml>=6.0       # Config file parsing

# For TypeScript/JavaScript parsing
tree-sitter>=0.21
tree-sitter-javascript>=0.21
tree-sitter-typescript>=0.21

# For Kotlin/Swift parsing
tree-sitter-kotlin>=1.0
tree-sitter-swift>=0.0.1

# For other languages
tree-sitter-go>=0.21
tree-sitter-java>=0.21
tree-sitter-c-sharp>=0.21
tree-sitter-rust>=0.21
tree-sitter-c>=0.21
tree-sitter-cpp>=0.21

# For HTML/CSS parsing
tree-sitter-html>=0.23
tree-sitter-css>=0.23

# For SQL parsing
tree-sitter-sql>=0.3

# Dev
pytest>=7.0
```

## When Stuck

1. Check PROJECT_SPEC.md for detailed data structures
2. Python parser should use ONLY stdlib `ast` module
3. For tree-sitter issues, check their Python bindings docs
4. Test with real-world files from open source projects

## CodeMap - Codebase Index

This project has a `.codemap/` index for efficient code navigation. **Use CodeMap before scanning files.**

### Start Watch Mode First
```bash
codemap watch . &
```
This keeps the index automatically updated as files change. Run once at the start of each session.

### Commands
```bash
codemap find "SymbolName"           # Find class/function/method/type by name
codemap find "name" --type method   # Filter by type (class|function|method|interface|enum|struct)
codemap show path/to/file.py        # Show file structure with line ranges
codemap validate                    # Check if index is fresh
codemap stats                       # View index statistics
codemap watch . &                   # Start watch mode (auto-updates index)
```

### Supported Languages
Python, TypeScript, JavaScript, Kotlin, Swift, Go, Java, C#, Rust, C, C++, PHP, Dart, SQL, HTML, CSS, Markdown, YAML

### Workflow
1. **Start watch mode**: `codemap watch . &` (run once per session)
2. **Find symbol**: `codemap find "UserService"` → `src/services/user.ts:15-89 [class]`
3. **Read targeted lines**: Read only lines 15-89 instead of the full file
4. **Explore structure**: `codemap show src/services/user.ts` to see all methods/functions with line ranges

### When to Use
- **USE CodeMap**: Finding symbol definitions, understanding file structure, locating code by name
- **READ full file**: Understanding implementation details, making edits, unindexed files

### Direct JSON Access
Symbol data is in `.codemap/<path>/.codemap.json` files - read directly for programmatic access.
