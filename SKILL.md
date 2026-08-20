---
name: patch-claude-code-lock
description: Patches the Claude Code (anthropic.claude-code) extension to stop locking editor groups and stop creating a buggy empty editor column (blank pane with only an X) when opening via Cmd+Alt+U next to Cursor Agents. Use when the Claude Code tab group shows the lock icon, when an empty panel with an X appears after summoning Claude Code, or after the Claude Code extension updated and the previous patch was overwritten.
license: MIT
---

# Patch Claude Code Group Locking + Empty Column

The Claude Code extension has two layout bugs when its panel opens in a new editor column:

1. It programmatically runs `workbench.action.lockEditorGroup` (bypasses `workbench.editor.autoLockGroups`).
2. It calls `findUnusedColumn()` instead of `ViewColumn.Beside`, which next to Cursor Agents creates a stray empty editor group (blank pane with only an X).

There is no setting to disable either behavior. The only fix is patching minified `extension.js` in each installed version. Extension updates install into a fresh directory, so the patch must be re-applied after every update.

## Instructions

1. Run the patch script:

   ```bash
   python3 scripts/patch.py
   ```

   Run it from this skill directory (the folder that contains `SKILL.md`). It finds every `anthropic.claude-code-*` directory under `~/.cursor/extensions` and `~/.vscode/extensions`, and applies both fixes in each `extension.js`. Already-patched pieces are skipped. The script prints per version, e.g. `lock already patched; column patched`.

2. If every version reports patched/already-patched for both pieces, tell the user to run **Developer: Reload Window**, close any currently empty group once (click its X), and unlock any locked group once (the patch only prevents future locks/empty columns).

3. If a version reports `PATTERN NOT FOUND`, the extension code changed. Locate the new call site with:

   ```bash
   rg -o '.{200}lockEditorGroup.{200}' <extension-dir>/extension.js
   rg -o '.{120}findUnusedColumn.{80}' <extension-dir>/extension.js
   ```

   Then apply a minimal same-length edit and update `scripts/patch.py`. Known good replacements:

   - `if(X)await Y.commands.executeCommand("workbench.action.lockEditorGroup")` → `if(X&&!1)await ...`
   - `this.findUnusedColumn()` (23 chars) → `{alias}.ViewColumn.Beside||1` (23 chars; `{alias}` is the minified `vscode` import in that scope — detect from nearby `ALIAS.window.createWebviewPanel`, e.g. `Tt` / `It` / `Rt`)
