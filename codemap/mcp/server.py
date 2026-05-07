"""
CodeMap MCP server (stdio) — works with any MCP-capable client (Cursor, Claude Desktop, …).

Depends on optional extra: pip install codemap[mcp]

Resolves `codemap` via PATH or the interpreter's script directory (venv-friendly).
Optional env: CODEMAP_WORKSPACE_ROOT when cwd is ambiguous.

Server instructions nudge assistants to poll `codemap_after_git_checkpoint`; MCP cannot
silently invoke tools — clients must honor `instructions`.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

from mcp.server.fastmcp import FastMCP

MARKER_NAME = "CURSOR_SUGGEST_CODEMAP_REFRESH"


def resolve_codemap() -> str | None:
    exe = shutil.which("codemap")
    if exe:
        return exe
    bundled = Path(sys.executable).resolve().parent / "codemap"
    if bundled.is_file() and os.access(bundled, os.X_OK):
        return str(bundled)
    fb = Path.home() / ".local" / "bin" / "codemap"
    if fb.is_file() and os.access(fb, os.X_OK):
        return str(fb)
    return None


def workspace_dir(explicit: str) -> str:
    if explicit and explicit.strip():
        return os.path.realpath(os.path.expanduser(explicit.strip()))
    env = os.environ.get("CODEMAP_WORKSPACE_ROOT", "").strip()
    if env:
        return os.path.realpath(os.path.expanduser(env))
    return os.path.realpath(os.getcwd())


def git_absolute_dir(workspace_root: str) -> str | None:
    r = subprocess.run(
        ["git", "rev-parse", "--absolute-git-dir"],
        cwd=workspace_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if r.returncode != 0:
        return None
    p = (r.stdout or "").strip()
    return p if os.path.isdir(p) else None


def peek_marker_snippet(workspace_root: str = "") -> str:
    """One-line boot hint for server instructions (no mutation)."""
    root = workspace_dir(workspace_root)
    gd = git_absolute_dir(root)
    if not gd:
        return ""
    marker = os.path.join(gd, MARKER_NAME)
    if not os.path.isfile(marker):
        return ""
    try:
        with open(marker, encoding="utf-8") as fh:
            raw = fh.read().strip()
    except OSError:
        return "(pending marker unreadable)"
    if "\t" in raw:
        reason, stamp = raw.split("\t", 1)
    else:
        reason, stamp = raw, ""
    bit = stamp.strip() or ""
    suf = f" ({bit})" if bit else ""
    return (
        f"PENDING GIT SYNC{suf}: `{reason.strip()}` — call codemap_after_git_checkpoint "
        "then offer codemap_validate / codemap_update."
    )


def build_server_instructions() -> str:
    base = """You are connected to the **CodeMap** MCP server.

**Automation policy — apply unless the user opts out of CodeMap for this task:**
1. **Every user-visible turn**, before substantive code edits or searches, call `codemap_after_git_checkpoint` once (omit `workspace_root` if cwd / CODEMAP_WORKSPACE_ROOT is correct).
2. If it reports **pending git**, inform the user and **offer** optional `codemap_validate` then `codemap_update` (all_files=true). Run `codemap_update` only after they agree or they asked to refresh.
3. For exploration, prefer `codemap_find` then narrow reads over whole files.
4. You may read resource `codemap://git-sync-status` for the same checkpoint text (read-only).

