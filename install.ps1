#Requires -Version 5.1
<#
.SYNOPSIS
    Installer for Workflow Manager -- clone-path install on Windows.

.DESCRIPTION
    Copies commands, skills, hooks, and rules from the cloned repo into
    the user's ~/.claude/ directory. Checks dependencies and prints
    guided install commands when a dep is missing.

.PARAMETER DryRun
    Print commands that would run without executing.

.NOTES
    FIN-008 -- dependency handling is hybrid: guided messages when deps
    are missing, never auto-installs system-level packages.
#>

param(
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# 1. Detect environment
# ---------------------------------------------------------------------------

$psVersion = $PSVersionTable.PSVersion
Write-Host "PowerShell version: $($psVersion.Major).$($psVersion.Minor)"

# Determine if running on Windows (PS 7+ exposes $IsWindows; PS 5.1 is always Windows)
$onWindows = $true
if ($PSVersionTable.PSVersion.Major -ge 6) {
    $onWindows = $IsWindows
}

if (-not $onWindows) {
    Write-Error "This installer is for Windows only. On macOS/Linux, run: bash install.sh"
    exit 1
}

# ---------------------------------------------------------------------------
# 2. Dependency checks
# ---------------------------------------------------------------------------

# --- git (REQUIRED) ---
$gitCmd = Get-Command git -ErrorAction SilentlyContinue
if (-not $gitCmd) {
    Write-Host ""
    Write-Host "ERROR: git is not installed or not on PATH." -ForegroundColor Red
    Write-Host "  Install Git for Windows via winget: winget install Git.Git"
    Write-Host "  Or download from https://git-scm.com/download/win"
    Write-Host ""
    exit 1
}

Write-Host "git: $($gitCmd.Source)" -ForegroundColor Green

# --- python (OPTIONAL -- only needed for /wm:doc-graph) ---
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
$pythonOk = $false

if ($pythonCmd) {
    $pythonVersionOutput = & python --version 2>&1
    # Output is like "Python 3.11.0"
    if ($pythonVersionOutput -match 'Python (\d+)\.(\d+)') {
        $pyMajor = [int]$Matches[1]
        $pyMinor = [int]$Matches[2]
        if ($pyMajor -gt 3 -or ($pyMajor -eq 3 -and $pyMinor -ge 8)) {
            $pythonOk = $true
            Write-Host "python: $pythonVersionOutput" -ForegroundColor Green
        }
    }
}

if (-not $pythonOk) {
    Write-Host ""
    Write-Host "WARNING: Python 3.x is optional -- required only for /wm:doc-graph." -ForegroundColor Yellow
    Write-Host "  Install via winget: winget install Python.Python.3.11"
    Write-Host "  Or download from https://www.python.org/downloads/"
    Write-Host ""
    # Continue install -- Python is optional per FIN-008
}

# ---------------------------------------------------------------------------
# 3. Determine source and target directories
# ---------------------------------------------------------------------------

$source = $PSScriptRoot

# Prefer $env:HOME (set in sandboxed/test environments) over $env:USERPROFILE
if ($env:HOME) {
    $target = Join-Path $env:HOME '.claude'
} else {
    $target = Join-Path $env:USERPROFILE '.claude'
}

Write-Host ""
Write-Host "Source : $source"
Write-Host "Target : $target"
Write-Host ""

# ---------------------------------------------------------------------------
# 4. Copy files -- four WM-owned subdirectories only
# ---------------------------------------------------------------------------

# Only these four subdirectories are managed by this installer.
# NEVER touch $target\settings.json, CLAUDE.md, or any other user-owned files.
$copyPairs = @(
    @{ Src = Join-Path $source 'commands\wm'; Dst = Join-Path $target 'commands\wm' }
    @{ Src = Join-Path $source 'skills\wm';   Dst = Join-Path $target 'skills\wm'  }
    @{ Src = Join-Path $source 'hooks';        Dst = Join-Path $target 'hooks'       }
    @{ Src = Join-Path $source 'rules';        Dst = Join-Path $target 'rules'       }
)

foreach ($pair in $copyPairs) {
    $src = $pair.Src
    $dst = $pair.Dst

    Write-Host "  $src"
    Write-Host "    -> $dst"

    if (-not $DryRun) {
        if (-not (Test-Path $src)) {
            Write-Host "    SKIP: source directory not found." -ForegroundColor Yellow
            continue
        }

        # Ensure parent directory exists before copying
        $dstParent = Split-Path $dst -Parent
        if (-not (Test-Path $dstParent)) {
            New-Item -ItemType Directory -Path $dstParent -Force | Out-Null
        }

        Copy-Item -Path $src -Destination $dst -Recurse -Force
        Write-Host "    OK" -ForegroundColor Green
    } else {
        Write-Host "    [DRY RUN -- skipped]" -ForegroundColor Cyan
    }
}

# ---------------------------------------------------------------------------
# 5. Executable bits -- no-op on Windows
# ---------------------------------------------------------------------------
# Windows does not use Unix-style executable permission bits; nothing to set.
# If you are using WSL and ran this script instead of install.sh, switch to:
#   bash install.sh
# to get correct chmod +x handling.

# ---------------------------------------------------------------------------
# 6. Final verification and success message
# ---------------------------------------------------------------------------

if (-not $DryRun) {
    $sentinel = Join-Path $target 'commands\wm\status.md'
    if (-not (Test-Path $sentinel)) {
        Write-Host ""
        Write-Host "WARNING: Expected file not found after copy: $sentinel" -ForegroundColor Yellow
        Write-Host "The install may be incomplete. Check source directory structure."
    } else {
        Write-Host ""
        Write-Host "Workflow Manager installed to: $target" -ForegroundColor Green
        Write-Host "Run /wm:status in Claude Code to verify."
    }
} else {
    Write-Host ""
    Write-Host "[DRY RUN] No files were copied. Remove -DryRun to perform the install."
    Write-Host "Target would be: $target"
}
