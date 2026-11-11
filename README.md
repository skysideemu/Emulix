<!--
SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Emulator

Experimental Nintendo Switch and Switch 2 emulator for Windows x64.

Emulator is a standalone, rebranded build of [Fritchii](https://github.com/Frizti/Fritchii)
(branch `nx2`), which adds Switch 2 titles to the yuzu -> Eden -> Eglantine -> Lichii line of
emulators. Emulation work comes from those projects; this repository adds its own name, version
numbers, release process and game-specific tuning, and takes new upstream versions in with one
command (see [docs/Maintaining.md](docs/Maintaining.md)).

The version shown in the window title, the about dialog and the first log line reads
`Emulator <version> (Basis: Fritchii nx2-<upstream commit>)`.

Emulator keeps its settings, data and logs in `%APPDATA%\emulator-fx`, so it can be installed next
to Eden, Lichii or Fritchii without touching their data. A `user` folder next to
`emulator-fx.exe` makes it portable.

It ships no keys, firmware or games. Use only games you own.

## Build on Windows

Requirements:

- Visual Studio 2022 with "Desktop development with C++" (MSVC; clang-cl also works)
- CMake 3.31 or newer, Ninja, Git, Python 3
- Vulkan SDK (`tools/windows/install-vulkan-sdk.ps1`, as administrator)
- Qt 6 is downloaded during configure, or pass an installed Qt 6 (msvc2022_64) with `-QtDir`

```powershell
git clone <repo-url> Emulator
cd Emulator
pwsh scripts/build-windows.ps1            # -> build\windows\bin\emulator-fx.exe, emulator-fx-cli.exe
pwsh scripts/build-windows.ps1 -Tests     # also build and run the unit tests
```

The upstream build guide ([docs/Build.md](docs/Build.md), [docs/Deps.md](docs/Deps.md),
[docs/Options.md](docs/Options.md)) still applies; the script above wraps it.

Build options specific to this project (all off by default): `ENABLE_WEB_SERVICE`,
`ENABLE_UPDATE_CHECKER` (checks the repository in `project/project.json`),
`USE_DISCORD_PRESENCE` (needs a `discord_app_id` in `project/project.json`).

## License

GPL-3.0-or-later, see [LICENSE.txt](LICENSE.txt). Third-party components keep their own licenses
(`LICENSES/`, `.reuse/dep5`). Copyright notices of the upstream projects remain in effect.

"Nintendo Switch" is a trademark of Nintendo. This project is not affiliated with Nintendo.
