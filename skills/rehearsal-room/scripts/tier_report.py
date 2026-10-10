#!/usr/bin/env python3
"""Tier report for a markdownlint JSON run (the Rehearsal Room).

Reads the JSON that `markdownlint --json -o out.json` writes, then shows what a
Codacy markdownlint scan would likely look like under progressively tuned rule sets,
and which directories to un-exclude first. Read-only; prints Markdown to stdout.

  python3 -I tier_report.py out.json \
      [--tier1 MD013,MD060] [--tier2 MD036,MD033,MD041,MD025,MD024] \
      [--stage "(root),docs,guides,quests"] [--top 8]

Tier 1 = rules dropped first (usually line length and table style: the bulk of the noise).
Tier 2 = Tier 1 plus the extra rules that suit this repo's writing style.
Stage  = top-level directories to bring into scope first (use "(root)" for top-level files).
"""
import argparse
import collections
import json
import sys

C = collections.Counter


def rule(issue):
    return issue["ruleNames"][0]


def top(path):
    return path.split("/")[0] if "/" in path else "(root)"


def summarize(issues, off):
    kept = [i for i in issues if rule(i) not in off]
    fixable = sum(1 for i in kept if i.get("fixInfo"))
    files = len({i["fileName"] for i in kept})
    return kept, fixable, files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path")
    ap.add_argument("--tier1", default="MD013,MD060")
    ap.add_argument("--tier2", default="MD036,MD033,MD041,MD025,MD024")
    ap.add_argument("--stage", default="(root),docs,guides,quests")
    ap.add_argument("--top", type=int, default=8)
    a = ap.parse_args()

    issues = json.load(open(a.json_path, encoding="utf-8"))
    if not issues:
        print("No issues found. Nothing to tune.")
        return 0

    t1 = {r for r in a.tier1.split(",") if r}
    t2 = t1 | {r for r in a.tier2.split(",") if r}
    stage = {s for s in a.stage.split(",") if s}
    all_files = len({i["fileName"] for i in issues})
    descs = {rule(i): i["ruleDescription"] for i in issues}

    print(f"# Rehearsal report\n\nDefault rules: **{len(issues)}** issues in **{all_files}** files.\n")

    print("## Noise by rule (default rules)\n\n| Issues | Rule | What it checks |\n|---:|---|---|")
    for r, n in C(rule(i) for i in issues).most_common(a.top + 4):
        print(f"| {n} | {r} | {descs[r][:60]} |")
    big = C(rule(i) for i in issues)
    share = 100 * sum(big[r] for r in t1) // len(issues)
    print(f"\nTier 1 rules ({', '.join(sorted(t1))}) make up **{share}%** of all issues.\n")

    print("## Tiers\n\n| Tier | Rules turned off | Issues left | Files | Auto-fixable |\n|---|---|---:|---:|---:|")
    for label, off in (("Default", set()), ("Tier 1", t1), ("Tier 2", t2)):
        kept, fx, files = summarize(issues, off)
        pct = f"{100 * fx // max(1, len(kept))}%" if kept else "n/a"
        print(f"| {label} | {', '.join(sorted(off)) or 'none'} | {len(kept)} | {files} | {fx} ({pct}) |")

    kept2, _, _ = summarize(issues, t2)
    print("\n## By directory (Tier 2)\n\n| Directory | Issues | Files | In stage 1 |\n|---|---:|---:|:-:|")
    by_dir = C(top(i["fileName"]) for i in kept2)
    files_dir = collections.defaultdict(set)
    for i in kept2:
        files_dir[top(i["fileName"])].add(i["fileName"])
    for d, n in by_dir.most_common():
        print(f"| {d} | {n} | {len(files_dir[d])} | {'yes' if d in stage else ''} |")

    s1 = [i for i in kept2 if top(i["fileName"]) in stage]
    print(f"\n## Stage 1 ({', '.join(sorted(stage))})\n\n**{len(s1)}** issues in **{len({i['fileName'] for i in s1})}** files at Tier 2.")
    print("\nWorst files to clean first:\n")
    for f, n in C(i["fileName"] for i in s1).most_common(a.top):
        print(f"- {n}  `{f}`")
    return 0


if __name__ == "__main__":
    sys.exit(main())
