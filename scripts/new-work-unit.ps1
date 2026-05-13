param(
    [Parameter(Mandatory = $true)]
    [string]$Name,

    [switch]$NoBranch,

    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    & git -c "safe.directory=$repoRoot" @args
}

function Convert-ToSlug([string]$value) {
    $slug = $value.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    if (-not $slug) {
        throw "Work-unit name must contain letters or numbers."
    }
    return $slug
}

$initialSafeDirectory = ((Get-Location).ProviderPath -replace '\\', '/')
$repoRoot = git -c "safe.directory=$initialSafeDirectory" rev-parse --show-toplevel
if (-not $repoRoot) {
    throw "Could not find git repository root."
}
$repoRoot = ($repoRoot -replace '\\', '/')
Set-Location $repoRoot

$dirty = Invoke-Git status --short
if ($dirty -and -not $AllowDirty) {
    throw "Working tree has uncommitted changes. Commit/stash first, or pass -AllowDirty intentionally."
}

$slug = Convert-ToSlug $Name
$branch = "codex/$slug"
$date = Get-Date -Format "yyyy-MM-dd"
$docDir = Join-Path $repoRoot "docs/work-units"
$docPath = Join-Path $docDir "$date-$slug.md"

New-Item -ItemType Directory -Force -Path $docDir | Out-Null

if (-not $NoBranch) {
    $current = Invoke-Git branch --show-current
    if ($current -ne $branch) {
        Invoke-Git switch -c $branch
    }
}

if (Test-Path $docPath) {
    throw "Work-unit doc already exists: $docPath"
}

@"
# Work Unit: $Name

## Goal


## Scope

- 

## Out Of Scope

- 

## Plan

- [ ] Add or update tests first
- [ ] Implement the smallest change that satisfies this work unit
- [ ] Run verification
- [ ] Update docs/tasks if needed
- [ ] Open a draft PR

## Verification

- [ ] `git diff --check`
- [ ] Backend tests, if backend changed
- [ ] Worker tests, if worker changed
- [ ] Docker smoke test, if runtime changed

## Notes


"@ | Set-Content -Path $docPath -Encoding UTF8

Write-Host "Created work-unit doc: $docPath"
if (-not $NoBranch) {
    Write-Host "Current branch: $branch"
}
