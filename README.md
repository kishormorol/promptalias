# promptalias

**[The visual walkthrough is at kishormorol.github.io/promptalias](https://kishormorol.github.io/promptalias/)** —
what a prompt is, the seven of them, how a typed sentence reaches one, and what is actually
measured.

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
mkdir -p ~/.agents/skills ~/.claude/skills ~/.codex/skills ~/.cursor/skills-cursor
for s in u n rv t d ex p; do
  rm -rf ~/.agents/skills/$s
  ln -s  ~/promptalias/$s          ~/.agents/skills/$s
  ln -sfn ../../.agents/skills/$s  ~/.claude/skills/$s
  ln -sfn ~/.agents/skills/$s      ~/.codex/skills/$s
  ln -sfn ~/.agents/skills/$s      ~/.cursor/skills-cursor/$s
done
```

Re-run it after adding a prompt — a new folder is not linked until you do. The
`~/.claude/skills` line matters: `add` created that entry for the first two prompts and
nothing recreates it for later ones, so a new prompt reaches Codex and Cursor while
staying invisible to Claude Code. Measured on this machine, by hitting exactly that.

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
| `/n` | Build something new that isn't there yet, with tests |
| `/u` | Update an existing feature, keeping its tests green |
| `/t` | Write tests for code that already works |
| `/d` | Track a failure to its root cause and fix it |
| `/rv` | Review the last diff for correctness, security, and performance |
| `/ex` | Explain existing code, changing nothing |
| `/p` | Plan an approach before any code is written |

`/n` and `/u` split on whether the thing exists yet; `/ex` and `/p` are the two that
write no code at all.

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

## Checks

```sh
./scripts/validate.py                        # errors fail, warnings print
./scripts/validate.py --strict               # warnings fail too
python3 -m unittest discover -s scripts      # tests for the validator and the hook
./scripts/check_phrasings.py                 # do the phrasings select their own prompt?
./scripts/check_phrasings.py --record        # rewrite docs/phrasings.md
./scripts/check_page.py                      # does the published page still tell the truth?
```

Python 3, no dependencies, all five run on every push via
[`.github/workflows/validate.yml`](.github/workflows/validate.yml).

It checks the conventions above, and one thing you cannot otherwise catch: a
`description` with no **"Use when"** clause. That prompt installs fine, appears in
`npx skills list`, and then never auto-invokes — nothing anywhere reports it as broken.
It also catches a `name` that drifted from its folder, missing or malformed frontmatter,
a folder with no `SKILL.md`, and frontmatter with an empty body.

`check_phrasings.py` answers a different question: whether two prompts claim the same
words. It runs every quoted example, and every sentence in
[`scripts/probes.json`](scripts/probes.json), back through the hook below, and fails if
one lands on the wrong prompt or ties. Results are recorded in
[`docs/phrasings.md`](docs/phrasings.md). It measures the hook, not the agent — see that
page for what stays unmeasured.

`check_page.py` guards the one thing nothing else can see rotting: [`docs/index.html`](docs/index.html)
is served publicly and states counts and routing outcomes. Add a prompt, rename a probe, or gain a
test, and it would keep telling visitors the old number. So the counts and every routing row on it
are checked against the repo on each push.

## Your own wording (Claude Code only)

A `description` fires a prompt when the agent judges your words to match it. If it keeps
missing on the way *you* phrase things, [`hooks/resolve.py`](hooks/resolve.py) closes the
gap: a `UserPromptSubmit` hook that reads what you typed, matches it against every quoted
example in every `description` plus your own phrases in
[`hooks/vocabulary.json`](hooks/vocabulary.json), and appends one line naming the prompt
it matched. It never blocks, never rewrites, and exits silently on any failure.

```sh
./hooks/resolve.py --explain "make the parser also handle tabs"   # /u  <- "make X also handle Y"
./hooks/resolve.py --list                                         # every phrase, ranked
```

Turn it on by copying the block in
[`hooks/settings.example.json`](hooks/settings.example.json) into `~/.claude/settings.json`.

```json
{ "hooks": { "UserPromptSubmit": [ { "hooks": [
  { "type": "command", "command": "~/promptalias/hooks/resolve.py", "timeout": 5 }
] } ] } }
```

Add your own wording to `hooks/vocabulary.json`, which outranks anything lifted from a
`description`. A lone capital stands for whatever you actually say:

```json
{ "prompts": { "u": ["make X also handle Y", "wire X up to Y"] } }
```

Two things to know before you turn it on. **It is one tool wide.** Codex and Cursor expose
no equivalent, so a phrase that only works through the hook does not travel — which is the
property that killed the compiler in the first place, given up on purpose here. Widen the
`description` first; it costs nothing and works in all three. And **it advises, it does not
decide** — the agent still chooses whether to run the prompt the hook names.

## License

[MIT](LICENSE).
