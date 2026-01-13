# Contributing to CodeMap

First off, thank you for considering contributing to CodeMap! 🎉

This document provides guidelines and instructions for contributing. Following these guidelines helps communicate that you respect the time of the developers managing this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Adding a New Language Parser](#adding-a-new-language-parser)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Help Wanted](#help-wanted)

---

## Code of Conduct

This project follows a simple code of conduct:

- **Be respectful** — Treat everyone with respect and kindness
- **Be constructive** — Provide helpful feedback, not criticism
- **Be patient** — Maintainers review PRs in their spare time
- **Be inclusive** — Welcome newcomers and help them get started

---

## How Can I Contribute?

### Reporting Bugs

Before creating a bug report, please check [existing issues](https://github.com/azidan/codemap/issues) to avoid duplicates.

When creating a bug report, include:

```markdown
**Environment:**
- OS: [e.g., macOS 14.0, Ubuntu 22.04, Windows 11]
- Python version: [e.g., 3.11.5]
- CodeMap version: [e.g., 1.0.0]

**Describe the bug:**
A clear description of what the bug is.

**To reproduce:**
1. Run `codemap init ...`
2. Then run `codemap find ...`
3. See error

**Expected behavior:**
What you expected to happen.

**Actual behavior:**
What actually happened.

**Error output:**
```
Paste any error messages here
```

**Additional context:**
Any other relevant information.
```

### Suggesting Features

Feature requests are welcome! Please include:

- **Use case** — Why do you need this feature?
- **Proposed solution** — How do you envision it working?
- **Alternatives considered** — Other ways to solve the problem
- **Additional context** — Screenshots, mockups, examples

### Contributing Code

1. Check [open issues](https://github.com/azidan/codemap/issues) for something to work on
2. Comment on the issue to let others know you're working on it
3. Fork the repository
4. Create a feature branch
5. Make your changes
6. Submit a pull request

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- (Optional) tree-sitter for TypeScript/JavaScript support

### Setup Steps

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/codemap.git
cd codemap

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install in development mode with all dependencies
pip install -e ".[all]"

# 4. Verify installation
codemap --version
pytest
```

### Running the CLI Locally

```bash
# Run from source
python -m codemap.cli --help

# Or use the installed command
codemap --help
```

---

## Project Structure

```
codemap/
├── cli.py                    # CLI entry point (Click commands)
├── core/
│   ├── __init__.py
│   ├── indexer.py            # Main indexing orchestrator
│   ├── hasher.py             # SHA256 file hashing
│   ├── map_store.py          # JSON storage (distributed indexes)
│   └── watcher.py            # File system watcher
├── parsers/
│   ├── __init__.py
│   ├── base.py               # Abstract Parser class
│   ├── python_parser.py      # Python AST parser
│   ├── typescript_parser.py  # TypeScript tree-sitter parser
│   └── javascript_parser.py  # JavaScript tree-sitter parser
├── hooks/
│   ├── __init__.py
│   └── installer.py          # Git hook installation
├── utils/
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   └── file_utils.py         # File discovery utilities
└── tests/
    ├── __init__.py
    ├── test_indexer.py
    ├── test_parsers.py
    ├── test_cli.py
    └── fixtures/             # Sample files for testing
```

### Key Files

| File | Purpose |
|------|---------|
| `cli.py` | All CLI commands (init, find, show, etc.) |
| `core/indexer.py` | Orchestrates file discovery and parsing |
| `core/map_store.py` | Reads/writes `.codemap/` JSON files |
| `parsers/base.py` | `Parser` abstract class and `Symbol` dataclass |

---

## Adding a New Language Parser

This is one of the most valuable contributions! Here's how to add support for a new language.

### Step 1: Create the Parser File

Create `codemap/parsers/{language}_parser.py`:

```python
"""Parser for {Language} files."""

from typing import List
from .base import Parser, Symbol


class {Language}Parser(Parser):
    """{Language} parser using {method}."""
    
    # File extensions this parser handles
    extensions = [".ext1", ".ext2"]
    
    def parse(self, source: str) -> List[Symbol]:
        """Parse {Language} source and extract symbols.
        
        Args:
            source: Source code as string
            
        Returns:
            List of top-level symbols
        """
        symbols = []
        
        # Your parsing logic here
        # Extract classes, functions, methods, etc.
        
        return symbols
```

### Step 2: Implement Symbol Extraction

The `Symbol` dataclass (from `base.py`):

```python
@dataclass
class Symbol:
    name: str                           # Symbol name (e.g., "UserService")
    type: str                           # One of: class, function, method, 
                                        #         async_function, async_method,
                                        #         interface, type, enum
    lines: tuple[int, int]              # (start_line, end_line), 1-indexed
    signature: Optional[str] = None     # Function signature
    docstring: Optional[str] = None     # First 150 chars of docstring
    children: List["Symbol"] = None     # Nested symbols (methods in class)
```

### Step 3: Choose a Parsing Strategy

**Option A: AST-based (preferred for languages with Python bindings)**

```python
# Example: Using a hypothetical Go AST library
import go_ast

class GoParser(Parser):
    extensions = [".go"]
    
    def parse(self, source: str) -> List[Symbol]:
        tree = go_ast.parse(source)
        return self._extract_symbols(tree)
    
    def _extract_symbols(self, tree) -> List[Symbol]:
        symbols = []
        for node in tree.declarations:
            if node.type == "function":
                symbols.append(Symbol(
                    name=node.name,
                    type="function",
                    lines=(node.start_line, node.end_line),
                    signature=self._get_signature(node),
                ))
        return symbols
```

**Option B: Tree-sitter (recommended for most languages)**

```python
# Example: Rust parser using tree-sitter
try:
    import tree_sitter_rust as ts_rust
    from tree_sitter import Language, Parser as TSParser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

class RustParser(Parser):
    extensions = [".rs"]
    
    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter-rust required. "
                "Install with: pip install tree-sitter tree-sitter-rust"
            )
        self._parser = TSParser(Language(ts_rust.language()))
    
    def parse(self, source: str) -> List[Symbol]:
        tree = self._parser.parse(bytes(source, "utf-8"))
        return self._extract_symbols(tree.root_node, source)
    
    def _extract_symbols(self, node, source) -> List[Symbol]:
        symbols = []
        for child in node.children:
            if child.type == "function_item":
                symbols.append(self._parse_function(child, source))
            elif child.type == "struct_item":
                symbols.append(self._parse_struct(child, source))
            elif child.type == "impl_item":
                symbols.extend(self._parse_impl(child, source))
        return symbols
```

**Option C: Regex-based (fallback, not recommended)**

Only use if no AST/tree-sitter option exists. Regex parsing is fragile.

### Step 4: Register the Parser

Edit `codemap/parsers/__init__.py`:

```python
from .base import Parser, Symbol
from .python_parser import PythonParser
from .typescript_parser import TypeScriptParser
from .javascript_parser import JavaScriptParser
from .{language}_parser import {Language}Parser  # Add this

__all__ = [
    "Parser", 
    "Symbol", 
    "PythonParser", 
    "TypeScriptParser",
    "JavaScriptParser",
    "{Language}Parser",  # Add this
]
```

Edit `codemap/core/indexer.py` to include the new parser:

```python
def _init_parsers(self) -> dict[str, Parser]:
    parsers = {}
    
    if "python" in self.languages:
        parsers["python"] = PythonParser()
    
    # Add your language
    if "{language}" in self.languages:
        try:
            from ..parsers.{language}_parser import {Language}Parser
            parsers["{language}"] = {Language}Parser()
        except ImportError:
            pass  # Optional dependency not installed
    
    return parsers
```

### Step 5: Add Tests

Create `tests/test_{language}_parser.py`:

```python
import pytest
from codemap.parsers.{language}_parser import {Language}Parser


@pytest.fixture
def parser():
    return {Language}Parser()


class Test{Language}Parser:
    
    def test_parse_function(self, parser):
        source = '''
        // Your language's function syntax
        func hello(name string) string {
            return "Hello, " + name
        }
        '''
        symbols = parser.parse(source)
        
        assert len(symbols) == 1
        assert symbols[0].name == "hello"
        assert symbols[0].type == "function"
        assert symbols[0].lines[0] > 0  # Valid line number
    
    def test_parse_class_or_struct(self, parser):
        # Test class/struct/type parsing
        pass
    
    def test_parse_empty_file(self, parser):
        symbols = parser.parse("")
        assert symbols == []
    
    def test_parse_syntax_error(self, parser):
        # Should not raise, return empty or partial results
        symbols = parser.parse("invalid {{{ syntax")
        assert isinstance(symbols, list)
```

Add test fixtures in `tests/fixtures/sample.{ext}`.

### Step 6: Update Documentation

1. Add language to the table in `README.md`
2. Add installation instructions if extra dependencies needed
3. Update `pyproject.toml` with optional dependencies

### Parser Checklist

- [ ] Parser class inherits from `Parser`
- [ ] `extensions` attribute lists all file extensions
- [ ] `parse()` returns `List[Symbol]`
- [ ] Line numbers are 1-indexed
- [ ] Handles empty files (returns `[]`)
- [ ] Handles syntax errors gracefully (no exceptions)
- [ ] Extracts: classes, functions, methods at minimum
- [ ] Nested symbols use `children` attribute
- [ ] Signatures are truncated to 100 chars
- [ ] Docstrings are truncated to 150 chars
- [ ] Unit tests cover basic cases
- [ ] Documented in README

---

## Code Style

### Python Style

We use **Black** for formatting and **Ruff** for linting.

```bash
# Format code
black codemap

# Check linting
ruff check codemap

# Fix auto-fixable issues
ruff check --fix codemap
```

### Guidelines

- **Type hints** — Use them everywhere
- **Docstrings** — Google style for public functions
- **Line length** — 100 characters max (Black default)
- **Imports** — Use absolute imports, sorted by isort

```python
# Good
from codemap.parsers.base import Parser, Symbol

def get_user(user_id: int) -> Optional[User]:
    """Fetch a user by ID.
    
    Args:
        user_id: The user's unique identifier.
        
    Returns:
        User object if found, None otherwise.
    """
    pass
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=codemap

# Run specific test file
pytest tests/test_python_parser.py

# Run specific test
pytest tests/test_python_parser.py::TestPythonParser::test_parse_class

# Verbose output
pytest -v
```

### Writing Tests

- Place tests in `tests/` directory
- Name files `test_*.py`
- Use pytest fixtures for common setup
- Test both success and failure cases
- Add fixtures to `tests/fixtures/` for sample files

### Test Coverage Goals

- **Parsers:** 90%+ coverage
- **Core:** 80%+ coverage
- **CLI:** 70%+ coverage (integration tests)

---

## Pull Request Process

### Before Submitting

1. ✅ Code is formatted (`black codemap`)
2. ✅ Linting passes (`ruff check codemap`)
3. ✅ All tests pass (`pytest`)
4. ✅ New code has tests
5. ✅ Documentation updated if needed

### PR Title Format

```
type: short description

Examples:
feat: add Go language parser
fix: handle empty files in Python parser
docs: update installation instructions
test: add edge case tests for indexer
refactor: simplify map_store logic
```

### PR Description Template

```markdown
## What

Brief description of changes.

## Why

Why is this change needed?

## How

How does this change address the issue?

## Testing

How was this tested?

## Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted with Black
- [ ] Linting passes
```

### Review Process

1. Submit PR against `main` branch
2. CI runs tests automatically
3. Maintainer reviews code
4. Address feedback if any
5. Maintainer merges when approved

---

## Help Wanted

Looking for something to work on? Here are high-impact areas:

### 🟢 Good First Issues

- Add more test cases for existing parsers
- Improve error messages
- Documentation improvements
- Add examples to README

### 🟡 Medium Difficulty

- **New language parsers:**
  - [ ] Go
  - [ ] Rust  
  - [ ] Java
  - [ ] C#
  - [ ] Ruby
  - [ ] PHP
- **CLI improvements:**
  - [ ] JSON output format (`--json` flag)
  - [ ] Fuzzy symbol search
  - [ ] Better progress indicators

### 🔴 Advanced

- **MCP server mode** — Expose CodeMap as Model Context Protocol server
- **VSCode extension** — GUI for non-CLI users
- **Performance optimization** — Parallel indexing for large repos
- **Incremental updates** — Only re-parse changed portions of files

---

## Questions?

- 💬 Open a [GitHub Discussion](https://github.com/azidan/codemap/discussions)
- 🐛 File an [Issue](https://github.com/azidan/codemap/issues)

Thank you for contributing! 🙏