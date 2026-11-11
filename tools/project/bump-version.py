#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Raise VERSION, move the "Unreleased" CHANGELOG.md section under the new version, commit
and tag v<version> (locally; pushing the tag starts the release workflow and is your step).

    bump-version.py major|minor|patch [--no-tag]
"""
import argparse
import datetime
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part", choices=["major", "minor", "patch"])
    ap.add_argument("--no-tag", action="store_true", help="commit only, do not create the tag")
    args = ap.parse_args()

    if git("status", "--porcelain").strip():
        sys.exit("bump-version: working tree is not clean")

    version_file = ROOT / "VERSION"
    major, minor, patch = (int(x) for x in version_file.read_text().strip().split("."))
    if args.part == "major":
        major, minor, patch = major + 1, 0, 0
    elif args.part == "minor":
        minor, patch = minor + 1, 0
    else:
        patch += 1
    version = f"{major}.{minor}.{patch}"
    version_file.write_text(version + "\n")

    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8") if changelog.exists() else "# Changelog\n\n## Unreleased\n"
    head = "## Unreleased\n"
    if head not in text:
        sys.exit("bump-version: CHANGELOG.md has no '## Unreleased' section")
    today = datetime.date.today().isoformat()
    text = text.replace(head, f"{head}\n## v{version} ({today})\n", 1)
    changelog.write_text(text, encoding="utf-8")

    git("add", "VERSION", "CHANGELOG.md")
    git("commit", "-q", "-m", f"Release v{version}")
    if not args.no_tag:
        git("tag", "-a", f"v{version}", "-m", f"Emulator v{version}")
    print(f"bump-version: {version} committed" + ("" if args.no_tag else f", tag v{version} created (not pushed)"))
    print(f"  push with: git push origin main && git push origin v{version}")


if __name__ == "__main__":
    main()
