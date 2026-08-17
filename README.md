# my-prompts

Reusable prompts, written once as [Agent Skills](https://skills.sh) and shared across
Claude Code, Codex, and Cursor. There is deliberately **no build step and no CLI here** —
each prompt is a folder with a `SKILL.md`, and `npx skills` symlinks them into every
agent's skills directory, so editing a file here is live in all three tools immediately.

This is not a text expander and not a config-sync tool. [Espanso](https://espanso.org)
expands triggers into text system-wide in any app, and knows nothing about agent command
formats. [rulesync](https://github.com/dyoshikawa/rulesync), `vsync`, and
`agent-skill-porter` compile or convert configs *between* tools' directories. This repo
skips that whole category: the three tools already read the same `SKILL.md` format, so
there is nothing to compile. See [`docs/prior-art.md`](docs/prior-art.md) for the research
that led here, including the CLI that got designed and then killed.

## Install

```sh
npx skills add ./my-prompts   # symlinks every skill into each agent's directory
npx skills list               # show what's installed where
npx skills update             # pull upstream changes
```

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
