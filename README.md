# my-prompts

Reusable prompts, written once as [Agent Skills](https://skills.sh) and shared across
Claude Code, Codex, and Cursor. There is deliberately **no build step and no CLI here** —
each prompt is a folder with a `SKILL.md`, and `npx skills` distributes them to every
agent's skills directory.

This is not a text expander and not a config-sync tool. [Espanso](https://espanso.org)
expands triggers into text system-wide in any app, and knows nothing about agent command
formats. [rulesync](https://github.com/dyoshikawa/rulesync), `vsync`, and
`agent-skill-porter` compile or convert configs *between* tools' directories. This repo
skips that whole category: the three tools already read the same `SKILL.md` format, so
there is nothing to compile. See [`docs/prior-art.md`](docs/prior-art.md) for the research
that led here, including the CLI that got designed and then killed.

## Install

```sh
npx skills add . --global --all   # install every skill for every agent
npx skills list -g                # show what's installed where
```

**Re-run `add` after every edit.** `npx skills add` *copies* each `SKILL.md` into a
canonical hub at `~/.agents/skills/<name>/`, then symlinks agent directories at that hub —
it does not link back to this repo. Verified by editing a file here and confirming the hub
did not change. So this repo is the source of truth for *you*, not for the agents, and
there is a sync step after all:

```sh
cd ~/my-prompts && npx skills add . --global --all
```

If you'd rather have true live editing, replace the hub copies with links to this repo:

```sh
rm -rf ~/.agents/skills/u ~/.agents/skills/rv
ln -s ~/my-prompts/u  ~/.agents/skills/u
ln -s ~/my-prompts/rv ~/.agents/skills/rv
```

That makes edits here instant everywhere, at the cost of `npx skills` no longer managing
these two entries — a future `add` or `update` may overwrite the links.

### Where things actually landed

| Tool | Status |
| --- | --- |
| Claude Code | ✅ Verified — `~/.claude/skills/{u,rv}` → `~/.agents/skills/{u,rv}` |
| Codex | ⚠️ `~/.codex/skills/` is empty. The installer classes Codex as a "universal" agent that reads `~/.agents/skills` directly — not verified from here. |
| Cursor | ⚠️ Same. Nothing in `~/.cursor/skills-cursor/`, which is where Cursor keeps its own skills. Installer reports success writing only to the hub. |

If `/u` doesn't resolve in Codex or Cursor, that's the reason — symlink the hub entry into
that tool's own skills directory by hand.

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