This keeps indexes aligned with the working tree after merges/rebases without silent heavy work."""
    boot = peek_marker_snippet("")
    if boot:
        return base + "\n\n**Current boot notice:** " + boot
    return base


mcp = FastMCP("codemap", instructions=build_server_instructions())


def run_codemap(cwd: str, args: list[str], timeout: int = 600) -> str:
    exe = resolve_codemap()
    if not exe:
        return "error: codemap CLI not found. Install CodeMap in this environment (same venv as codemap-mcp)."
    if not os.path.isdir(cwd):
        return f"error: workspace directory does not exist: {cwd}"
    try:
        r = subprocess.run(
            [exe, *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"error: codemap subprocess timed out after {timeout}s"
    except OSError as e:
        return f"error: failed to run codemap: {e}"
    out = (r.stdout or "").strip()
    err = (r.stderr or "").strip()
    bits: list[str] = []
    if out:
        bits.append(out)
    if err:
        bits.append("[stderr]\n" + err)
    if r.returncode != 0:
        bits.append(f"(exit code {r.returncode})")
    return "\n".join(bits) if bits else f"(exit code {r.returncode}, no output)"


def describe_git_checkpoint(workspace_root: str, consume_marker: bool) -> str:
    root = workspace_dir(workspace_root)
    gd = git_absolute_dir(root)
    if not gd:
        return f"no git repo at workspace: {root}"
    marker = os.path.join(gd, MARKER_NAME)
    if not os.path.isfile(marker):
        return (
            "no pending git-sync hint for CodeMap.\n"
            "(Marker absent — no recent merge/rebase/checkout ping, or already consumed.)"
        )
    try:
        with open(marker, encoding="utf-8") as fh:
            raw = fh.read().strip()
    except OSError as e:
        return f"error reading marker: {e}"
    if "\t" in raw:
        reason, stamp = raw.split("\t", 1)
    else:
        reason, stamp = raw, ""
    reason = reason.strip()
    stamp = stamp.strip()
    stamp_part = f" at {stamp}" if stamp else ""
    body = (
        f"pending_git_sync_marker: yes\nreason: {reason}{stamp_part}\n\n"
        "Optional — line ranges may be stale until refreshed:\n"
        "  1) codemap_validate\n"
        "  2) codemap_update(all_files=true) — only after user confirms or asks\n\n"
        "Cheap reads depend on an up-to-date index (CodeMap philosophy)."
    )
    if consume_marker:
        try:
            os.unlink(marker)
            body += "\n\n(marker consumed / deleted)"
        except OSError as e:
            body += f"\n\n(warning: could not consume marker: {e})"
    return body


@mcp.resource("codemap://git-sync-status")
def resource_git_sync_status() -> str:
    """Same payload as `codemap_after_git_checkpoint` without consuming the marker."""
    return describe_git_checkpoint("", consume_marker=False)


@mcp.tool()
def codemap_after_git_checkpoint(
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
    consume_marker: Annotated[
        bool,
        "If true, delete the marker after returning (after successful codemap_update).",
    ] = False,
) -> str:
    """Optional `.git/` sentinel from external git hooks (Cursor / custom)."""
    return describe_git_checkpoint(workspace_root, consume_marker)


@mcp.tool()
def codemap_health(
    workspace_root: Annotated[str, "Repository root (empty => CODEMAP_WORKSPACE_ROOT or cwd)"] = "",
) -> str:
    """Check codemap CLI and `.codemap/.codemap.json` presence."""
    root = workspace_dir(workspace_root)
    exe = resolve_codemap()
    exe_line = exe or "(not found)"
    manifest = os.path.join(root, ".codemap", ".codemap.json")
    mf = "present" if os.path.isfile(manifest) else "missing"
    probe = ""
    if exe:
        r = subprocess.run(
            [exe, "--help"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        probe = (
            (r.stdout or r.stderr or "").splitlines()[0]
            if (r.stdout or r.stderr)
            else f"exit {r.returncode}"
        )
    return f"codemap: {exe_line}\nworkspace: {root}\nmanifest .codemap/.codemap.json: {mf}\n{probe}".strip()


@mcp.tool()
def codemap_find(
    query: Annotated[str, "Symbol or substring to search for"],
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
    symbol_type: Annotated[str, "Optional codemap --type filter"] = "",
    fuzzy: Annotated[bool, "Use codemap --fuzzy"] = False,
) -> str:
    """Run `codemap find`."""
    root = workspace_dir(workspace_root)
    args: list[str] = ["find", query]
    if symbol_type.strip():
        args.extend(["--type", symbol_type.strip()])
    if fuzzy:
        args.append("--fuzzy")
    return run_codemap(root, args)


@mcp.tool()
def codemap_show(
    file_path: Annotated[str, "Path relative to workspace root"],
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
) -> str:
    """Run `codemap show` for symbol ranges in one file."""
    root = workspace_dir(workspace_root)
    return run_codemap(root, ["show", file_path])


@mcp.tool()
def codemap_validate(
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
    path: Annotated[str, "Optional file to validate"] = "",
) -> str:
    """Run `codemap validate`."""
    root = workspace_dir(workspace_root)
    args = ["validate"]
    if path.strip():
        args.append(path.strip())
    return run_codemap(root, args)


@mcp.tool()
def codemap_update(
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
    all_files: Annotated[bool, "Run codemap update --all"] = True,
    single_path: Annotated[str, "When all_files false, path to refresh"] = "",
) -> str:
    """Run `codemap update --all` or refresh one path."""
    root = workspace_dir(workspace_root)
    if all_files:
        return run_codemap(root, ["update", "--all"], timeout=1200)
    if not single_path.strip():
        return "error: set single_path when all_files is false"
    return run_codemap(root, ["update", single_path.strip()], timeout=1200)


@mcp.tool()
def codemap_init(
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
    extra_args: Annotated[str, "Extra tokens passed after `codemap init .`"] = "",
) -> str:
    """Run `codemap init .` plus optional whitespace-separated extra args."""
    root = workspace_dir(workspace_root)
    args = ["init", "."]
    if extra_args.strip():
        args.extend(extra_args.split())
    return run_codemap(root, args, timeout=1200)


@mcp.tool()
def codemap_stats(
    workspace_root: Annotated[str, "Repo root (empty => env/cwd)"] = "",
) -> str:
    """Run `codemap stats`."""
    root = workspace_dir(workspace_root)
    return run_codemap(root, ["stats"])


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
