#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
"""Replace the upstream (Lichii) branding in the source tree.

Reads project/project.json and project/rebrand-rules.json, applies the rules, and writes
project/rebrand-manifest.json listing every path it touched (tools/project/sync_upstream.py
uses that list to resolve merge conflicts in favour of upstream).

    rebrand.py          apply the rules (idempotent)
    rebrand.py --check  exit 1 if "lichii" is left anywhere outside the exception list
    rebrand.py --reset  put every path in the manifest back to the upstream commit from
                        project.json, then apply (needed after changing a name in project.json)
"""
import argparse
import fnmatch
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEFTOVER = re.compile("lichii", re.IGNORECASE)


def load_project():
    pj = json.loads((ROOT / "project/project.json").read_text(encoding="utf-8"))
    pj["repo_slug"] = "/".join(pj["repo_url"].rstrip("/").split("/")[-2:])
    pj["ident_upper"] = re.sub(r"[^A-Za-z0-9]", "_", pj["exe_name"]).upper()
    return pj


def fill(value, pj):
    """Expand @key@ placeholders from project.json ({} is left alone: CMake and fmt use it)."""
    return re.sub(r"@(\w+)@", lambda m: pj[m.group(1)], value)


def rel(path):
    return path.relative_to(ROOT).as_posix()


def matches_any(relpath, patterns):
    return any(fnmatch.fnmatch(relpath, p) or relpath.startswith(p.rstrip("/*") + "/") for p in patterns)


def is_text(path):
    try:
        with open(path, "rb") as f:
            return b"\0" not in f.read(8192)
    except OSError:
        return False


def walk(rules):
    skip = rules["skip_dirs"]
    for dirpath, dirnames, filenames in os.walk(ROOT):
        d = Path(dirpath)
        dirnames[:] = sorted(n for n in dirnames if not matches_any(rel(d / n), skip))
        for name in sorted(filenames):
            yield d / name


def apply_edit(path, src, dst):
    text = path.read_text(encoding="utf-8")
    if src in text:
        path.write_text(text.replace(src, dst), encoding="utf-8")
        return True
    if dst in text:
        return False  # already applied
    sys.exit(f"rebrand: anchor not found in {rel(path)}: {src!r}\n"
             "         upstream changed that line; update project/rebrand-rules.json")


def apply_insert(path, after, line):
    text = path.read_text(encoding="utf-8")
    if line in text.splitlines():
        return False
    lines = text.splitlines(keepends=True)
    for i, l in enumerate(lines):
        if l.rstrip("\n") == after:
            lines.insert(i + 1, line + "\n")
            path.write_text("".join(lines), encoding="utf-8")
            return True
    sys.exit(f"rebrand: anchor line not found in {rel(path)}: {after!r}")


def drop_section(path, heading):
    """Remove a Markdown section from its heading line up to the next heading of the same level."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    level = heading.split(" ", 1)[0]
    try:
        start = next(i for i, l in enumerate(lines) if l.rstrip("\n") == heading)
    except StopIteration:
        return False
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith(level + " ") or (lines[i].startswith("#") and
                    len(lines[i].split(" ", 1)[0]) < len(level))), len(lines))
    path.write_text("".join(lines[:start] + lines[end:]), encoding="utf-8")
    return True


def append_file(path, source):
    """Append source's text once; later runs refresh it in place between marker lines."""
    begin, end = "<!-- emulator-fx:begin -->\n", "<!-- emulator-fx:end -->\n"
    text = path.read_text(encoding="utf-8")
    block = begin + (ROOT / source).read_text(encoding="utf-8") + end
    if begin in text:
        new = text[:text.index(begin)] + block + text[text.index(end) + len(end):]
    else:
        new = text.rstrip("\n") + "\n\n" + block
    if new != text:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def replace_text(path, replacements, line_exceptions):
    text = path.read_text(encoding="utf-8")
    out = []
    changed = False
    for line in text.splitlines(keepends=True):
        if any(e in line for e in line_exceptions):
            out.append(line)
            continue
        new = line
        for src, dst in replacements:
            new = new.replace(src, dst)
        changed |= new != line
        out.append(new)
    if changed:
        path.write_text("".join(out), encoding="utf-8")
    return changed


