# mise-en-place

A Claude Code setup as code: rules, skills, hooks, an output style and settings, installed under `~/.claude`.

It is one person's opinionated setup: `rules/global.md` loads in every session and sets policies such as branch naming, worktree layout and which model subagents run on. The recommended use is to fork it and ask your agent to adapt it to you.

```
rules/             user-level rules: global.md (no paths) loads in every session; the others load when Claude reads or edits a file matching their paths (Read, Edit, Write, or a single-command shell read)
settings.json      user-level settings: marketplaces, plugins, output style...
skills/ output-styles/ hooks/
docs/              docs rules/global.md points skills at: issue tracker, domain docs, track builds, worktrees, subagents
```

## Setup

Requires git, jq and python3 (3.9 or later; on macOS, the Command Line Tools ship it).

1. Fork this repo and clone your fork:

   ```sh
   git clone <your fork> ~/mise
   ```

2. In `~/mise`, ask your agent to adapt it to you: start with `rules/global.md` and `settings.json`, then the skills you won't use.

3. Link it into `~/.claude` (keep `~/.claude` itself out of git). Anything already there is moved aside to `<name>.bak`:

   ```sh
   mkdir -p ~/.claude
   for d in rules skills output-styles hooks docs settings.json; do
     if [ -e ~/.claude/$d ] && [ ! -L ~/.claude/$d ]; then mv ~/.claude/$d ~/.claude/$d.bak; fi
     ln -sfn ~/mise/$d ~/.claude/$d
   done
   ```

   Drop `settings.json` from the list to keep your own settings.

Run `tests/check.sh` after changing a script or hook.

## License

MIT, in [LICENSE](LICENSE).

## Credits

Many skills in `skills/` and rules in `rules/` are based on [mattpocock/skills](https://github.com/mattpocock/skills) and [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), both MIT-licensed; their notices are in [LICENSE](LICENSE).
