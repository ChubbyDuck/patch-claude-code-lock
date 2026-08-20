#!/usr/bin/env python3
"""Patch Claude Code extension.js to stop empty/locked editor columns.

Two fixes, both applied to every anthropic.claude-code-* install under
~/.cursor/extensions and ~/.vscode/extensions:

1. Lock: neutralize `workbench.action.lockEditorGroup` when the panel opens in
   a new column (`if(X)` → `if(X&&!1)`).
2. Column: replace `this.findUnusedColumn()` with `{alias}.ViewColumn.Beside||1`
   so opening Claude next to Cursor Agents does not create a stray empty group
   (findUnusedColumn picks an absolute unused ViewColumn and leaves a blank
   pane with only an X). The minified vscode import alias varies by version
   (e.g. Tt, It, Rt) and is detected from nearby createWebviewPanel usage.
"""

import re
import sys
from pathlib import Path

EXTENSION_ROOTS = [
    Path.home() / ".cursor" / "extensions",
    Path.home() / ".vscode" / "extensions",
]

# Matches: if(E)await Pe.commands.executeCommand("workbench.action.lockEditorGroup")
LOCK_CALL = re.compile(
    r"if\((?P<cond>[A-Za-z$_][\w$]*)\)"
    r'(?P<call>await [A-Za-z$_][\w$]*\.commands\.executeCommand\("workbench\.action\.lockEditorGroup"\))'
)

LOCK_ALREADY = re.compile(
    r"if\([A-Za-z$_][\w$]*&&!1\)"
    r'await [A-Za-z$_][\w$]*\.commands\.executeCommand\("workbench\.action\.lockEditorGroup"\)'
)

# Same length (23): keep the minified bundle layout intact.
COLUMN_OLD = "this.findUnusedColumn()"
COLUMN_PATCHED = re.compile(
    r"(?P<alias>[A-Za-z$_][\w$]*)\.ViewColumn\.Beside\|\|1"
)
# After a bad/good column patch: ...else i=ALIAS.ViewColumn.Beside||1,n=!0}let o=ALIAS.window.createWebviewPanel
COLUMN_SITE = re.compile(
    r"(?:this\.findUnusedColumn\(\)|[A-Za-z$_][\w$]*\.ViewColumn\.Beside\|\|1)"
    r"(?P<tail>,n=!0\}let o=([A-Za-z$_][\w$]*)\.window\.createWebviewPanel)"
)


def column_replacement(alias: str) -> str:
    return f"{alias}.ViewColumn.Beside||1"


def patch_file(extension_js: Path) -> str:
    src = extension_js.read_text()
    parts: list[str] = []

    if LOCK_ALREADY.search(src):
        parts.append("lock already patched")
    else:
        patched, count = LOCK_CALL.subn(r"if(\g<cond>&&!1)\g<call>", src)
        if count == 0:
            parts.append("lock PATTERN NOT FOUND")
        else:
            src = patched
            parts.append(f"lock patched ({count})")

    site = COLUMN_SITE.search(src)
    if site is None:
        if COLUMN_OLD in src:
            parts.append("column PATTERN NOT FOUND (no createWebviewPanel alias)")
        elif COLUMN_PATCHED.search(src):
            parts.append("column already patched")
        else:
            parts.append("column PATTERN NOT FOUND")
    else:
        alias = site.group(2)
        desired = column_replacement(alias)
        current = site.group(0)[: len(desired)]
        if current == desired:
            parts.append("column already patched")
        elif len(desired) != len(COLUMN_OLD):
            parts.append(f"column PATTERN NOT FOUND (alias {alias!r} wrong length)")
        else:
            src = src[: site.start()] + desired + src[site.start() + len(desired) :]
            if current == COLUMN_OLD:
                parts.append(f"column patched ({alias})")
            else:
                parts.append(f"column fixed ({current.split('.')[0]}→{alias})")

    if any(
        p.startswith("lock patched")
        or p.startswith("column patched")
        or p.startswith("column fixed")
        for p in parts
    ):
        extension_js.write_text(src)

    return "; ".join(parts)


def main() -> int:
    found_any = False
    failures = 0
    for root in EXTENSION_ROOTS:
        if not root.is_dir():
            continue
        for ext_dir in sorted(root.glob("anthropic.claude-code-*")):
            extension_js = ext_dir / "extension.js"
            if not extension_js.is_file():
                print(f"{ext_dir.name}: extension.js missing, skipped")
                continue
            found_any = True
            result = patch_file(extension_js)
            print(f"{ext_dir.name} ({root}): {result}")
            if "NOT FOUND" in result:
                failures += 1
    if not found_any:
        print("No anthropic.claude-code-* extension installations found.")
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
