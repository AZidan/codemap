# CodeMap Usage (Embed in AI Assistant Instructions)

Copy the section below into your `CLAUDE.md`, `copilot-instructions.md`, or similar files:

---

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
Python, TypeScript, JavaScript, Kotlin, Swift, Go, Java, C#, Rust, Markdown, YAML

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

---

## Minimal Version (For Space-Constrained Files)

```markdown
## CodeMap
Start watch mode first: `codemap watch . &`

Use `.codemap/` index before scanning files:
- `codemap find "Name"` - Find symbols by name
- `codemap show file.ts` - Show file structure with line ranges
- `codemap watch . &` - Keep index auto-updated

Workflow: Start watch → Find symbol → Read only those lines
```
