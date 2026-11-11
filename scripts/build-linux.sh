#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Compile and unit-test check on Linux (CI and sync script). Windows is the shipping target.
#   scripts/build-linux.sh [--tests] [--cli-only]
set -euo pipefail
cd "$(dirname "$0")/.."
tests=OFF qt=ON
for a in "$@"; do
    case "$a" in
        --tests) tests=ON ;;
        --cli-only) qt=OFF ;;
        *) echo "unknown argument: $a" >&2; exit 2 ;;
    esac
done
cmake -S . -B build/linux -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DENABLE_QT=$qt -DYUZU_CMD=ON \
    -DYUZU_TESTS=$tests -DBUILD_TESTING=$tests \
    -DYUZU_USE_BUNDLED_SDL3=ON \
    -DENABLE_WERROR=OFF
targets=(yuzu-cmd)
[ "$qt" = ON ] && targets+=(yuzu)
[ "$tests" = ON ] && targets+=(tests update_checker_tests)
cmake --build build/linux --target "${targets[@]}" --parallel
if [ "$tests" = ON ]; then
    ctest --test-dir build/linux --output-on-failure
    build/linux/bin/tests "[oot]" --reporter compact
fi
