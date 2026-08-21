---
name: patch-claude-code-lock
description: Patches the Claude Code (anthropic.claude-code) extension to stop locking editor groups, stop creating a buggy empty editor column (blank pane with only an X) when opening via Cmd+Alt+U next to Cursor Agents, and make new sessions join an existing group that mixes Claude tabs with regular files instead of opening a new split. Use when the Claude Code tab group shows the lock icon, when an empty panel with an X appears after summoning Claude Code, when new sessions split instead of joining the existing Claude tabs, or after the Claude Code extension updated and the previous patch was overwritten.
license: MIT
---

# Patch Claude Code Group Locking + Empty Column + Group Reuse

The Claude Code extension has three layout bugs when its panel opens as an editor tab:

1. It programmatically runs `workbench.action.lockEditorGroup` (bypasses `workbench.editor.autoLockGroups`).
2. It calls `findUnusedColumn()` instead of `ViewColumn.Beside`, which next to Cursor Agents creates a stray empty editor group (blank pane with only an X).
3. `createPanel` reuses an existing editor group only if ALL of its tabs are Claude webviews (`tabs.every(...viewType.includes("claudeVSCodePanel"))`). One regular file in the group and every new session opens in a fresh split instead of joining the existing Claude tabs.

There is no setting to disable any of these behaviors. The only fix is patching minified `extension.js` in each installed version. Extension updates install into a fresh directory, so the patch must be re-applied after every update.

## Instructions

1. Run the patch script:

   ```bash
   python3 scripts/patch.py
   ```

   Run it from this skill directory (the folder that contains `SKILL.md`). It finds every `anthropic.claude-code-*` directory under `~/.cursor/extensions` and `~/.vscode/extensions`, and applies all three fixes in each `extension.js`. Already-patched pieces are skipped. The script prints per version, e.g. `lock already patched; column patched; group patched`.

2. If every version reports patched/already-patched for all pieces, tell the user to run **Developer: Reload Window**, close any currently empty group once (click its X), and unlock any locked group once (the patch only prevents future locks/empty columns).

3. If a version reports `PATTERN NOT FOUND`, the extension code changed. Locate the new call site with:

   ```bash
   rg -o '.{200}lockEditorGroup.{200}' <extension-dir>/extension.js
   rg -o '.{120}findUnusedColumn.{80}' <extension-dir>/extension.js
   rg -o '.{80}claudeVSCodePanel.{40}' <extension-dir>/extension.js
   ```

   Then apply a minimal edit and update `scripts/patch.py`. Known good replacements:

   - `if(X)await Y.commands.executeCommand("workbench.action.lockEditorGroup")` → `if(X&&!1)await ...`
   - `this.findUnusedColumn()` (23 chars) → `{alias}.ViewColumn.Beside||1` (23 chars; `{alias}` is the minified `vscode` import in that scope — detect from nearby `ALIAS.window.createWebviewPanel`, e.g. `Tt` / `It` / `Rt`)
   - `...tabs.length===0)return!1;return X.tabs.every((u)=>{if(u.input instanceof Y.TabInputWebview)return u.input.viewType.includes("claudeVSCodePanel")...` → same with `X.tabs.some(`
