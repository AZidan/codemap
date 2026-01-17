<div align="center">

# 🗺️ CodeMap

**A lightweight index that makes LLM code exploration cheaper — not smarter.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/) [![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

CodeMap does **not** try to understand your code, infer architecture, or decide what's relevant. That job belongs to the LLM.

CodeMap exists for one reason:

> **To make each step of an LLM's reasoning over a codebase cost fewer tokens.**

[Quick Start](#-quick-start) • [How It Works](#how-it-works) • [Commands](#commands) • [Claude Plugin](#-claude-code-plugin) • [Comparison](#comparison-with-alternatives)

![CodeMap Demo](docs/codemap-demo.gif)

</div>

---

## The Problem

LLMs explore codebases iteratively. They:

1. Think about what they need
2. Read some code
3. Think again
4. Read more code
5. Repeat

The problem is that **reading code is expensive**.

Without help, an LLM often has to:
- Read entire files
- Re-read the same files after context resets
- Pull in large chunks "just in case"

This quickly leads to massive token usage—even when the LLM only needed a small part of each file.

---

## The Insight

LLMs don't need *less reasoning*. They need **cheaper reads**.

If you make each "read code" step smaller and more precise, the *same reasoning process* becomes dramatically cheaper.

**The bottleneck is not intelligence — it's I/O cost.**

That's what CodeMap fixes.

---

## What CodeMap Is (and Is Not)

### ✅ What CodeMap **is**

- A **structural index** of your codebase
- A fast way to locate **symbols and their exact line ranges**
- A tool that lets an LLM jump directly to relevant snippets
- A **cost-reduction layer** for iterative LLM reasoning

### ❌ What CodeMap is **not**

- Not a semantic analyzer
- Not an architecture inference engine
- Not a replacement for LSPs
- Not an agent
- Not "smart"

CodeMap does not decide *what* code matters. It only makes it cheaper to *read* the code the LLM decides to look at.

---

## How This Changes LLM Code Exploration

### Without CodeMap

```
LLM thinks
  → reads 5 full files (~30K tokens)
  → thinks
  → reads 3 more full files (~18K tokens)

Total: ~48K tokens
```

### With CodeMap

```
LLM thinks
  → queries symbols → reads 5 targeted snippets (~5K tokens)
  → thinks
  → queries again → reads 3 more snippets (~3K tokens)

Total: ~8K tokens
```

**Same reasoning. Same conclusions. ~83% fewer tokens.**

The LLM can always escalate: snippet → larger slice → full file. CodeMap never blocks access—it just makes precision cheap.

---

## 📊 Measured Impact

The savings compound across a session:

| Scenario | Without CodeMap | With CodeMap | Savings |
|----------|-----------------|--------------|---------|
| Single class lookup | 1,700 tokens | 1,000 tokens | **41%** |
| 10-file refactor | 51,000 tokens | 11,600 tokens | **77%** |
| 50-turn coding session | 70,000 tokens | 21,000 tokens | **70%** |

It's not about any single lookup. It's about making **every** lookup cheaper and letting those savings multiply.

---

## ⚡ Quick Start

```bash
pip install git+https://github.com/AZidan/codemap.git
codemap init .
codemap watch . &   # Keep index updated in background
codemap find "ClassName"
# → src/file.py:15-89 [class] ClassName

# Now the LLM reads only lines 15-89 instead of the entire file
```

---

## How It Works

1. CodeMap scans your repository and builds a **symbol index**
2. Each symbol is mapped to:
   - File path
   - Start line / end line
   - Type (function, class, method, etc.)
   - Signature and docstring (optional)
3. The index is stored locally under `.codemap/`
4. An LLM (or human) can:
   - Search for symbols by name
   - Read only the exact lines needed
   - Check if files changed without re-reading them
   - Repeat as part of its reasoning loop

No embeddings. No inference. No opinions.

---

## Commands

### `codemap init [PATH]`

Build the index for a directory.

```bash
codemap init                     # Index current directory
codemap init ./src               # Index specific directory
codemap init -l python           # Only Python files
codemap init -e "**/tests/**"    # Exclude patterns
```

### `codemap find QUERY`

Find symbols by name (case-insensitive substring match).

```bash
codemap find "UserService"              # Find by name
codemap find "process" --type method    # Filter by type
codemap find "handle" --type function   # Functions only
```

Output:
```
src/services/user.py:15-89 [class] UserService
src/services/user.py:20-45 [method] process_request
```

### `codemap show FILE`

Display file structure with symbols and line ranges.

```bash
codemap show src/services/user.py
```

Output:
```
File: src/services/user.py (hash: a3f2b8c1d4e5)
Lines: 542
Language: python

Symbols:
- UserService [class] L15-189
  (self, config: Config)
  # Handles user operations
  - __init__ [method] L20-35
  - get_user [method] L37-98
    (self, user_id: int) -> User
  - create_user [async_method] L100-145
    (self, data: dict) -> User
```

### `codemap validate [FILE]`

Check if indexed files have changed—**without re-reading them**.

```bash
codemap validate              # Check all files
codemap validate src/main.py  # Check specific file
```

Output:
```
Stale entries (2):
  - src/utils/helpers.py
  - src/models/user.py

Run 'codemap update --all' to refresh
```

This is where hash-based staleness detection saves tokens. The LLM can check if a file changed without paying to read it again.

### `codemap update [FILE] [--all]`

Update the index for changed files.

```bash
codemap update src/main.py    # Update single file
codemap update --all          # Update all stale files
```

### `codemap watch [PATH]`

Watch for file changes and update index in real-time.

```bash
codemap watch                 # Watch current directory
codemap watch ./src           # Watch specific directory
codemap watch -d 1.0          # 1 second debounce
codemap watch -q              # Quiet mode
```

Output:
```
Watching /path/to/project for changes...
Press Ctrl+C to stop

[14:30:15] Updated main.py (2 symbols changed)
[14:30:22] Updated utils.py
[14:31:05] Added new_module.py (3 symbols)
```

### `codemap stats`

Show statistics about the index.

```bash
codemap stats
```

Output:
```
CodeMap Statistics
========================================
Root: /path/to/project
Total files: 47
Total symbols: 382

Files by language:
  python: 35
  typescript: 10
  javascript: 2

Symbols by type:
  method: 245
  function: 67
  class: 42
  async_method: 13
```

### `codemap install-hooks`

Install git pre-commit hook for automatic updates.

```bash
codemap install-hooks
```

---

## 🔌 Claude Code Plugin

The plugin teaches [Claude Code](https://docs.anthropic.com/en/docs/claude-code) to use CodeMap automatically.

### Installation

```bash
# Add the marketplace
claude plugin marketplace add AZidan/codemap

# Install the plugin
claude plugin install codemap
```

### What Changes

Once installed, Claude will:
1. Use `codemap find` to locate symbols instead of scanning files
2. Read only the relevant line ranges instead of full files
3. Use `codemap validate` to check staleness before re-reading
4. Auto-install the CLI if not present

The LLM's reasoning doesn't change—each step just gets cheaper.

### Manual Skill Installation

```bash
# Copy skill to your project
cp -r .claude/skills/codemap /path/to/your/project/.claude/skills/
```

See [plugin/README.md](plugin/README.md) for detailed documentation.

---

## Installation

### Claude Code (Recommended)

```bash
claude plugin marketplace add AZidan/codemap
claude plugin install codemap
```

### pip Install

```bash
# Basic (Python only)
pip install git+https://github.com/AZidan/codemap.git

# With TypeScript/JavaScript support
pip install "codemap[treesitter] @ git+https://github.com/AZidan/codemap.git"

# All languages + watch mode
pip install "codemap[all] @ git+https://github.com/AZidan/codemap.git"
```

### From Source

```bash
git clone https://github.com/azidan/codemap.git
cd codemap
pip install -e ".[all]"
```

---

## Supported Languages

| Language | Parser | Install | Symbol Types |
|----------|--------|---------|--------------|
| **Python** | stdlib `ast` | (included) | class, function, method, async_function, async_method |
| **TypeScript** | tree-sitter | see below | class, function, method, interface, type, enum |
| **JavaScript** | tree-sitter | see below | class, function, method, async_function, async_method |
| **Kotlin** | tree-sitter | see below | class, interface, function, method, object |
| **Swift** | tree-sitter | see below | class, struct, protocol, enum, function, method |
| **Go** | tree-sitter | see below | function, method, struct, interface, type |
| **Java** | tree-sitter | see below | class, interface, enum, method |
| **C#** | tree-sitter | see below | class, interface, struct, enum, method, property |
| **Rust** | tree-sitter | see below | function, struct, enum, trait, impl, module |
| **C** | tree-sitter | see below | function, struct, enum, typedef |
| **C++** | tree-sitter | see below | class, struct, function, method, namespace, enum, template |
| **HTML** | tree-sitter | see below | element (semantic), id |
| **CSS** | tree-sitter | see below | selector (class, id, element), media, keyframe |
| **Markdown** | regex | (included) | section (H2), subsection (H3), subsubsection (H4) |
| **YAML** | pyyaml | (included) | key, section, list |

```bash
# Install with specific language support
pip install "codemap[treesitter] @ git+https://github.com/AZidan/codemap.git"  # TS/JS
pip install "codemap[kotlin] @ git+https://github.com/AZidan/codemap.git"      # Kotlin
pip install "codemap[swift] @ git+https://github.com/AZidan/codemap.git"       # Swift
pip install "codemap[go] @ git+https://github.com/AZidan/codemap.git"          # Go
pip install "codemap[java] @ git+https://github.com/AZidan/codemap.git"        # Java
pip install "codemap[csharp] @ git+https://github.com/AZidan/codemap.git"      # C#
pip install "codemap[rust] @ git+https://github.com/AZidan/codemap.git"        # Rust
pip install "codemap[c] @ git+https://github.com/AZidan/codemap.git"           # C
pip install "codemap[cpp] @ git+https://github.com/AZidan/codemap.git"         # C++
pip install "codemap[html] @ git+https://github.com/AZidan/codemap.git"        # HTML
pip install "codemap[css] @ git+https://github.com/AZidan/codemap.git"         # CSS

# Install all languages
pip install "codemap[languages] @ git+https://github.com/AZidan/codemap.git"
```

Language support is intentionally modular and extensible.

---

## Configuration

Create a `.codemaprc` file in your project root:

```yaml
# Languages to index
languages:
  - python
  - typescript
  - javascript

# Patterns to exclude
exclude:
  - "**/node_modules/**"
  - "**/__pycache__/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/.venv/**"
  - "**/migrations/**"

# Patterns to include (optional)
include:
  - "src/**"
  - "lib/**"

# Truncate long docstrings
max_docstring_length: 150

# Output directory (default: .codemap)
output: .codemap
```

---

## Output Format

### Directory Structure

CodeMap uses distributed per-directory indexes for scalability:

```
project/
├── .codemap/
│   ├── .codemap.json           # Root manifest
│   ├── _root.codemap.json      # Files in project root
│   ├── src/
│   │   ├── .codemap.json       # Files in src/
│   │   └── components/
│   │       └── .codemap.json   # Files in src/components/
│   └── tests/
│       └── .codemap.json
├── src/
│   └── ...
└── tests/
    └── ...
```

### Index Format

Each `.codemap.json` contains:

```json
{
  "version": "1.0",
  "generated_at": "2025-01-12T10:30:00Z",
  "directory": "src",
  "files": {
    "main.py": {
      "hash": "a3f2b8c1d4e5",
      "indexed_at": "2025-01-12T10:30:00Z",
      "language": "python",
      "lines": 150,
      "symbols": [
        {
          "name": "UserService",
          "type": "class",
          "lines": [10, 150],
          "docstring": "Handles user operations",
          "children": [
            {
              "name": "get_user",
              "type": "method",
              "lines": [25, 50],
              "signature": "(self, user_id: int) -> User"
            }
          ]
        }
      ]
    }
  }
}
```

---

## When CodeMap Is a Good Fit

- **Large repositories** where context limits matter
- **Long coding sessions** where savings compound
- **Refactoring tasks** that touch many files
- **Token-sensitive workflows** where API costs matter
- **200K context models** where every token counts

## When CodeMap Is Not the Right Tool

- **Small projects** that fit entirely in context anyway
- **Deep semantic analysis** — use LSP tools instead
- **Architecture inference** — CodeMap doesn't infer anything
- **1M token contexts** where limits rarely matter

CodeMap is deliberately simple.

---

## Comparison with Alternatives

| Feature | CodeMap | Aider RepoMap | Serena | RepoPrompt |
|---------|---------|---------------|--------|------------|
| **Approach** | Lookup index | Summarization | Semantic (LSP) | Context building |
| **Who decides relevance** | LLM | Tool (PageRank) | Tool | Tool |
| **Token cost model** | Per-lookup | Upfront | Per-query | Upfront |
| **Line-range precision** | ✅ Exact | ❌ Approximate | ❌ Full symbols | ❌ Full files |
| **Hash-based staleness** | ✅ | ❌ | ❌ | ❌ |
| **Watch mode** | ✅ | ❌ | ❌ | ❌ |
| **Setup complexity** | Low | Medium | High | Low |

The key difference: other tools try to predict what context matters. CodeMap lets the LLM decide, and just makes each decision cheaper to act on.

---

## Design Philosophy

> **Do one thing. Do it well. Stay dumb.**

CodeMap is intentionally:
- **Deterministic** — same query, same results
- **Transparent** — just file paths and line numbers
- **Predictable** — no inference, no surprises

It is a primitive—not a framework.

---

## Development

```bash
# Clone the repo
git clone https://github.com/azidan/codemap.git
cd codemap

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[all]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=codemap

# Format code
black codemap
ruff check codemap
```

### Project Structure

```
codemap/
├── cli.py                 # Click CLI commands
├── core/
│   ├── indexer.py         # Main indexing orchestrator
│   ├── hasher.py          # SHA256 file hashing
│   ├── map_store.py       # Distributed JSON storage
│   └── watcher.py         # File system watcher
├── parsers/
│   ├── base.py            # Abstract parser interface
│   ├── treesitter_base.py # Base for tree-sitter parsers
│   ├── python_parser.py   # Python AST parser (stdlib)
│   ├── typescript_parser.py
│   ├── javascript_parser.py
│   ├── kotlin_parser.py   # Kotlin tree-sitter parser
│   ├── swift_parser.py    # Swift tree-sitter parser
│   ├── go_parser.py
│   ├── java_parser.py
│   ├── csharp_parser.py
│   ├── rust_parser.py
│   ├── c_parser.py        # C tree-sitter parser
│   ├── cpp_parser.py      # C++ tree-sitter parser
│   ├── html_parser.py     # HTML tree-sitter parser
│   ├── css_parser.py      # CSS tree-sitter parser
│   ├── markdown_parser.py # Markdown regex parser
│   └── yaml_parser.py     # YAML parser
├── hooks/
│   └── installer.py       # Git hook installation
└── utils/
    ├── config.py          # Configuration management
    └── file_utils.py      # File discovery utilities
```

---

## 🤝 Contributing

Contributions welcome! Areas where help is needed:

- **New language parsers** — Ruby, PHP, Scala
- **MCP server mode** — For non-Claude tools
- **Fuzzy symbol search** — `codemap find "usr srv"` → `UserService`
- **VSCode extension** — GUI for non-CLI users

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
---

## 💬 Community & Support

- 🐛 **Bug reports:** [GitHub Issues](https://github.com/azidan/codemap/issues)
- 💡 **Feature requests:** [GitHub Issues](https://github.com/azidan/codemap/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/azidan/codemap/discussions)
- ⭐ **Like it?** Star the repo!

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Inspired by [Aider's RepoMap](https://aider.chat/docs/repomap.html) concept
- Built with [Click](https://click.palletsprojects.com/) for CLI
- Uses [tree-sitter](https://tree-sitter.github.io/) for multi-language parsing

---

<div align="center">

**CodeMap: Because the bottleneck is I/O cost, not intelligence.**

[⬆ Back to top](#-codemap)

</div>
