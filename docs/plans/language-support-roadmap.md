# Language Support Roadmap

> Plan to expand CodeMap's language support using tree-sitter grammars, prioritized by popularity.

## Current Status

**Supported Languages (13):**
- Python (stdlib ast)
- TypeScript, JavaScript (tree-sitter)
- Kotlin, Swift (tree-sitter)
- Go, Java, C#, Rust (tree-sitter)
- C, C++ (tree-sitter)
- Markdown, YAML (custom parsers)

## Priority Tiers

Languages ranked by combined popularity from [TIOBE Index](https://www.tiobe.com/tiobe-index/), [Stack Overflow 2025 Survey](https://survey.stackoverflow.co/2025/technology), and [GitHub Octoverse](https://github.blog/news-insights/octoverse/).

### Tier 1: Critical (Top 10 Most Used)

| Rank | Language | TIOBE 2025 | Stack Overflow | Status | Package |
|------|----------|------------|----------------|--------|---------|
| 1 | Python | #1 (26%) | #3 (53%) | ✅ Done | stdlib ast |
| 2 | JavaScript | #6 | #1 (66%) | ✅ Done | tree-sitter-javascript |
| 3 | TypeScript | #9 | #5 (43%) | ✅ Done | tree-sitter-typescript |
| 4 | Java | #4 | #8 (30%) | ✅ Done | tree-sitter-java |
| 5 | C# | #5 | #9 (27%) | ✅ Done | tree-sitter-c-sharp |
| 6 | C++ | #2 | #10 (20%) | ✅ Done | tree-sitter-cpp |
| 7 | C | #3 | #12 (17%) | ✅ Done | tree-sitter-c |
| 8 | Go | #8 | #13 (14%) | ✅ Done | tree-sitter-go |
| 9 | Rust | #13 | #14 (13%) | ✅ Done | tree-sitter-rust |
| 10 | PHP | #17 | #11 (18%) | ⏳ Planned | tree-sitter-php |

**Tier 1 Completion: 10/10 (100%) - Only PHP remaining!**

### Tier 2: High Priority (Ranks 11-25)

| Rank | Language | TIOBE 2025 | Stack Overflow | Status | Package |
|------|----------|------------|----------------|--------|---------|
| 11 | SQL | - | #4 (52%) | ⏳ Planned | tree-sitter-sql |
| 12 | HTML | - | #2 (54%) | ⏳ Planned | tree-sitter-html |
| 13 | CSS/SCSS | - | #6 (42%) | ⏳ Planned | tree-sitter-css |
| 14 | Bash/Shell | - | #7 (33%) | ⏳ Planned | tree-sitter-bash |
| 15 | Ruby | #18 | #17 (6%) | ⏳ Planned | tree-sitter-ruby |
| 16 | Kotlin | #15 | #15 (9%) | ✅ Done | tree-sitter-kotlin |
| 17 | Swift | #16 | #16 (6%) | ✅ Done | tree-sitter-swift |
| 18 | Lua | #26 | #21 (4%) | ⏳ Planned | tree-sitter-lua |
| 19 | Dart | #20 | #18 (6%) | ⏳ Planned | tree-sitter-dart |
| 20 | R | #10 | #22 (4%) | ⏳ Planned | tree-sitter-r |
| 21 | Scala | #28 | #24 (3%) | ⏳ Planned | tree-sitter-scala |
| 22 | Perl | #11 | #26 (2%) | ⏳ Planned | tree-sitter-perl |
| 23 | Objective-C | #19 | #27 (2%) | ⏳ Planned | tree-sitter-objc |
| 24 | Elixir | #40 | #28 (3%) | ⏳ Planned | tree-sitter-elixir |
| 25 | Haskell | #29 | #29 (2%) | ⏳ Planned | tree-sitter-haskell |

**Tier 2 Completion: 2/15 (13%)**

### Tier 3: Medium Priority (Config/Data Languages)

| Language | Use Case | Status | Package |
|----------|----------|--------|---------|
| JSON | Config files | ⏳ Planned | tree-sitter-json |
| TOML | Config files (Rust, Python) | ⏳ Planned | tree-sitter-toml |
| XML | Config, data | ⏳ Planned | tree-sitter-xml |
| GraphQL | API schemas | ⏳ Planned | tree-sitter-graphql |
| Dockerfile | DevOps | ⏳ Planned | tree-sitter-dockerfile |
| HCL/Terraform | Infrastructure | ⏳ Planned | tree-sitter-hcl |
| Protobuf | Data serialization | ⏳ Planned | tree-sitter-proto |
| Makefile | Build systems | ⏳ Planned | tree-sitter-make |

**Tier 3 Completion: 0/8 (0%)**

### Tier 4: Emerging/Niche Languages

| Language | Trend | Status | Package |
|----------|-------|--------|---------|
| Zig | Rising fast (#42 TIOBE) | ⏳ Planned | tree-sitter-zig |
| Gleam | Most admired 2025 | ⏳ Planned | tree-sitter-gleam |
| Nim | Systems programming | ⏳ Planned | tree-sitter-nim |
| V | Simple systems lang | ⏳ Planned | tree-sitter-v |
| Julia | Scientific computing | ⏳ Planned | tree-sitter-julia |
| Clojure | Functional JVM | ⏳ Planned | tree-sitter-clojure |
| F# | Functional .NET | ⏳ Planned | tree-sitter-f-sharp |
| OCaml | Functional | ⏳ Planned | tree-sitter-ocaml |
| Erlang | Distributed systems | ⏳ Planned | tree-sitter-erlang |
| Crystal | Ruby-like compiled | ⏳ Planned | tree-sitter-crystal |

**Tier 4 Completion: 0/10 (0%)**

---

## Implementation Plan

### Phase 1: Complete Tier 1 (2 languages)

**C++ Parser**
```
Symbols: class, struct, function, method, namespace, enum, template
File extensions: .cpp, .hpp, .cc, .hh, .cxx, .hxx
Complexity: High (templates, namespaces, operator overloading)
```

**C Parser**
```
Symbols: function, struct, enum, typedef, macro
File extensions: .c, .h
Complexity: Medium (preprocessor macros)
```

**PHP Parser**
```
Symbols: class, interface, trait, function, method
File extensions: .php
Complexity: Medium
```

### Phase 2: High-Value Web Languages

**HTML Parser**
```
Symbols: element (semantic tags), id, class
File extensions: .html, .htm
Complexity: Low (flat structure)
```

**CSS Parser**
```
Symbols: selector, class, id, keyframe, media-query
File extensions: .css, .scss, .sass, .less
Complexity: Medium (nested selectors in SCSS)
```

**SQL Parser**
```
Symbols: table, view, function, procedure, trigger
File extensions: .sql
Complexity: Medium (dialect variations)
```

### Phase 3: Shell & DevOps

**Bash Parser**
```
Symbols: function
File extensions: .sh, .bash, .zsh
Complexity: Low
```

**Dockerfile Parser**
```
Symbols: stage, instruction
File extensions: Dockerfile, .dockerfile
Complexity: Low
```

**HCL/Terraform Parser**
```
Symbols: resource, variable, module, output, data
File extensions: .tf, .hcl
Complexity: Medium
```

### Phase 4: Additional Languages

Implement remaining Tier 2-4 languages based on user demand.

---

## Symbol Extraction Guidelines

### Standard Symbol Types by Category

**Object-Oriented Languages** (Java, C#, C++, PHP, Ruby, etc.)
- class, interface, struct, enum
- method, constructor, property
- namespace/module/package

**Functional Languages** (Haskell, Elixir, F#, OCaml, etc.)
- module, function, type, typeclass/protocol

**Scripting Languages** (Bash, Lua, Perl, etc.)
- function

**Markup/Config** (HTML, CSS, SQL, etc.)
- Language-specific structures (tables, selectors, elements)

---

## Alternative: tree-sitter-language-pack

Instead of individual packages, consider using [tree-sitter-language-pack](https://pypi.org/project/tree-sitter-language-pack/) which bundles 160+ languages.

**Pros:**
- Single dependency for all languages
- Pre-compiled wheels, no build step
- Maintained and updated regularly

**Cons:**
- Larger install size
- Requires Python 3.10+
- Less control over specific grammar versions

**Recommendation:** Use individual packages for Tier 1-2 languages (better control), consider language-pack for Tier 3-4 (convenience).

---

## Progress Tracking

| Tier | Total | Done | Remaining | Completion |
|------|-------|------|-----------|------------|
| Tier 1 (Critical) | 10 | 9 | 1 | 90% |
| Tier 2 (High Priority) | 15 | 2 | 13 | 13% |
| Tier 3 (Config/Data) | 8 | 0 | 8 | 0% |
| Tier 4 (Emerging) | 10 | 0 | 10 | 0% |
| **Total** | **43** | **11** | **32** | **26%** |

---

## Next Actions

1. [x] Implement C++ parser (Tier 1) ✅ Done
2. [x] Implement C parser (Tier 1) ✅ Done
3. [ ] Implement PHP parser (Tier 1) - PR #6 under review
4. [ ] Evaluate tree-sitter-language-pack vs individual packages
5. [ ] Add HTML/CSS/SQL parsers (Tier 2 web stack)
6. [ ] Add Bash parser (Tier 2 DevOps)
