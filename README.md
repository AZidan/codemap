<div align="center">

# 🗺️ CodeMap

**Cut your LLM token costs by 41-80% when coding with AI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet)](https://docs.anthropic.com/en/docs/claude-code)

Stop burning tokens on full-file reads. CodeMap creates a lightweight navigation index so LLMs read only the code they need.

[Quick Start](#-tldr) • [Installation](#installation) • [Commands](#commands) • [Claude Plugin](#-claude-code-plugin) • [Comparison](#comparison-with-alternatives)

![CodeMap Demo](docs/codemap-demo.gif)

</div>

---

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│  WITHOUT CodeMap                  WITH CodeMap                 │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  LLM: "Edit UserService"          LLM: "Edit UserService"      │
│        ↓                                ↓                      │
│  Read user.py (500 lines)         codemap find "UserService"   │
│  = 6,000 tokens                         ↓                      │
│                                   → user.py:15-89              │
│                                         ↓                      │
│                                   Read lines 15-89 only        │
│                                   = 1,000 tokens               │
│                                                                │
│  ❌ Token cost: 6,000             ✅ Token cost: 1,000 (-83%)  │
└────────────────────────────────────────────────────────────────┘
```

CodeMap creates a `.codemap/` index containing:
- **Symbol locations** → exact line ranges for every class, function, method
- **File hashes** → detect changes without re-reading content  
- **Hierarchical structure** → navigate nested symbols efficiently

---

## ⚡ TL;DR

```bash
pip install git+https://github.com/AZidan/codemap.git
codemap init .
codemap watch . &   # Keep index auto-updated in background
codemap find "ClassName"
# → src/file.py:15-89 [class] ClassName

# Now read only lines 15-89 instead of the entire file
```

**That's it.** You just saved 60-80% of tokens.

---

## 📊 Real-World Results

| Scenario | Without CodeMap | With CodeMap | Savings |
|----------|-----------------|--------------|---------|
| Find & edit a class | 1,700 tokens | 1,000 tokens | **41%** |
| Navigate 10-file refactor | 51,000 tokens | 11,600 tokens | **77%** |
| Long coding session (50 turns) | 70,000 tokens | 21,000 tokens | **70%** |

*Tested against Serena (LSP-based tool) on equivalent tasks*

---

## Installation

### Recommended (Most Users)

```bash
pip install git+https://github.com/AZidan/codemap.git
```

### With TypeScript/JavaScript Support

```bash
pip install "codemap[treesitter] @ git+https://github.com/AZidan/codemap.git"
```

### Full Installation (Watch Mode + All Languages)

```bash
pip install "codemap[all] @ git+https://github.com/AZidan/codemap.git"
```

### From Source

```bash
git clone https://github.com/azidan/codemap.git
cd codemap
pip install -e ".[all]"
```

> **💡 Claude Code Users:** Skip manual install — use the plugin instead:
> ```bash
> claude plugin marketplace add AZidan/codemap
> claude plugin install codemap
> ```

---

## Quick Start

### 1. Index Your Codebase

```bash
codemap init ./src
```

Output:
```
Scanning ./src...
Indexed 47 files, 382 symbols
Saved to .codemap/
```

### 2. Start Watch Mode (Recommended)

Keep the index automatically updated as you work:

```bash
codemap watch . &
```

This runs in the background and updates the index whenever files change.

### 3. Find Symbols

```bash
codemap find "PaymentProcessor"
```

Output:
```
src/payments/processor.py:15-189 [class] PaymentProcessor
  └── process_payment [method] L26-58
  └── validate_card [method] L60-88
```

### 4. Read Only What You Need

Instead of reading the entire 500-line file, read just lines 15-189:

```python
# LLM reads only the relevant section
view("src/payments/processor.py", line_range=[15, 189])
```

No need to manually update - watch mode keeps the index fresh.

---

## When to Use CodeMap

### ✅ Use CodeMap when:

- Working with codebases **> 10 files**
- Frequently **hitting token limits** with AI assistants
- Using **Claude Code, Cursor, Aider**, or similar tools
- Doing **refactoring across multiple files**
- Your team wants to **reduce API costs**

### ❌ Skip CodeMap when:

- Working with **single-file scripts**
- Your **entire codebase fits in context** anyway
- You need **full semantic analysis** (use Serena/LSP instead)

---

## Commands

### `codemap init [PATH]`

Index a directory and create the `.codemap/` structure.

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

Display file structure with symbols, line ranges, and signatures.

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

Check if indexed files have changed.

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

CodeMap includes a plugin for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that enables automatic codebase navigation.

### Installation

```bash
# Add the marketplace
claude plugin marketplace add AZidan/codemap

# Install the plugin
claude plugin install codemap
```

### What It Does

Once installed, Claude will automatically:

1. ✅ Use `codemap find` to locate symbols instead of scanning files
2. ✅ Read only relevant line ranges instead of full files
3. ✅ Validate freshness before re-reading after context resets
4. ✅ Auto-install the CLI if not present

### Manual Skill Installation

```bash
# Copy skill to your project
cp -r .claude/skills/codemap /path/to/your/project/.claude/skills/
```

See [plugin/README.md](plugin/README.md) for detailed documentation.

---

## Comparison with Alternatives

| Feature | CodeMap | Aider RepoMap | Serena | RepoPrompt |
|---------|:-------:|:-------------:|:------:|:----------:|
| **Token efficiency** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Line-range navigation** | ✅ | ❌ | ❌ | ❌ |
| **Hash-based staleness** | ✅ | ❌ | ❌ | ❌ |
| **Watch mode** | ✅ | ❌ | ❌ | ❌ |
| **Claude Code plugin** | ✅ | ❌ | ✅ (MCP) | ✅ (MCP) |
| **Setup complexity** | Low | Medium | High (LSP) | Low |
| **Languages supported** | 9 | 20+ | 10+ | Many |
| **Approach** | Navigation | Summarization | Semantic | Context building |

### Why CodeMap is Different

Most tools focus on **summarization** — condensing code into smaller representations.

CodeMap focuses on **navigation** — telling the LLM exactly **where to look**.

This is why CodeMap achieves 41% better token efficiency than LSP-based tools on navigation tasks. You don't need full semantic analysis to find and edit code.

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

```bash
# Install with specific language support
pip install "codemap[treesitter] @ git+https://github.com/AZidan/codemap.git"  # TS/JS
pip install "codemap[kotlin] @ git+https://github.com/AZidan/codemap.git"      # Kotlin
pip install "codemap[swift] @ git+https://github.com/AZidan/codemap.git"       # Swift
pip install "codemap[go] @ git+https://github.com/AZidan/codemap.git"          # Go
pip install "codemap[java] @ git+https://github.com/AZidan/codemap.git"        # Java
pip install "codemap[csharp] @ git+https://github.com/AZidan/codemap.git"      # C#
pip install "codemap[rust] @ git+https://github.com/AZidan/codemap.git"        # Rust

# Install all languages
pip install "codemap[languages] @ git+https://github.com/AZidan/codemap.git"
```

> **Adding a language?** See [CONTRIBUTING.md](CONTRIBUTING.md) - new languages only need ~50 lines of config!

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

## LLM Integration Example

Here's how an LLM should use CodeMap:

### Without CodeMap ❌

```
1. Read entire user.py (500 lines, 6000 tokens)
2. Find UserService class
3. Make edit
4. Context resets...
5. Read entire user.py again (6000 more tokens)
```

### With CodeMap ✅

```
1. Run: codemap find "UserService"
   → src/user.py:15-89 [class] UserService

2. Read only lines 15-89 (1000 tokens)

3. Make edit

4. Context resets...

5. Run: codemap validate src/user.py
   → Up to date ✓ (no need to re-read!)
```

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
│   └── rust_parser.py
├── hooks/
│   └── installer.py       # Git hook installation
└── utils/
    ├── config.py          # Configuration management
    └── file_utils.py      # File discovery utilities
```

---

## 🤝 Contributing

Contributions are welcome! Here's where help is needed:

- [ ] **New language parsers** — Ruby, PHP, Scala, more!
- [ ] **MCP server mode** — For non-Claude tools
- [ ] **Fuzzy symbol search** — `codemap find "usr srv"` → `UserService`
- [ ] **VSCode extension** — GUI for non-CLI users
- [ ] **Performance optimization** — Faster indexing for huge repos

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

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
- Uses [tree-sitter](https://tree-sitter.github.io/) for TypeScript/JavaScript parsing

---

<div align="center">

**Built with ❤️ for developers tired of burning tokens**

[⬆ Back to top](#-codemap)

</div>
