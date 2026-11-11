# AGENTS

See `docs/Coding.md` for technical coding guidance.

Keep comments to a reasonable level. Do not overexplain or add/remove comments from unrelated parts of the codebase.

## Game bug reports

Users report game bugs with Emulator logs (`eden_log.txt`, `eden_log.txt.old`). Each `Booting game: <program id>` line starts a session; the build is on the first line (`Emulator Version: ... | nx2-<sha>`). Known program ids:

| Program id | Game |
|---|---|
| 040074A01BF12000 | Donkey Kong Bananza |
| 040077201BE50000 | Kirby Air Riders |
| 04007C6028AA8000 | Yoshi and the Mysterious Book (demo) |
| 0400D4201C6EA000 | Mario Tennis Fever |
| 0400E88025B1A000 | Star Fox |
| 04007EF01F8AE000 | Fire Emblem: Fortune's Weave |
| 0400C3F00006E000 | Mario Kart World |
| 04008E001F098000 | Nintendo Switch Sports Resort |
| 0400A3A01EE4C000 | Pokémon Pokopia |
| 0400A4802437E000 | Drag x Drive Global Jam |
| 040041E0212AE000 | Fast Fusion |
| 04005B902517C000 | Kirby Air Riders Global Test Ride |
| 040057C02159A000 | Nintendo Switch 2 Welcome Tour |
| 040004F027560000 | Orbitals Global Friends Pass |
| 0400380020056000 | Raiders |
| 0400D1D02399A000 | The Duskbloods network test |
| 0400486024DEC000 | The Legend of Zelda: Ocarina of Time |

Add ids here when a report identifies a new game.

## Debugging tools

Use these before guessing. All are off unless the variable is set; set them in the environment before starting the build under test (see "Builds" below). Read them from the log at `*:Info` unless noted.

| Symptom | Tool | Output |
|---|---|---|
| Wrong image (white, black, missing objects, smearing) | `EDEN_NX2_FRAME_DUMP=<dir>` with `EDEN_NX2_FRAME_DUMP_AT=<seconds>`, `<frame>f` or `file` (captures once `<dir>/capture.now` exists; default 60); add `EDEN_NX2_FRAME_DUMP_SAMPLED=1` for pass inputs | One frame's pass colour targets, dispatch storage images (3D included) and present source; with `_SAMPLED`, every texture each pass samples and each compute shader samples before its first dispatch (`kind: sampled`, with stage (5 = compute), TIC index, 3D and depth included) as `.png` and `.raw.zst`, plus `manifest.jsonl` with shader hashes, formats, addresses and per-channel stats. `python3 -I tools/nx2/frame_dump_index.py <dir>` builds `index.html`. Find the first pass whose output is wrong, then inspect its shaders. |
| Rejected or miscompiled shaders | `EDEN_NX2_SHADER_DUMP=<dir>` | Native programs with `.header.bin` sidecars and `failed-compute-*.env` for failed compute pipelines. Replay offline with `tools/nx2/shader_sweep.py` (see `tools/nx2/shader-sweep.md`). |
| A newly lowered program changes the image | `EDEN_NX2_REJECT_HASH=<hash>,...` (native program keys from shader dump file names, or shader hashes from the frame dump) | Those programs are rejected as if unsupported; the log shows `rejected by EDEN_NX2_REJECT_HASH` per hit. Bisect by halving the list. The key covers the captured code, so recompute it when the capture rules change. |
| Draw and render-state questions | `EDEN_NX2_RENDER_TRACE=1`, filter `*:Info HW.GPU:Debug Render.Vulkan:Debug Shader:Debug` | Per-draw state, rejected stages and zero-format texture descriptors. |
| Video playback | `EDEN_NX2_VDEC_TRACE=1`, `EDEN_NX2_VDEC_DUMP=<dir>` | Decoder submit, decode and composite trace; decoded frames. |
| Performance and frame pacing | `EDEN_NX2_GPU_PROFILE=1`, `EDEN_DKB_FRAME_TRACE=1` | GPU thread time per second by zone; per-present interval, CPU and fence timing. |
| Command corruption or pop-in | `EDEN_NX2_PB_CHECK=1`; A/B with `EDEN_NX2_PB_SNAPSHOT=0` or `EDEN_NX2_FETCH_DRAIN=1` | How many pushbuffer entries change between submit and parse. |
| Split GPU thread races | `EDEN_NX2_SPLIT_CHECK=1` | Reports scheduler use from the wrong thread. |
| Upscaler and DLSS contracts | `EDEN_NX2_DLSS_CONTRACT_TRACE=1` | Inputs and outputs of replaced upscaler networks. |
| Service calls | `EDEN_NX2_IPC_TRACE=1` | IPC command trace. |
| Host crash (log just stops) | Windows minidump in `%LOCALAPPDATA%\CrashDumps\emulator-fx.exe.<pid>.dmp` | Read the exception and stack with the `minidump` Python package, then symbolize with `llvm-symbolizer --obj=emulator-fx.exe --inlines --relative-address <offset>` next to the build's `emulator-fx.pdb`. |

<!-- emulator-fx:begin -->
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
<!-- emulator-fx:end -->
