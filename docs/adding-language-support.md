# Adding New Language Support to CodeMap

> A comprehensive guide for implementing new language parsers in CodeMap.

## Architecture Overview

CodeMap uses a **configuration-driven tree-sitter architecture** for parsing. Most parsers extend `TreeSitterParser` and use `LanguageConfig` with `NodeMapping` to define how symbols are extracted.

### Core Components

```
codemap/parsers/
├── base.py              # Symbol dataclass + abstract Parser class
├── treesitter_base.py   # TreeSitterParser, LanguageConfig, NodeMapping
├── <language>_parser.py # Language-specific parser
└── __init__.py          # Parser registry
```

### Class Hierarchy

```
Parser (abstract base)
└── TreeSitterParser (config-driven base)
    ├── GoParser
    ├── JavaParser
    ├── SwiftParser
    ├── DartParser
    └── ... (most parsers)
```

---

## Step-by-Step Implementation Guide

### Step 1: Create Feature Branch

Follow the git workflow in `docs/plans/workflow.md`:

```bash
# Create task branch from main or feature branch
git checkout main
git pull origin main
git checkout -b <language>/parser
```

### Step 2: Explore the AST Structure

Before writing code, explore the tree-sitter AST for your language:

```python
from tree_sitter import Parser
from tree_sitter_<language> import language  # or use language-pack

parser = Parser(language())
code = b'''
class Example {
  void method() {}
}
'''
tree = parser.parse(code)

def print_tree(node, indent=0):
    print(f"{'  '*indent}{node.type} [{node.start_point[0]+1}-{node.end_point[0]+1}]")
    for child in node.children:
        if indent < 3:
            print_tree(child, indent + 1)

print_tree(tree.root_node)
```

This helps identify:
- Node types for classes, functions, methods, etc.
- Child node names for identifiers, parameters, bodies
- Comment/docstring node types

### Step 3: Create the Parser File

Create `codemap/parsers/<language>_parser.py`:

```python
"""<Language> parser using tree-sitter with configuration-driven extraction."""

from __future__ import annotations

from .treesitter_base import TreeSitterParser, LanguageConfig, NodeMapping

# Define language configuration
<LANGUAGE>_CONFIG = LanguageConfig(
    name="<language>",
    extensions=[".<ext>"],
    grammar_module="<language>",
    node_mappings={
        # Map tree-sitter node types to symbol extraction config
        "class_declaration": NodeMapping(
            symbol_type="class",
            name_child="identifier",
            body_child="class_body",
        ),
        "function_declaration": NodeMapping(
            symbol_type="function",
            name_child="identifier",
            signature_child="parameters",
        ),
        "method_declaration": NodeMapping(
            symbol_type="method",
            name_child="identifier",
            signature_child="parameters",
        ),
        # Add more mappings as needed...
    },
    comment_types=["comment", "block_comment"],
    doc_comment_prefix="/**",  # or "///" for triple-slash
)


class <Language>Parser(TreeSitterParser):
    """Parser for <Language> files using tree-sitter."""

    config = <LANGUAGE>_CONFIG
    extensions = [".<ext>"]  # REQUIRED: class attribute for get_parser_for_extension()
    language = "<language>"   # REQUIRED: class attribute

    # Override __init__ only if custom grammar loading is needed
    # def __init__(self):
    #     ...

    # Override _extract_symbol only for complex cases
    # def _extract_symbol(self, node, source_bytes):
    #     ...
```

### Step 4: Handle Special Cases

For languages with complex constructs, override specific methods:

```python
def _extract_symbol(self, node, source_bytes):
    """Override for language-specific handling."""
    # Example: Detect if class is actually an interface
    if node.type == "class_declaration":
        if self._is_interface(node):
            # Custom handling
            return Symbol(
                name=name,
                type="interface",
                ...
            )

    # Fall back to default behavior
    return super()._extract_symbol(node, source_bytes)
```

### Step 5: Register the Parser

Update `codemap/parsers/__init__.py`:

```python
# Add import block
try:
    from .<language>_parser import <Language>Parser
    __all__.append("<Language>Parser")
except ImportError:
    <Language>Parser = None

# Add to get_available_parsers()
def get_available_parsers() -> list[type[Parser]]:
    parsers = [...]

    if <Language>Parser:
        parsers.append(<Language>Parser)

    return parsers
```

### Step 6: Wire Up Integration Points

Three files must be updated so the new parser is used during indexing and file discovery:

#### 6a. `codemap/core/indexer.py` — Initialize the parser

Add to `_init_parsers()`:

```python
# <Language> parser (optional, requires tree-sitter)
try:
    from ..parsers.<language>_parser import <Language>Parser
    self._parsers["<language>"] = <Language>Parser()
except ImportError:
    logger.debug("<Language> parser not available (tree-sitter-<language> not installed)")
```

#### 6b. `codemap/utils/config.py` — Add to defaults

Add the language to the `Config.languages` default list:

```python
languages: list[str] = field(default_factory=lambda: [
    ..., "<language>"
])
```

Add the file extension(s) to `DEFAULT_INCLUDE_PATTERNS`:

```python
DEFAULT_INCLUDE_PATTERNS = [
    ...,
    "**/*.<ext>",  # <Language>
]
```

#### 6c. `codemap/utils/file_utils.py` — Add extension mappings

Add to `_get_extensions_for_languages()` `extension_map`:

```python
"<language>": [".<ext>"],
```

Add to `get_language()` `extension_to_lang`:

```python
".<ext>": "<language>",
```

