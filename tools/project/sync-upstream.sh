#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Thin wrapper: the logic is in sync_upstream.py (same arguments: --to <commit>, --no-build).
exec python3 -I "$(dirname "$0")/sync_upstream.py" "$@"
