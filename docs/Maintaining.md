<!--
SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Maintaining Emulator

Emulator is Fritchii `nx2` plus a thin layer of our own. The rule that keeps updates cheap:
**our things live in our files; every change to an upstream file is made by
`tools/project/rebrand.py`**, which can run any number of times.

| What | Where |
|---|---|
| Name, exe names, App-ID, user data folder, repo URLs, last upstream commit | `project/project.json` |
| Version (MAJOR.MINOR.PATCH) | `VERSION` |
| Release notes | `CHANGELOG.md` |
| Icons and logo | `project/branding/` |
| Rebrand rules and exceptions | `project/rebrand-rules.json` |
| Files rebrand.py has touched (used by the sync) | `project/rebrand-manifest.json` (generated) |
| Our CMake settings (version string, infra off) | `project/emulator.cmake` |
| Our AGENTS.md section | `project/AGENTS.project.md` |
| Scripts | `tools/project/`, `scripts/` |

Branches: `upstream-nx2` mirrors `upstream/nx2` and is never edited by hand. `main` is ours;
upstream comes in by merge, never by rebase. Remote `upstream` =
`https://github.com/Frizti/Fritchii.git`, remote `origin` = our repository.

## Take in upstream

```powershell
pwsh tools/project/sync-upstream.ps1              # up to the tip of upstream nx2
pwsh tools/project/sync-upstream.ps1 -To <commit> # up to a given upstream commit
pwsh tools/project/sync-upstream.ps1 -NoBuild     # skip build and tests
```

On Linux/macOS: `tools/project/sync-upstream.sh [--to <commit>] [--no-build]`.

What it does, from a clean `main`:

1. fetches `upstream`, fast-forwards `upstream-nx2`;
2. creates `sync/<yyyymmdd>-<short>` from `main` and merges the upstream commit;
3. conflicts in files only rebrand.py touched are resolved to upstream's side (rebrand.py redoes
   its edits next); `README.md` keeps ours (`merge=ours`). Any other conflict is listed and the
   script stops with the merge in progress: resolve, `git commit`, then run
   `python tools/project/rebrand.py` and `python tools/project/rebrand.py --check` yourself;
4. runs `rebrand.py` and `rebrand.py --check`, writes the new upstream commit into
   `project/project.json`, commits;
5. writes a CHANGELOG proposal to `build/sync-changelog-<short>.md`;
6. builds and runs the unit tests including the Ocarina ones (`scripts/build-windows.ps1 -Tests`).

It never merges into `main` and never pushes. Afterwards:

```powershell
git checkout main
git merge --no-ff sync/<yyyymmdd>-<short>
# paste the CHANGELOG proposal under "## Unreleased" and commit
git push origin main
```

Then re-measure the Ocarina test route and update `docs/oot/baseline.md`.

If `rebrand.py` stops with "anchor not found", upstream changed a line a rule edits: look at the
new line, adjust the rule in `project/rebrand-rules.json`, rerun. If `--check` reports leftovers,
upstream added new "Lichii" text: add a replacement or an exception, rerun.

## Raise the version

```powershell
python tools/project/bump-version.py patch   # or minor / major
```

Updates `VERSION`, moves `## Unreleased` in `CHANGELOG.md` under the new version, commits and
creates the local tag `v<version>`. `--no-tag` skips the tag.

## Make a release

```powershell
python tools/project/bump-version.py minor
git push origin main
git push origin v<version>
```

The tag starts `.github/workflows/release.yml`: Windows x64 build, `emulator-fx-windows-x86_64.zip`,
a **draft** release with the CHANGELOG section as notes. Check it on GitHub and publish it.
Every push also runs `.github/workflows/ci.yml` (rebrand check, Windows build, unit tests).

Build locally: `pwsh scripts/build-windows.ps1 [-Tests] [-Clean] [-QtDir <qt>] [-Clang]`.

## Change name or logo

- Name, exe names, App-ID, user data folder or repo URL: edit `project/project.json`, then

  ```powershell
  python tools/project/rebrand.py --reset   # restore upstream text of every touched file, reapply
  python tools/project/rebrand.py --check
  git add -A; git commit -m "rebrand: rename"
  ```

  Changing `user_data_dir` moves where settings are looked for; copy the old folder over by hand.
- Logo: replace `project/branding/icon.png` (1024x1024), `icon-256.png`, `icon.ico`, `icon.icns`,
  then `python tools/project/rebrand.py`. The current icon is a placeholder.

## Local patches

Changes to emulation code that are not from upstream. Each one is its own commit with a unit test
where possible. On every sync, check whether upstream now has the fix and drop ours if so.

| Commit | Files | Why | Test | Upstream status |
|---|---|---|---|---|
| (none yet) | | | | |

## Deliberately kept upstream names

- Internal identifiers: `YUZU_*` CMake options, the CMake project `yuzu`, targets `yuzu`/`yuzu-cmd`,
  `EDEN_NX2_*`/`EDEN_DKB_*` environment variables, the log file name `eden_log.txt`.
- Copyright and SPDX lines naming Eden, yuzu, Lichii and others.
- Historical documents in `docs/` (Star Fox, Kirby, shader sweep reports) that describe Lichii
  builds; listed as exceptions in `project/rebrand-rules.json`.
