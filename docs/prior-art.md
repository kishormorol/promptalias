# Why this repo is a folder of SKILL.md files and not a CLI

**Last checked: 17 August 2026.** Everything below rots. Re-check before trusting it.
Measured claims about how the phrasings route live in
[`phrasings.md`](phrasings.md), regenerated from the code rather than written by hand.

**`promptalias` is the name; the compiler is not what got built.** The original plan was a
CLI: a single dense YAML file — twenty two-character aliases as twenty lines — compiled
into native command files for Claude Code, Codex, and Cursor. Research killed that plan
twice, on two different grounds, before any code was written. The name stayed; what ships
under it is this folder of `SKILL.md` files.

This note records what was found, so the decision is re-checkable when the formats change.

Full design review lives in the Claude Design project
*"Design review: adapter targets and compiler strategy"*.

---

## Part 1 — State of each tool's command format

The premise of the original brief was that these three formats had diverged and needed a
compiler to bridge them. They had in fact converged on the open **Agent Skills** standard:
a directory containing `SKILL.md` with `name` and `description` YAML frontmatter. All
three tools read it. That single fact is what removed most of the need for a tool.

| Tool | Legacy command path | State as of 2026-08-17 |
| --- | --- | --- |
| **Claude Code** | `.claude/commands/*.md`, `$ARGUMENTS` and `$1`–`$9` | Commands were unified into skills. `.claude/skills/<name>/SKILL.md` is the recommended path. Old command files still work. |
| **Codex** | `~/.codex/prompts/*.md` (or `$CODEX_HOME/prompts/`), invoked `/prompts:name` | Officially **deprecated** in favour of skills, and there are open reports of prompts not loading at all in recent CLI builds. Global scope only — no project scope. |
| **Cursor** | `.cursor/commands/*.md`, `$1`/`$2` args | Commands still work. They take **no frontmatter** — so there is nowhere for a `description` to go. Project skills live in `.cursor/skills/`; the *global* directory is `~/.cursor/skills-cursor/`, not `~/.cursor/skills/`, which does not exist. Ships a `/migrate-to-skills` command. |

Three corrections this forced on the original brief:

1. Cursor commands accept no frontmatter, so `description` cannot be expressed there.
   Any cross-tool compiler must demote it to a body line and report the demotion.
2. Codex prompts are worse than "deprecated" — there are regressions where they stop
   being discovered entirely. Writing into `~/.codex/prompts/` is building on sand.
3. There is a fourth target the brief never listed — `SKILL.md` — and it is the only one
   all three tools agree on.

### Watch for these signs that this note has rotted

- The three tools diverge again on `SKILL.md` frontmatter. Convergence is about a year
  old; it is a convention, not a standard body.
- Codex regains project-scoped prompts or skills.
- Cursor commands gain frontmatter support.

### Links

- Codex custom prompts — <https://developers.openai.com/codex/custom-prompts>
- Codex prompt-discovery regression — <https://github.com/openai/codex/issues/15941>
- `npx skills` / skills.sh — <https://skills.sh>

---

## Part 2 — Prior art

Two research passes. The first killed the tool on **scope overlap**. The second killed it
again on **commodity**: every hard part except the source file format is already shipped,
in more than one tool.

### First pass

