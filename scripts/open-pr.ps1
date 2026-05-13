param(
    [Parameter(Mandatory = $true)]
    [string]$Title,

    [Parameter(Mandatory = $true)]
    [string]$Body,

    [Parameter(Mandatory = $true)]
    [string]$CommitMessage,

    [string]$Base = "main",

    [string]$WorkUnit,

    [switch]$SkipVerification,

    [switch]$AllowLargePr
)

$ErrorActionPreference = "Stop"

function Run-Step([string]$label, [scriptblock]$command) {
    Write-Host "==> $label"
    & $command
}

function Invoke-Git {
    & git -c "safe.directory=$repoRoot" @args
}

function Resolve-GhPath {
    $command = Get-Command gh -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        "C:\Program Files\GitHub CLI\gh.exe",
        "C:\Program Files (x86)\GitHub CLI\gh.exe",
        "$env:LOCALAPPDATA\GitHubCLI\gh.exe",
        "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

function Invoke-Gh {
    & $script:GhPath @args
}

$script:GhPath = Resolve-GhPath
if (-not $script:GhPath) {
    throw "GitHub CLI 'gh' is not installed or not on PATH."
}

$initialSafeDirectory = ((Get-Location).ProviderPath -replace '\\', '/')
$repoRoot = git -c "safe.directory=$initialSafeDirectory" rev-parse --show-toplevel
if (-not $repoRoot) {
    throw "Could not find git repository root."
}
$repoRoot = ($repoRoot -replace '\\', '/')
Set-Location $repoRoot

$branch = Invoke-Git branch --show-current
if (-not $branch) {
    throw "No current Git branch found."
}

if ($branch -eq "main" -or $branch -eq "master") {
    throw "Refusing to open a PR directly from $branch. Create a codex/<task> branch first."
}

if ($branch -notlike "codex/*") {
    throw "Branch must use codex/<task-name> for conservative work units. Current branch: $branch"
}

$remote = Invoke-Git remote get-url origin
if (-not $remote) {
    throw "No git remote named origin is configured."
}

if (-not $WorkUnit) {
    $candidate = Get-ChildItem -Path "docs/work-units" -Filter "*.md" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if ($candidate) {
        $WorkUnit = $candidate.FullName
    }
}

if ($WorkUnit -and -not (Test-Path $WorkUnit)) {
    throw "Work-unit doc not found: $WorkUnit"
}

$changedFiles = Invoke-Git diff --name-only
$stagedFiles = Invoke-Git diff --cached --name-only
$untrackedFiles = Invoke-Git ls-files --others --exclude-standard
$fileCount = @($changedFiles + $stagedFiles + $untrackedFiles | Where-Object { $_ } | Sort-Object -Unique).Count

if ($fileCount -gt 20 -and -not $AllowLargePr) {
    throw "This PR touches $fileCount files. Split the work or pass -AllowLargePr intentionally."
}

if (-not $SkipVerification) {
    Run-Step "Whitespace check" { Invoke-Git diff --check }
}

Run-Step "Git status" { Invoke-Git status --short }
Run-Step "Stage files" { Invoke-Git add -A }
Run-Step "Commit" { Invoke-Git commit -m $CommitMessage }
Run-Step "Push branch" { Invoke-Git push -u origin $branch }

$fullBody = $Body
if ($WorkUnit) {
    $relativeWorkUnit = Resolve-Path -Relative $WorkUnit
    $fullBody = "$Body`n`nWork unit: $relativeWorkUnit"
}

Run-Step "Create draft PR" {
    Invoke-Gh pr create --draft --base $Base --head $branch --title $Title --body $fullBody
}