def do_apply(rules, pj):
    manifest = {"modified": [], "renamed": [], "removed": [], "created": []}
    file_exc = rules["file_exceptions"]
    line_exc = rules["line_exceptions"]

    for r in rules["remove"]:
        p = ROOT / r
        manifest["removed"].append(r)
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    renames = [(x["from"], fill(x["to"], pj)) for x in rules["renames"]]
    # Only the last path component is renamed, deepest paths first, so a renamed directory
    # never invalidates a path below it.
    paths = set()
    for p in walk(rules):
        paths.add(p)
        paths.update(q for q in p.parents if q != ROOT and ROOT in q.parents)
    for p in sorted(paths, key=lambda q: len(q.parts), reverse=True):
        name = p.name
        for src, dst in renames:
            name = name.replace(src, dst)
        if name != p.name:
            target = p.with_name(name)
            p.rename(target)
            manifest["renamed"].append([rel(p), rel(target)])

    for e in rules["edits"]:
        p = ROOT / e["file"]
        if apply_edit(p, e["from"], fill(e["to"], pj)):
            manifest["modified"].append(e["file"])
    for i in rules["inserts"]:
        p = ROOT / i["file"]
        if apply_insert(p, i["after"], i["line"]):
            manifest["modified"].append(i["file"])

    for d in rules.get("drop_sections", []):
        if drop_section(ROOT / d["file"], d["heading"]):
            manifest["modified"].append(d["file"])

    replacements = [(x["from"], fill(x["to"], pj)) for x in rules["replacements"]]
    for p in walk(rules):
        rp = rel(p)
        if matches_any(rp, file_exc) or not is_text(p):
            continue
        if replace_text(p, replacements, line_exc):
            manifest["modified"].append(rp)

    # After the replacements, so the appended project text is never rewritten by them.
    for a in rules.get("appends", []):
        if append_file(ROOT / a["file"], a["source"]):
            manifest["modified"].append(a["file"])

    for ic in rules["icons"]:
        dst = ROOT / fill(ic["to"], pj)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / ic["from"], dst)
        manifest["created"].append(rel(dst))

    # Keep every path ever touched: a second run changes nothing but must not forget the first.
    old_path = ROOT / "project/rebrand-manifest.json"
    if old_path.exists():
        old = json.loads(old_path.read_text(encoding="utf-8"))
        for k in manifest:
            for item in old.get(k, []):
                if item not in manifest[k]:
                    manifest[k].append(item)
    for k in manifest:
        manifest[k] = sorted(set(map(tuple, manifest[k])) if k == "renamed" else set(manifest[k]))
        manifest[k] = [list(x) if isinstance(x, tuple) else x for x in manifest[k]]
    old_path.write_text(json.dumps(manifest, indent=4) + "\n", encoding="utf-8")
    print(f"rebrand: {len(manifest['modified'])} files edited, {len(manifest['renamed'])} renamed, "
          f"{len(manifest['removed'])} removed, {len(manifest['created'])} created (cumulative)")


def do_reset():
    import subprocess
    commit = json.loads((ROOT / "project/project.json").read_text(encoding="utf-8"))["upstream_commit"]
    m = json.loads((ROOT / "project/rebrand-manifest.json").read_text(encoding="utf-8"))

    def in_upstream(path):
        return subprocess.run(["git", "cat-file", "-e", f"{commit}:{path}"], cwd=ROOT,
                              capture_output=True).returncode == 0

    restore = set(m["modified"]) | set(m["removed"]) | {old for old, _ in m["renamed"]}
    drop = set(m["created"]) | {new for _, new in m["renamed"]}
    for path in sorted(drop - restore):
        p = ROOT / path
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    for path in sorted(p for p in restore if in_upstream(p)):
        subprocess.run(["git", "restore", f"--source={commit}", "--worktree", "--", path], cwd=ROOT, check=True)
    (ROOT / "project/rebrand-manifest.json").unlink()


def do_check(rules):
    hits = []
    for p in walk(rules):
        rp = rel(p)
        if LEFTOVER.search(rp):
            hits.append(f"{rp}: (path)")
        if matches_any(rp, rules["file_exceptions"]) or not is_text(p):
            continue
        inside = False  # text appended from project/ (skipped there too) is ours
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            inside = (inside or line == "<!-- emulator-fx:begin -->") and line != "<!-- emulator-fx:end -->"
            if not inside and LEFTOVER.search(line) and not any(e in line for e in rules["line_exceptions"]):
                hits.append(f"{rp}:{n}: {line.strip()[:120]}")
    for h in hits:
        print(h)
    print(f"rebrand --check: {len(hits)} leftover(s)")
    return 1 if hits else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="only look for leftover 'lichii'")
    ap.add_argument("--reset", action="store_true", help="restore upstream state of touched files, then apply")
    args = ap.parse_args()
    rules = json.loads((ROOT / "project/rebrand-rules.json").read_text(encoding="utf-8"))
    if args.check:
        sys.exit(do_check(rules))
    if args.reset:
        do_reset()
    do_apply(rules, load_project())


if __name__ == "__main__":
    main()
