# CodeMap Plugin for Claude Code

A Claude Code plugin that enables efficient codebase navigation through structural indexes.

## What It Does

The CodeMap skill teaches Claude how to use pre-built codebase indexes stored in `.codemap/` directories. This reduces token consumption by 60-80% by enabling targeted line-range reads instead of full file scans.

## Installation

### Prerequisites

Install the CodeMap CLI tool:

```bash
pip install git+https://github.com/AZidan/codemap.git
```

For additional language support:

```bash
# TypeScript/JavaScript
pip install tree-sitter-javascript tree-sitter-typescript

# Kotlin
pip install tree-sitter-kotlin

# Swift
pip install tree-sitter-swift

# C/C++
pip install tree-sitter-c tree-sitter-cpp
```

### Install the Plugin

```bash
# Clone or download the plugin
git clone https://github.com/AZidan/codemap.git

# Install the plugin to Claude Code
claude plugin install ./codemap/plugin
```

Or copy the plugin directory to your Claude Code plugins location.

## Usage

### 1. Initialize CodeMap in Your Project

```bash
cd your-project
codemap init .
```

This creates a `.codemap/` directory with structural indexes of your codebase.

### 2. Let Claude Use It Automatically

Once the skill is installed, Claude will automatically use CodeMap when:
- Looking for symbol definitions (classes, functions, methods)
- Exploring file structure
- Navigating large codebases

### 3. Manual Invocation

You can also explicitly ask Claude to use CodeMap:

```
"Use codemap to find the UserService class"
"Show me the structure of src/auth/handlers.ts using codemap"
```

## What Gets Indexed

| Language | Symbol Types |
|----------|-------------|
| **Python** | Classes, functions, methods, async functions/methods |
| **TypeScript/JavaScript** | Classes, functions, methods, interfaces, types, enums |
| **Kotlin** | Classes, interfaces, objects, functions |
| **Swift** | Structs, classes, protocols, enums, functions |
| **C** | Functions, structs, enums, typedefs |
| **C++** | Classes, structs, functions, methods, namespaces, enums, templates |
| **Markdown** | H2/H3/H4 sections |
| **YAML** | Keys, nested sections |

## Commands Available to Claude

| Command | Purpose |
|---------|---------|
| `codemap find "Name"` | Find symbols by name |
| `codemap show file.ts` | Show file structure with line ranges |
| `codemap validate` | Check if index is up-to-date |
| `codemap stats` | View index statistics |

## Directory Structure

```
plugin/
├── .claude-plugin/
│   └── plugin.json      # Plugin manifest
├── skills/
│   └── codemap/
│       └── SKILL.md     # The skill definition
└── README.md
```

## License

MIT
