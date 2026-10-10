---
name: rehearsal-room
description: Rehearses a Codacy scope or rule change locally before it touches the repository or Codacy Cloud. Sweeps for committed vendored directories, runs markdownlint over the Markdown, tiers the noise by rule and directory, and proposes a staged un-exclusion plan. Use when the user wants to try Codacy on prose or Markdown, un-exclude paths from .codacy.yml, estimate how noisy a config change will be, triage a Codacy security export, or says "rehearsal room" or "dry run". Also use for any Codacy rehearsal on the Eaprime1/custos repository or its sibling repos.
license: MIT
metadata:
  author: Eaprime1 (custos overlay)
  version: 1.0.0
---

# Rehearsal Room

> **custos context:** Read [custos-context.md](../../references/custos-context.md) first. The rule that makes this skill worth having: Codacy reads `.codacy.yml` from the default branch, so a wrong scope change is expensive to discover. Rehearse locally, commit nothing, change nothing in Codacy Cloud.

A rehearsal answers three questions with real numbers before anyone opens a PR: what would this scan flag, how much of it is noise, and which paths should come into scope first.

## What this skill never does

- Never edits `.codacy.yml`, opens PRs, imports configs to Codacy Cloud or runs `git rm`. It produces numbers and a proposal; the owner decides.
- Never commits rehearsal output. Work in a scratch directory.

## Workflow

```
Rehearsal Progress:
- [ ] Step 0: Vendor sweep
- [ ] Step 1: Baseline run (default rules)
- [ ] Step 2: Tier the noise
- [ ] Step 3: Choose stage-1 paths
- [ ] Step 4: Write the proposal
```

### Step 0: Vendor sweep (always first)

Run `bash scripts/vendor_sweep.sh` from the repository root. It lists committed directories such as `venv/`, `node_modules/`, `site-packages/`, `vendor/`, `dist/` and `build/`, with file counts, and suggests exclude globs.

Do this before tuning anything. In the first rehearsal, 480 of 501 critical security items came from a committed virtualenv, which is 96% of the export and had nothing to do with the repo's own code. See [first-run-2026-10-09.md](references/first-run-2026-10-09.md).

### Step 1: Baseline run

markdownlint is quick: a few seconds for several hundred files. In a scratch directory:

```bash
npm init -y && npm i markdownlint-cli
cd <repo> && <scratch>/node_modules/.bin/markdownlint '**/*.md' --ignore node_modules --json -o <scratch>/default.json
```

Use the default rules so the numbers show the worst case. If the Codacy Analysis CLI is installed and works in this session, prefer `codacy-analysis analyze` with its markdownlint tool for the closest match to Codacy; Codacy's enabled patterns and tool version may differ from plain markdownlint, so treat the numbers as an estimate and say so.

### Step 2: Tier the noise

```bash
python3 -I scripts/tier_report.py <scratch>/default.json --stage "(root),docs,guides,quests"
```

Defaults: Tier 1 drops line length (`MD013`) and table style (`MD060`); Tier 2 also drops style rules that fight narrative or lore writing (`MD036`, `MD033`, `MD041`, `MD025`, `MD024`). Override with `--tier1` and `--tier2` when the repo's voice differs. Report the share of issues the Tier 1 rules account for, the issues left per tier, and how many of those are auto-fixable (`markdownlint --fix`).

### Step 3: Choose stage-1 paths

Bring paths into scope in this order, and explain each choice:

1. **Living instruction documents** that people and agents read and edit (root files like `CLAUDE.md` and `README.md`, `docs/`, `guides/`, `quests/`).
2. **Narrative that is still growing** (for example chronicles and lore).
3. **Append-only history** (turn logs, PR journeys) last, or never. Rarely edited files cost the most to bring in and give the least back.

Expect a one-time cost: Codacy re-analyzes everything after a tool or scope change on the next commit, then scans only changed files. A large first pass of pre-existing issues is normal. Offer `markdownlint --fix` on the auto-fixable share as a separate, reviewable cleanup PR so the baseline shrinks before the scope change lands.

### Step 4: Write the proposal

Deliver a short report: the vendor sweep result, the tier table, the stage-1 list with issue counts, the worst files, and the exact `.codacy.yml` change (only the lines to remove from `exclude_paths`). State clearly that the change must go to the default branch in its own PR, and that the Markdown tool's rules are set in Codacy's tool settings, which `configure-codacy-cloud` handles after the owner agrees.

## Triaging a Codacy security export

When the user supplies a Codacy security CSV (columns include `repository`, `filepath`, `pattern_internal_id`, `severity`):

1. Split vendored paths from the rest (the same name list as the vendor sweep). Report both counts.
2. Mark repositories that are forks of someone else's project; those findings are upstream code, so exclude or ignore them rather than fix them.
3. Group what remains by pattern and give each group a plain-language verdict: likely real, likely benign, or needs a human look. Say which verdicts come from reading the code and which are guesses.
4. Recurring real patterns worth a repo-wide rule: `curl | bash` installers, GitHub Actions expression injection (move `${{ }}` into `env:`), `subprocess` calls without a static string, and `md5` used for non-security hashing (`hashlib.md5(usedforsecurity=False)` or switch to SHA-256).