| Project | What it does | Overlap |
| --- | --- | --- |
| [rulesync](https://github.com/dyoshikawa/rulesync) | 20+ tools. Generates rules, MCP configs, commands, subagents, and skills from `.rulesync/`. Has `--dry-run`, `--check` for CI, global mode, per-target selection. | ~90% of the planned v0.1 |
| [npx skills (skills.sh)](https://skills.sh) | Installs and updates `SKILL.md` packages into each agent's directory, **symlinked** per tool. Registry, search, `--json`, CI-friendly. | Owns the "one file, all tools" job outright |
| [ai-rules-sync](https://github.com/lbb00/ai-rules-sync) | One normalised IR, then render per target. Untranslatable constructs surface as warnings rather than silent drops — that discipline is the part worth stealing. | Architecture, not scope |
| [Espanso](https://espanso.org) | System-wide trigger → text expansion. Types characters into any app; does not register native commands or understand tool-specific placeholder syntax. | None — genuinely orthogonal |

⚠️ The first pass recorded `ai-rules-sync` as "rules only." That is probably now stale —
the repo advertises rules, skills, **commands**, and subagents across eight tools. Only
the repo description was checked, not the README. Verify before relying on it.

### Second pass

These three were named in the original brief but never examined in the first pass.

| Project | What it does | Overlap |
| --- | --- | --- |
| [agent-skill-porter](https://github.com/hatappo/agent-command-sync) *(formerly `agent-command-sync`, CLI `sk`)* | Seven agents — Claude Code, Gemini CLI, Codex, OpenCode, Copilot, Cursor, Chimera Hub. Handles both `SKILL.md` directories and single-file commands. Already does placeholder translation across dialects: `$ARGUMENTS` ↔ `{{args}}`, `` !`cmd` `` ↔ `!{cmd}`, `@path` ↔ `@{path}`. Ships `-n` dry-run, `--no-overwrite`, `--sync-delete`, provenance via `_from`. **No source file** — it converts bidirectionally between tools' existing directories. | Owns the translation layer |
| [ccmd](https://github.com/gifflet/ccmd) | Claude Code exclusive; no Codex, no Cursor. A package manager — `ccmd install <repo>` pulls commands from Git against `ccmd.yaml` + `ccmd-lock.yaml`. Distribution, not authoring. | None. Not a competitor. |
| `ai-command-library` | **Could not be found.** Two searches returned nothing matching the name — misremembered, renamed, or private. Do not carry an unverifiable name in a prior-art list. | Unknown; probably nonexistent |

And one the brief never mentioned, which lands closest of all:

| Project | What it does | Overlap |
| --- | --- | --- |
| [vsync](https://github.com/nicepkg/vsync) | Syncs Skills, MCP, Agents, and **Commands** across Claude Code, Cursor, OpenCode, Codex from `.vsync.json`. Dry-run, hash-based change detection, Safe Mode by default with opt-in Prune Mode, variable translation. Watch mode planned for v1.3. Its config names a source **tool** (`"source_tool": "claude-code"`), not a source **file**, so it inherits folder-per-command authoring. | The entire non-negotiables list |

Also in this space, not examined in depth:
[agent-rules-sync](https://github.com/dhruv-anand-aintech/agent-rules-sync) — real-time
sync of rules, skills, settings, and MCP across five tools.

### The commodity table

Every requirement from the original brief, against who already ships it:

| Requirement | Already shipped in |
| --- | --- |
| Placeholder translation per target | agent-skill-porter, vsync, rulesync |
| `--dry-run` without touching disk | agent-skill-porter (`-n`), vsync, rulesync |
| Manifest + stale cleanup | agent-skill-porter (`--sync-delete`), vsync (hash detection, Prune Mode) |
| Never clobber hand-written files | agent-skill-porter (`--no-overwrite`), vsync (Safe Mode, default) |
| `sync --watch` | Nobody yet — vsync has it on the v1.3 roadmap |
| **Terse single source file** (20 aliases = 20 lines) | **Nobody. The only row left.** |

Every tool checked is either folder-per-artifact authoring or tool-to-tool conversion
with no authoring layer at all. Not one lets you write twenty two-character aliases as
twenty lines. The differentiator survives — it is just now the *only* thing that does,
and it is one YAML parser wide.

---

## Part 3 — A flaw in the original design, recorded

If v0.1 targets `SKILL.md`, the planned **Resolver unit is vestigial.**

The agent matches the trigger from the folder name; the tool never sees the input string.
That leaves `resolve(input: string): Match | null` with exactly one caller — `list` — and
the "keep it swappable for a fuzzy resolver later" argument collapses, because a fuzzy
resolver has to sit in the agent's prompt path. In Claude Code that means the
`UserPromptSubmit` hook, which the brief explicitly placed out of scope.

A resolver is load-bearing only in a design that intercepts input. A `SKILL.md` compiler
doesn't.

---

## When to revisit

Build the compiler if any of these become true:

- **Volume.** Past roughly twenty prompts, the folder-per-alias tax starts to bite, and a
  terse-YAML compiler earns its keep. *Seven as of 17 Aug 2026 — `/n /u /t /d /rv /ex /p`.
  Not close.*
- **Divergence.** The three tools split again on `SKILL.md` frontmatter, restoring the
  translation problem that `npx skills` currently makes moot.
- **Reach.** You want the same triggers outside coding agents — Slack, email, docs. That
  is Espanso's job, and a different tool, not this one.
- **Your own vocabulary.** *(Added 17 Aug 2026 — a trigger this list originally missed.)*
  You want your own keywords and sentences to select a prompt, rather than typing the
  trigger or hoping the `description` matches. This is the one case Part 3 rules out by
  assumption: it concluded the Resolver was vestigial *because* a `SKILL.md` compiler
  never sees the input string. A design that intercepts input revives it. In Claude Code
  that is the `UserPromptSubmit` hook; Codex and Cursor expose no equivalent, so anything
  built here is single-tool and forfeits the cross-tool property that killed the
  compiler in the first place. Try richer `Use when` clauses before writing the hook —
  they cost nothing and work in all three tools.

  **Acted on, 17 Aug 2026, in that order.** The clauses were widened first (878882a).
  The hook followed as `hooks/resolve.py`, taking its phrases from the descriptions
  themselves plus `hooks/vocabulary.json`, so the two cannot drift apart. The cost was
  paid knowingly and is exactly as stated: a phrase that only works through the hook
  does not travel to Codex or Cursor. It advises rather than decides — one line of
  context naming the prompt it matched — which keeps the failure mode to a missed
  suggestion rather than a hijacked turn.

  This does not revive the compiler either. The Resolver is real now, but it lives in a
  hook rather than in a build step, and it reads the `SKILL.md` files as they are. There
  is still nothing to compile.

Until then: one folder per prompt, installed with `npx skills add . --global --all`.

One correction to the argument that killed the compiler, measured after the fact. The kill
rationale claimed `npx skills` symlinks the source file so edits are live everywhere "with
no sync step at all," and that this was the part a compiler could never beat. **That is
false.** `add` copies into a hub at `~/.agents/skills/` and symlinks agent directories at
the hub, so edits here are invisible until `add` is re-run — the same re-run-after-edit tax
the compiler would have carried. It also silently missed two of the three tools, reporting
success for Codex and Cursor while writing to neither. Live editing in all three took a
hand-written symlink chain (see the README).

This does not revive the compiler: the tax is one command, and rulesync and vsync still
cover the rest of the scope. But the case was argued on a claim that turned out to be
marketing rather than behaviour, and the record should say so.
