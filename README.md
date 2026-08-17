# promptalias

Reusable prompts, written once as [Agent Skills](https://skills.sh) and shared across
Claude Code, Codex, and Cursor. Each prompt is a folder with a `SKILL.md`, and
`npx skills` distributes them to every agent's skills directory.

> **There is no `promptalias` command.** The name comes from a CLI that was designed and
> then killed before implementation — a compiler from one terse YAML file into per-tool
> command files. It turned out the three tools had converged on a single format, so there
> was nothing left to compile. The name stuck; the compiler never happened. The full
> reasoning, with links, is in [`docs/prior-art.md`](docs/prior-art.md).

This is not a text expander and not a config-sync tool. [Espanso](https://espanso.org)
expands triggers into text system-wide in any app, and knows nothing about agent command
formats. [rulesync](https://github.com/dyoshikawa/rulesync), `vsync`, and
`agent-skill-porter` compile or convert configs *between* tools' directories. This repo
skips that whole category: the three tools already read the same `SKILL.md` format, so
there is nothing to compile. See [`docs/prior-art.md`](docs/prior-art.md) for the research
that led here, including the two research passes that killed the CLI.

## Install

```sh
npx skills add . --global --all   # install every skill for every agent
npx skills list -g                # show what's installed where
```

Two caveats worth knowing, both measured rather than assumed.

**`add` copies; it does not link back here.** It writes each `SKILL.md` into a hub at
`~/.agents/skills/<name>/` and symlinks agent directories at *the hub*. Edits to this repo
are therefore invisible until you re-run `add`. Confirmed by editing `u/SKILL.md` and
watching the hub not change.

**`add` did not reach Codex or Cursor.** It reported success for both while writing only to
the hub, leaving `~/.codex/skills/` empty and `~/.cursor/skills-cursor/` untouched.

The fix for both is one chain of symlinks — point the hub at this repo, then point each
tool at the hub:

```sh
rm -rf ~/.agents/skills/u ~/.agents/skills/rv
ln -s ~/promptalias/u  ~/.agents/skills/u
ln -s ~/promptalias/rv ~/.agents/skills/rv

mkdir -p ~/.codex/skills ~/.cursor/skills-cursor
for s in u rv; do
  ln -sfn ~/.agents/skills/$s ~/.codex/skills/$s
  ln -sfn ~/.agents/skills/$s ~/.cursor/skills-cursor/$s
done
```

### Current state on this machine

All three resolve to this repo, and edits are live with no sync step:

| Tool | Path | Resolves to |
| --- | --- | --- |
| Claude Code | `~/.claude/skills/u` | `~/promptalias/u` ✅ |
| Codex | `~/.codex/skills/u` | `~/promptalias/u` ✅ |
| Cursor | `~/.cursor/skills-cursor/u` | `~/promptalias/u` ✅ |

The tradeoff: `npx skills` no longer manages these entries, so a future `add` or `update`
may replace the links with copies again. If `/u` stops picking up your edits, that's what
happened — re-run the block above.

### On another machine

Now that this repo is public, install from GitHub instead of a local path:

```sh
npx skills add kishormorol/promptalias --global --all
```

That also sets `Source:` to the repo rather than `local`, which is what makes
`npx skills update` able to pull anything.

## Prompts

| Trigger | Does |
| --- | --- |
| `/u` | Update an existing feature, keeping its tests green |
| `/rv` | Review the last diff for correctness, security, and performance |

The folder name is the trigger, so keep folder names short — `u/` gives you `/u`.

## Adding a prompt

```
mkdir mytrigger && $EDITOR mytrigger/SKILL.md
```

```markdown
---
name: mytrigger
description: Do X. Use when the user asks to …
---

Body of the prompt. $ARGUMENTS interpolates whatever followed the trigger.
```

One rule that matters more than the rest: **write `description` as "do X. Use when Y."**
The `Use when` clause is what the agent matches on to fire the skill implicitly. A bare
label like `"Update a feature"` will never auto-invoke — it only works if you type `/u`
yourself.

## Conventions

- Folder name = trigger. Short and lowercase.
- `name` in frontmatter matches the folder name.
- `$ARGUMENTS` for everything after the trigger; `$1`–`$9` for positional args.
- Keep bodies short enough to read in one screen. If a prompt needs more than that, it
  probably wants to be a real skill with reference files, not a shorthand.
