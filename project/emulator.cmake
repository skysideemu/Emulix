# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later

# Project-specific CMake settings. The root CMakeLists.txt includes this file through a line
# that tools/project/rebrand.py inserts right after project(yuzu). Everything that is ours and
# touches the build lives here, so upstream files keep only generated edits.

file(READ "${CMAKE_SOURCE_DIR}/VERSION" EMULATOR_FX_VERSION)
string(STRIP "${EMULATOR_FX_VERSION}" EMULATOR_FX_VERSION)

file(READ "${CMAKE_SOURCE_DIR}/project/project.json" _emulator_fx_json)
string(JSON EMULATOR_FX_DISPLAY_NAME GET "${_emulator_fx_json}" display_name)
string(JSON EMULATOR_FX_UPSTREAM_NAME GET "${_emulator_fx_json}" upstream_name)
string(JSON EMULATOR_FX_UPSTREAM_BRANCH GET "${_emulator_fx_json}" upstream_branch)
string(JSON EMULATOR_FX_UPSTREAM_COMMIT GET "${_emulator_fx_json}" upstream_commit)
string(JSON EMULATOR_FX_DISCORD_APP_ID GET "${_emulator_fx_json}" discord_app_id)
unset(_emulator_fx_json)

string(SUBSTRING "${EMULATOR_FX_UPSTREAM_COMMIT}" 0 7 _emulator_fx_short)
# Shown in the window title, the about dialog and the first log line (through REPO_NAME in
# CMakeModules/GenerateSCMRev.cmake, which rebrand.py points at this variable).
set(EMULATOR_FX_VERSION_STRING
    "${EMULATOR_FX_DISPLAY_NAME} ${EMULATOR_FX_VERSION} (Basis: ${EMULATOR_FX_UPSTREAM_NAME} ${EMULATOR_FX_UPSTREAM_BRANCH}-${_emulator_fx_short})")
unset(_emulator_fx_short)
message(STATUS "[emulator-fx] ${EMULATOR_FX_VERSION_STRING}")

add_compile_definitions(EMULATOR_FX_DISCORD_APP_ID="${EMULATOR_FX_DISCORD_APP_ID}")

# Infrastructure of the predecessor projects is off unless asked for on the command line.
# option() and cmake_dependent_option() keep a value that is already in the cache, so these
# defaults win over upstream's without touching upstream's option() lines.
set(ENABLE_WEB_SERVICE OFF CACHE BOOL "Enable web services (telemetry, etc.)")
set(ENABLE_UPDATE_CHECKER OFF CACHE BOOL "Enable update checker (for Qt and Android)")
set(USE_DISCORD_PRESENCE OFF CACHE BOOL "Enables Discord Rich Presence")
set(YUZU_ROOM OFF CACHE BOOL "Enable dedicated room functionality")
set(YUZU_ROOM_STANDALONE OFF CACHE BOOL "Enable standalone room executable")
