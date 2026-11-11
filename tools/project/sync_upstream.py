#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Take over a new upstream (Fritchii nx2) state with one command.

Steps (docs/Maintaining.md has the long form):
  a) abort unless the working tree is clean and the current branch is main
  b) fetch upstream, fast-forward the upstream-nx2 mirror branch
  c) create sync/<date>-<short> from main and merge the target commit into it
  d) resolve conflicts in files only rebrand.py touched in favour of upstream;
     list every other conflict and stop (the merge stays in progress for you)
  e) run rebrand.py and rebrand.py --check
  f) record the upstream commit in project.json; write a CHANGELOG proposal
  g) build and run the unit tests (incl. the Ocarina ones); never merge or push

    sync_upstream.py [--to <commit>] [--no-build]
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MIRROR = "upstream-nx2"


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True)
    if check and r.returncode != 0:
        sys.exit(f"sync: git {' '.join(args)} failed:\n{r.stderr.strip()}")
    return r.stdout.strip()


def is_ancestor(a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT).returncode == 0


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, cwd=ROOT, **kw).returncode


def rebrand_paths():
    m = json.loads((ROOT / "project/rebrand-manifest.json").read_text(encoding="utf-8"))
    paths = set(m["modified"]) | set(m["created"]) | set(m["removed"])
    for old, new in m["renamed"]:
        paths.update((old, new))
    return paths


def resolve_conflicts(target):
    conflicted = [p for p in git("diff", "--name-only", "--diff-filter=U").splitlines() if p]
    if not conflicted:
        return []
    ours = rebrand_paths()
    manual = []
    for path in conflicted:
        if not any(path == p or path.startswith(p + "/") for p in ours):
            manual.append(path)
            continue
        if subprocess.run(["git", "cat-file", "-e", f"{target}:{path}"], cwd=ROOT, capture_output=True).returncode == 0:
            git("checkout", target, "--", path)
        else:
            git("rm", "-q", "-f", "--", path)
        print(f"sync: {path}: rebrand-only file, took upstream's version")
    return manual


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--to", metavar="COMMIT", help="stop at this upstream commit instead of the branch tip")
    ap.add_argument("--no-build", action="store_true", help="skip step g")
    args = ap.parse_args()

    project = json.loads((ROOT / "project/project.json").read_text(encoding="utf-8"))
    upstream_branch = project["upstream_branch"]

    # a)
    if git("status", "--porcelain"):
        sys.exit("sync: working tree is not clean")
    if git("rev-parse", "--abbrev-ref", "HEAD") != "main":
        sys.exit("sync: run this from branch main")

    # b)
    if "upstream" not in git("remote").split():
        git("remote", "add", "upstream", project["upstream_repo"])
    print(f"sync: fetching upstream/{upstream_branch}", flush=True)
    git("fetch", "upstream", upstream_branch)
    remote_tip = git("rev-parse", f"upstream/{upstream_branch}")
    if git("rev-parse", "--verify", "--quiet", MIRROR, check=False) and not is_ancestor(MIRROR, remote_tip):
        sys.exit(f"sync: {MIRROR} is not an ancestor of upstream/{upstream_branch}; upstream rewrote history")
    git("branch", "-f", MIRROR, remote_tip)

    target = git("rev-parse", "--verify", args.to + "^{commit}") if args.to else remote_tip
    if not is_ancestor(target, remote_tip):
        sys.exit(f"sync: {target} is not on upstream/{upstream_branch}")
    short = target[:7]
    old_base = project["upstream_commit"]
    if is_ancestor(target, "HEAD"):
        sys.exit(f"sync: main already contains upstream {short}")

    # c)
    branch = f"sync/{datetime.date.today():%Y%m%d}-{short}"
    git("checkout", "-q", "-b", branch)
    print(f"sync: merging upstream {short} into {branch}", flush=True)
    merge = subprocess.run(["git", "merge", "--no-edit", "-m", f"Merge upstream {upstream_branch} {short}", target],
                           cwd=ROOT, text=True, capture_output=True)

    # d)
    if merge.returncode:
        manual = resolve_conflicts(target)
        if manual:
            print("sync: conflicts that need a human (merge left in progress):")
            for p in manual:
                print("   ", p)
            sys.exit(1)
        git("commit", "-q", "--no-edit")

    # e)
    if run([sys.executable, "-I", "tools/project/rebrand.py"]):
        sys.exit("sync: rebrand.py failed (see above; fix project/rebrand-rules.json, then rerun)")

    # f)
    project["upstream_commit"] = target
    (ROOT / "project/project.json").write_text(json.dumps(project, indent=4) + "\n", encoding="utf-8")
    log = git("log", "--no-merges", "--format=- %s (%h)", f"{old_base}..{target}")
    proposal = ROOT / "build" / f"sync-changelog-{short}.md"
    proposal.parent.mkdir(exist_ok=True)
    proposal.write_text(f"### Upstream {upstream_branch} {old_base[:7]}..{short}\n{log}\n", encoding="utf-8")

    if run([sys.executable, "-I", "tools/project/rebrand.py", "--check"]):
        sys.exit("sync: leftovers after rebrand; add rules, rerun rebrand.py, then commit")
    git("add", "-A")
    if git("status", "--porcelain"):
        git("commit", "-q", "-m", f"sync: rebrand after upstream {short}")

    # g)
    if not args.no_build:
        if os.name == "nt":
            shell = "pwsh" if subprocess.run(["where", "pwsh"], capture_output=True).returncode == 0 else "powershell"
            rc = run([shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/build-windows.ps1", "-Tests"])
        else:
            rc = run(["bash", "scripts/build-linux.sh", "--tests"])
        if rc:
            sys.exit("sync: build or tests failed; fix on this branch, then merge by hand")

    print(f"""
sync: done on branch {branch}
  upstream {old_base[:7]} -> {short}, {len(log.splitlines())} new upstream commits
  CHANGELOG proposal: {proposal.relative_to(ROOT)} (paste under '## Unreleased')
  next: review, then  git checkout main && git merge --no-ff {branch}
        and re-measure the Ocarina test route (docs/oot/baseline.md).
  Nothing was merged into main or pushed.""")


if __name__ == "__main__":
    main()
