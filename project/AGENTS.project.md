## Emulator project rules

This tree is "Emulator", a standalone fork of [Fritchii](https://github.com/Frizti/Fritchii)
branch `nx2` (fork chain yuzu -> Eden -> Eglantine -> Lichii -> Fritchii). The text above this
section is upstream's, adjusted by `tools/project/rebrand.py`; this section comes from
`project/AGENTS.project.md`. Edit it there, never here.

- Upstream files change only through `tools/project/rebrand.py` and its rules in
  `project/rebrand-rules.json`. Our own code lives in our own files (`project/`,
  `tools/project/`, `scripts/`, `docs/Maintaining.md`, `docs/oot/`).
- Exception: a fix in emulation code (`src/core`, `src/video_core`, `src/dynarmic`,
  `src/shader_recompiler`, `src/audio_core`) is a hand edit. One commit per fix, a unit test where
  possible, and an entry under "Local patches" in `docs/Maintaining.md`.
- Do not rename internal identifiers (`YUZU_*` options, the CMake project `yuzu`, `EDEN_NX2_*`
  variables); they keep upstream merges clean.
- Keep SPDX and copyright headers, `LICENSES/` and `.reuse/dep5` as they are. New files get an
  SPDX header (GPL-3.0-or-later).
- No keys, firmware, game files, or links to them.
- Never push, publish tags or rewrite published history without the owner's okay.

### Before writing a fix

1. Check upstream first: `Frizti/Fritchii` and `Djihads80/Eglantine`, branch `nx2`, open and closed
   PRs, unmerged branches and issues (`gh pr list -R <repo> --state all`, `gh pr diff <n>`).
2. If upstream has it: take it with `tools/project/sync-upstream.ps1` or port it and cite the source
   in the commit message.
3. Otherwise write the smallest fix of the root cause the logs show. No special cases by program id
   when a generally correct fix exists.

### Builds

- The shipping target is Windows x64: `pwsh scripts/build-windows.ps1 [-Tests] [-Clean]`
  -> `build\windows\bin\emulator-fx.exe` and `emulator-fx-cli.exe`.
- User data lives in `%APPDATA%\emulator-fx` (or `user\` next to the exe for a portable install);
  the log is `log\eden_log.txt` there.
- The owner tests on his Windows PC and sends logs back. Tell him exactly which build to start,
  with which environment variables, and what to play.
