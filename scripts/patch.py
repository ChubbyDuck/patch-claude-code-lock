#!/usr/bin/env python3
"""Patch Claude Code extension.js to stop empty/locked editor columns.

Three fixes, all applied to every anthropic.claude-code-* install under
~/.cursor/extensions and ~/.vscode/extensions:

1. Lock: neutralize `workbench.action.lockEditorGroup` when the panel opens in
   a new column (`if(X)` → `if(X&&!1)`).
2. Column: replace `this.findUnusedColumn()` with `{alias}.ViewColumn.Beside||1`
   so opening Claude next to Cursor Agents does not create a stray empty group
   (findUnusedColumn picks an absolute unused ViewColumn and leaves a blank
   pane with only an X). The minified vscode import alias varies by version
   (e.g. Tt, It, Rt) and is detected from nearby createWebviewPanel usage.
3. Group: createPanel reuses an existing editor group only if ALL of its tabs
   are Claude webviews (`tabs.every(...viewType.includes("claudeVSCodePanel"))`).
   As soon as one regular file shares the group, every new session opens in a
   fresh split instead of joining the existing Claude tabs. `every` → `some`:
   one Claude tab in a group is enough to reuse it.
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
# Before/after the column patch: ...else i=this.findUnusedColumn(),n=!0}let o=ALIAS.window.createWebviewPanel
# The flag/panel variable names (n, o / i, s / ...) vary by version like the alias does.
COLUMN_SITE = re.compile(
    r"(?:this\.findUnusedColumn\(\)|[A-Za-z$_][\w$]*\.ViewColumn\.Beside\|\|1)"
    r"(?P<tail>,[A-Za-z$_][\w$]*=!0\}let [A-Za-z$_][\w$]*="
    r"(?P<alias>[A-Za-z$_][\w$]*)\.window\.createWebviewPanel)"
)


# Matches: if(l.tabs.length===0)return!1;return l.tabs.every((u)=>{
#   if(u.input instanceof Nt.TabInputWebview)return u.input.viewType.includes("claudeVSCodePanel");return!1})
GROUP_CALL = re.compile(
    r"(?P<head>tabs\.length===0\)return!1;return [A-Za-z$_][\w$]*\.tabs\.)every"
    r"(?P<tail>\(\([A-Za-z$_][\w$]*\)=>\{if\([A-Za-z$_][\w$]*\.input instanceof "
    r"[A-Za-z$_][\w$]*\.TabInputWebview\)return [A-Za-z$_][\w$]*"
    r'\.input\.viewType\.includes\("claudeVSCodePanel"\))'
)

GROUP_ALREADY = re.compile(
    r"tabs\.length===0\)return!1;return [A-Za-z$_][\w$]*\.tabs\.some\("
)


def column_replacement(alias: str) -> str:
    return f"{alias}.ViewColumn.Beside||1"


def patch_file(extension_js: Path) -> str:
    src = extension_js.read_text(encoding="utf-8")
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
        alias = site.group("alias")
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

    if GROUP_ALREADY.search(src):
        parts.append("group already patched")
    else:
        patched, count = GROUP_CALL.subn(r"\g<head>some\g<tail>", src)
        if count == 0:
            parts.append("group PATTERN NOT FOUND")
        else:
            src = patched
            parts.append(f"group patched ({count})")

    if any(
        p.startswith("lock patched")
        or p.startswith("column patched")
        or p.startswith("column fixed")
        or p.startswith("group patched")
        for p in parts
    ):
        extension_js.write_text(src, encoding="utf-8")

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
