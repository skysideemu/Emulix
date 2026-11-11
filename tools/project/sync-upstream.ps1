# SPDX-FileCopyrightText: Copyright 2026 Emulator contributors
# SPDX-License-Identifier: GPL-3.0-or-later
# Thin wrapper: the logic is in sync_upstream.py (same arguments, e.g. -To <commit>, -NoBuild).
param([string]$To, [switch]$NoBuild)
$ErrorActionPreference = "Stop"
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command python3 -ErrorAction Stop }
$a = @()
if ($To) { $a += @("--to", $To) }
if ($NoBuild) { $a += "--no-build" }
& $py.Source -I (Join-Path $PSScriptRoot "sync_upstream.py") @a
exit $LASTEXITCODE
