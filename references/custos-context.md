# custos project context

This plugin is configured for the **Eaprime1/custos** repository (public, GitHub). Read this file before running any Codacy command or editing any file in that repo. Every skill in this plugin links here.

## Repository identity

- Provider `gh`, organization/owner `Eaprime1` (the clone URL is written `eaprime1/custos`), repository `custos`.
- Default branch is `main`. The `pixel8` branch carries the Pixel 8 device layer. Feature branches develop into separate destination repos.
- Inside a clone, the Cloud CLI auto-detects provider/org/repo from the remote. Outside one, pass them explicitly, copying the exact casing that `codacy repositories` shows rather than guessing.

## What is actually in scope for Codacy

custos is a prose-heavy "concept" repo (lore, quests, turn logs, custody records) with a thin layer of real automation. Codacy is deliberately scoped to the automation:

- **Analyzed:** shell scripts in `tools/` and `.locations/`, GitHub Actions workflows in `.github/workflows/`, `.github/scripts/cue-parser.js`, and top-level config (`prima.yaml`, `_config.yml`, `index.html`, JSON/YAML).
- **Excluded by `.codacy.yml`:** every `**/*.md`, PDFs, DOCX and images, plus narrative and working directories (`docs/`, `guides/`, `world/`, `templates/`, `seeds/`, `quests/`, `atelier/`, `vault/`, `device/`, `branch-tracker/`, `prima-clock/`, `moav/`, `returns/`, `queue/`, `pr-journeys/`, `valuation/`, `.claude/`, `.agents/`, `.gemini/`, and similar).
- Treat `.codacy.yml` as the intentional scope strategy. Never propose un-excluding narrative paths or enabling prose/markdown patterns.
- Languages present: Bash, YAML (workflows), one JavaScript file, JSON/YAML config, and one Python helper (`valuation/_helper.py`, inside an excluded directory). There is no `package.json`, no Python project file and no compiled language.
- **Stray content:** an unrelated Apache Airavata project, `airavata-custos/` (Go service plus Next.js app, with its own nested `.git`), can appear untracked in the working tree. It only shares the name "custos". Exclude it from every local analysis and from stack discovery, otherwise Go/TypeScript tooling will be suggested for a repo that does not use them.

## Rules that differ from default Codacy behavior

1. **Codacy reads `.codacy.yml` from `main`, not from the PR head.** A fix to the config on a branch is invisible to Codacy and the PR stays at `action_required`. The fix is a *separate PR to `main`*; after it merges, Codacy re-runs on the blocked PR with no re-push. Before opening a PR from a branch with new paths, check `git diff origin/main -- .codacy.yml`.
2. **A 0-second Codacy result is not a clean result.** When a Codacy check run has `started_at == completed_at`, it is a service-side cached or errored result, not a real analysis. Say so explicitly. Try one reanalysis (`--reanalyze-and-wait`); if it stays at 0 seconds, back it with a local analysis of the changed files and note the cached result in the PR body. custos has merged on that basis when every other check was green and the diff was clean.
3. **The Final Review Gate counts Codacy.** `.github/workflows/final-review.yml` (manual, `strict_mode` defaults to `true`) fails when no Codacy check run exists for the commit, or when any Codacy conclusion is not `success`, `neutral` or `skipped`. So `action_required`, `failure` and in-progress all block. A PR touching only excluded paths may produce no Codacy check run; the documented answer is running the gate with `strict_mode=false`. The repo rule is "resolve Codacy findings before merge" (see `docs/final-review-and-codacy.md`).
4. **Pin third-party actions to a full commit SHA.** This was the baseline Codacy finding (`anthropics/claude-code-action`). Never keep or add an unpinned third-party action, and never disable the pattern that flags it. Look up the real SHA for the release tag; never guess one. First-party `actions/*` use version tags in this repo.
5. **Untrusted text goes through `env:`, not into `run:`.** Existing workflows pass comment bodies and similar input via `env:` variables. Hold new or changed workflows to the same standard, and keep `permissions:` minimal.
6. **Other analyzers also run on PRs** (DeepSource, GitGuardian, `dependency-review`). Do not duplicate their findings in a Codacy summary; mention them only when relevant.

## Environment limits

- Claude sessions have historically not been able to reach Codacy's service from the container (a past session needed the user to paste findings from the PR check). If a Cloud CLI call fails on the network, do not loop on retries. Say plainly that Codacy is unreachable from here and ask the user to paste the findings or run the Cloud CLI from their own machine (Termux, Codespaces or a desktop).
- GitHub GraphQL is also unavailable in these sessions; use the REST API.

## Repo conventions to respect when changing files

- **Deck Master review** (CODEOWNERS, `@eaprime1`) is required for changes under `vault/`, `moav/`, `prima-clock/`, `branch-tracker/`, `world/` and `device/`. Flag any change that touches them. Never edit `vault/` directly; those are origin molds.
- **Before committing**, run the repo's own checks: `bash tools/scan_lexeme.sh` (placeholder scan), `bash tools/validate_json_yaml.sh .` (JSON/YAML must parse; this blocks CI) and, when relevant, `bash tools/prime_check.sh`.
- **PR bodies** need the Intent, What Arrived and Resonance sections; the seal gate parses them. Post Codacy review output as a separate comment and never overwrite the PR body.
- **Custody records** (prima-clock stamps from `date '+%Y%m%d%H%M'`, MOAV carriers) are for formal custody events such as a branch reaching its destination repo. Routine Codacy tuning is not one. Do not create stamps or carriers unless the Shepherd asks.
- **Local Codacy artifacts stay local.** Do not commit `.codacy/codacy.config.json` or generated tool configs; they have no effect on Codacy Cloud and would add noise to a clean repo.

## Tests and coverage reality

- Tests are dependency-free scripts: `bash tools/test_validate_json_yaml.sh` and `bash tools/test_cue_parser.sh` (which runs `tools/test_cue_parser.js` with Node). Neither is wired into a CI workflow, and there is no coverage tooling or report today.
- The only realistic coverage target is `.github/scripts/cue-parser.js`. Quest "Completion Checks" in this repo are deterministic bash commands, so test plans should be written in that style.

## Lessons from the sibling repos (security export, 2026-10-09)

- **Sweep for committed vendored code first.** In `runexusiam`, 480 of 501 critical Codacy items came from a committed virtualenv (about 15,000 tracked files, no `.codacy.yml`). Run the `rehearsal-room` vendor sweep before tuning any repo, and put the exclusions on the default branch.
- **Forks carry upstream findings.** `termux-app` and `knowledge-work-plugins` are forks; their findings are not the owner's code. Exclude or ignore them rather than fix them.
- **Recurring real patterns** across `now`, `hodie` and `mandelbrot`: `curl | bash` installers, GitHub Actions expression injection, `subprocess` without a static string, and `md5` used for non-security hashing. `hodie/scripts/check_workflow_injection.py` already checks for the injection pattern.
- **Existing parts worth porting:** `radix` has a SHA-pinned Codacy SARIF scan workflow and a Review Consolidator that posts one merged check report per PR.

## Roles, for tone

The owner is `eaprime1`, who holds both the Shepherd and Deck Master roles. Keep suggestions concrete and low-ceremony, and ask before any step that changes Codacy Cloud settings or the repo's workflows.