> **Warning:** Skipping these steps means the parser exists but files are silently ignored during indexing. See [issue #16](https://github.com/AZidan/codemap/issues/16).

### Step 7: Create Test Fixture

Create `codemap/tests/fixtures/sample_module.<ext>`:

```
// Include examples of all supported constructs:
// - Classes (regular and special variants)
// - Functions/methods
// - Enums, interfaces, etc.
// - Documentation comments
// - Edge cases
```

### Step 8: Write Tests

Create `codemap/tests/test_<language>_parser.py`:

```python
"""Tests for the <Language> parser."""

import pytest

# Skip if grammar not installed
pytest.importorskip("tree_sitter_<language>")

from codemap.parsers.<language>_parser import <Language>Parser


class Test<Language>Parser:
    """Tests for <Language>Parser class."""

    @pytest.fixture
    def parser(self):
        return <Language>Parser()

    def test_parse_class(self, parser):
        source = '''class Example {}'''
        symbols = parser.parse(source)
        assert len(symbols) == 1
        assert symbols[0].name == "Example"
        assert symbols[0].type == "class"

    def test_parse_function(self, parser):
        ...

    def test_parse_fixture_file(self, parser):
        """Test parsing the fixture file."""
        import os
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "sample_module.<ext>"
        )
        with open(fixture_path, "r") as f:
            source = f.read()
        symbols = parser.parse(source, fixture_path)
        assert len(symbols) >= 3  # Adjust based on fixture

    def test_extensions(self, parser):
        assert ".<ext>" in parser.extensions

    def test_language(self, parser):
        assert parser.language == "<language>"
```

### Step 9: Run Tests

```bash
# Run specific parser tests
pytest codemap/tests/test_<language>_parser.py -v

# Run full test suite
pytest -q
```

### Step 10: Update Documentation

Update `docs/plans/language-support-roadmap.md`:
- Mark language as ✅ Done in the appropriate tier
- Update completion percentages
- Update "Next Actions" section

### Step 11: Commit and Create PR

```bash
# Stage only relevant files
git add codemap/parsers/<language>_parser.py \
        codemap/parsers/__init__.py \
        codemap/tests/fixtures/sample_module.<ext> \
        codemap/tests/test_<language>_parser.py \
        docs/plans/language-support-roadmap.md

# Commit with descriptive message
git commit -m "feat: Add <Language> parser support

- Add <Language>Parser using tree-sitter
- Support <list key features>
- Add comprehensive test suite
- Update language-support-roadmap.md

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# Push and create PR
git push -u origin <language>/parser
gh pr create --base main --title "feat: Add <Language> parser support" --body "..."
```

---

## Configuration Reference

### LanguageConfig Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Language identifier (e.g., "dart", "go") |
| `extensions` | `list[str]` | File extensions (e.g., [".dart"]) |
| `grammar_module` | `str` | tree-sitter module name for dynamic import |
| `node_mappings` | `dict[str, NodeMapping]` | Map of node types to extraction config |
| `export_wrappers` | `list[str]` | Nodes containing exportable children |
| `comment_types` | `list[str]` | Comment node types for docstrings |
| `doc_comment_prefix` | `str` | Doc comment prefix (e.g., "/**", "///") |

### NodeMapping Fields

| Field | Type | Description |
|-------|------|-------------|
| `symbol_type` | `str` | Output type ("class", "function", "method", etc.) |
| `name_child` | `str \| list[str]` | Child node type(s) containing the name |
| `signature_child` | `str \| None` | Child node for parameters/signature |
| `body_child` | `str \| None` | Child node containing children symbols |
| `docstring_extractor` | `str` | How to extract docstring (default: "preceding_comment") |
| `is_async_check` | `Callable` | Function to check if symbol is async |

---

## Special Cases

### Using tree-sitter-language-pack

If no standalone package exists (like Dart):

```python
try:
    from tree_sitter import Parser as TSParser
    from tree_sitter_language_pack import get_language
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

class DartParser(TreeSitterParser):
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(...)
        self._parser = TSParser(get_language("dart"))
```

### Custom Grammar Loading

Some packages have non-standard APIs (like PHP):

```python
def __init__(self):
    from tree_sitter_php import language_php
    self._parser = TSParser(Language(language_php()))
```

### Complex Symbol Detection

For languages where node types are ambiguous:

```python
def _is_interface(node) -> bool:
    """Check if class_declaration is actually an interface."""
    for child in node.children:
        if child.type == "interface":
            return True
    return False
```

---

## Checklist

Before submitting PR:

- [ ] Parser extends `TreeSitterParser` (or `Parser` for custom implementations)
- [ ] `extensions` class attribute defined
- [ ] `language` class attribute defined
- [ ] Parser registered in `__init__.py`
- [ ] Parser initialized in `indexer.py` `_init_parsers()`
- [ ] Language added to `config.py` default languages and include patterns
- [ ] Extension mappings added to `file_utils.py` (`_get_extensions_for_languages` and `get_language`)
- [ ] Test fixture created with representative code
- [ ] Tests cover all major symbol types
- [ ] All tests pass (`pytest -q`)
- [ ] Documentation updated
- [ ] Follows git workflow (feature branch → PR → approval → merge)

---

## Examples

Reference implementations:

| Parser | Complexity | Notes |
|--------|------------|-------|
| `go_parser.py` | Simple | Basic config-driven |
| `kotlin_parser.py` | Medium | Overrides for interface detection |
| `swift_parser.py` | Medium | Multiple body types |
| `dart_parser.py` | Complex | Uses language-pack, custom extraction |
| `php_parser.py` | Medium | Custom grammar loading |
| `typescript_parser.py` | Complex | Export wrappers, arrow functions |

---

*Last updated: January 2026*
