# CodeMap Integration for AI Coding Assistants

This project uses **CodeMap** - a structural index of the codebase that enables targeted code navigation without reading entire files.

## Start Watch Mode First

Before working on the codebase, start watch mode to keep the index automatically updated:
```bash
codemap watch . &
```

This runs in the background and updates the index whenever files change.

## Quick Reference

```bash
# Find a symbol (class, function, method, type, interface)
codemap find "SymbolName"

# Show file structure with all symbols and line ranges
codemap show path/to/file.ts

# Check if index is up-to-date
codemap validate

# View statistics
codemap stats

# Start watch mode (keeps index updated automatically)
codemap watch . &
```

## When to Use CodeMap

**USE CodeMap first when:**
- Looking for where a class, function, or type is defined
- Needing to understand a file's structure before reading it
- Searching for symbols by name (case-insensitive)
- Checking if a file has changed since last indexed

**READ the full file when:**
- You need to understand implementation details
- Making edits to the code
- The symbol isn't in the index (new/untracked file)

## Workflow: Finding Code

### 1. Find a Symbol Location
```bash
codemap find "UserService"
```
Output:
```
src/services/user.ts:15-89 [class] UserService
  (config: Config)
```

### 2. Read Only the Relevant Lines
Instead of reading the entire file, read just lines 15-89:
```
Read lines 15-89 from src/services/user.ts
```

### 3. Explore Nested Symbols
```bash
codemap show src/services/user.ts
```
Output:
```
File: src/services/user.ts (hash: a3f2b8c1)
Lines: 542
Language: typescript

Symbols:
- UserService [class] L15-189
  (config: Config)
  - constructor [method] L20-35
  - getUser [method] L37-98
    (userId: string) : Promise<User>
  - createUser [async_method] L100-145
    (data: CreateUserDto) : Promise<User>
```

Now you can read just the specific method you need (e.g., lines 100-145 for `createUser`).

## Symbol Types

| Type | Description | Languages |
|------|-------------|-----------|
| `class` | Class declaration | Python, TS/JS, Kotlin, Swift, Java, C#, C++, Go (struct) |
| `function` | Function declaration | All languages |
| `method` | Class/struct method | All languages |
| `async_function` | Async function | Python, TS/JS |
| `async_method` | Async class method | Python, TS/JS |
| `interface` | Interface/protocol | TS, Kotlin, Swift (protocol), Go, Java, C# |
| `type` | Type alias | TypeScript |
| `enum` | Enum declaration | TS, Kotlin, Swift, Java, C#, Rust, C, C++ |
| `struct` | Struct declaration | Swift, Go, C#, Rust, C, C++ |
| `trait` | Trait declaration | Rust |
| `object` | Object declaration | Kotlin |
| `typedef` | Type definition | C |
| `namespace` | Namespace declaration | C++ |
| `template` | Template class/function | C++ |

## Filtering by Type

```bash
codemap find "handle" --type method      # Only methods
codemap find "User" --type interface     # Only interfaces
codemap find "create" --type function    # Only functions
```

## Validating Freshness

Before re-reading a file after context compaction:
```bash
codemap validate src/services/user.ts
```
- If "up to date": Line ranges are still valid, no need to re-read
- If "stale": File changed, re-read or run `codemap update`

## Index Structure

The `.codemap/` directory mirrors the project structure:
```
.codemap/
├── .codemap.json              # Root manifest (stats, config)
├── _root.codemap.json         # Files in project root
├── src/
│   ├── .codemap.json          # Files in src/
│   └── services/
│       └── .codemap.json      # Files in src/services/
```

You can read these JSON files directly for programmatic access to symbol locations.

## Best Practices

1. **Search before scanning**: Always try `codemap find` before grep/search
2. **Use line ranges**: Read specific line ranges instead of full files
3. **Check freshness**: Use `codemap validate` before trusting cached line numbers
4. **Explore structure first**: Use `codemap show` to understand file layout before diving in

## Example Session

Task: "Fix the authentication bug in the login handler"

```bash
# 1. Find relevant symbols
codemap find "login"
# → src/auth/handlers.ts:45-92 [function] handleLogin

# 2. Check file structure
codemap show src/auth/handlers.ts
# Shows handleLogin and related functions with line ranges

# 3. Read only the relevant function (lines 45-92)
# ... make your fix ...

# 4. If you need related code, find it
codemap find "validateToken"
# → src/auth/utils.ts:12-38 [function] validateToken
```

This approach reduces token usage by 60-80% compared to reading entire files.
