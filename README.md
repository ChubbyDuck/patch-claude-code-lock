# patch-claude-code-lock

[![skills.sh](https://skills.sh/b/ChubbyDuck/patch-claude-code-lock)](https://skills.sh/ChubbyDuck/patch-claude-code-lock)

Agent skill that patches the Claude Code (`anthropic.claude-code`) extension so it stops locking editor groups and creating a stray empty column (blank pane with only an X) when opened next to Cursor Agents.

There is no setting for either behavior. The skill patches minified `extension.js` in each installed version. Extension updates install into a fresh directory, so re-run the patch after every update.

## Install

```bash
npx skills add ChubbyDuck/patch-claude-code-lock
```

This is a private GitHub repo. The [skills CLI](https://www.skills.sh/) can still install it if you have access (Git credentials, GitHub CLI, or SSH). For a global Cursor install:

```bash
npx skills add ChubbyDuck/patch-claude-code-lock -g -a cursor -y
```

Browse the skill on [skills.sh](https://skills.sh/ChubbyDuck/patch-claude-code-lock).

## Usage

Ask your agent to apply the Claude Code lock patch, or run it yourself from this skill directory:

```bash
python3 scripts/patch.py
```

The script finds every `anthropic.claude-code-*` install under `~/.cursor/extensions` and `~/.vscode/extensions`. After a successful patch, reload the window (`Developer: Reload Window`), close any leftover empty group once, and unlock any already-locked group once.

## License

[MIT](LICENSE)
