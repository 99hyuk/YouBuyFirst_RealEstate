param(
    [string]$Repository = "",
    [string]$RemoteUrl = "",
    [ValidateSet("private", "public", "internal")]
    [string]$Visibility = "private",
    [switch]$CreateRepo,
    [string]$BaseBranch = "main"
)

$ErrorActionPreference = "Stop"

function Stop-WithGuide($Message, $Guide) {
    Write-Host ""
    Write-Host $Message
    Write-Host ""
    Write-Host $Guide
    exit 1
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

function Get-OriginRemote {
    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $remote = & git -c "safe.directory=$repoRoot" remote get-url origin 2>$null
        if ($LASTEXITCODE -ne 0) {
            return ""
        }
        return $remote
    } finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
}

$initialSafeDirectory = ((Get-Location).ProviderPath -replace '\\', '/')
$repoRoot = git -c "safe.directory=$initialSafeDirectory" rev-parse --show-toplevel
if (-not $repoRoot) {
    throw "Could not find git repository root."
}
$repoRoot = ($repoRoot -replace '\\', '/')
Set-Location $repoRoot

$script:GhPath = Resolve-GhPath
if (-not $script:GhPath) {
    Stop-WithGuide "GitHub CLI 'gh' was not found." @"
Install GitHub CLI, open a new terminal, then run this script again.

1. Install: https://cli.github.com
2. Verify: gh --version
3. Login: gh auth login
4. Retry: powershell -ExecutionPolicy Bypass -File .\scripts\setup-github.ps1 -Repository "<owner>/<repo>"
"@
}

Invoke-Gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    Stop-WithGuide "GitHub CLI authentication is required." @"
Run:

gh auth login

Recommended choices:
- GitHub.com
- HTTPS
- Authenticate Git with your GitHub credentials: Yes
- Login with a web browser
"@
}

$existingRemote = Get-OriginRemote

if ($CreateRepo) {
    if ([string]::IsNullOrWhiteSpace($Repository)) {
        Stop-WithGuide "-CreateRepo requires -Repository owner/name." 'Example: powershell -ExecutionPolicy Bypass -File .\scripts\setup-github.ps1 -Repository "your-id/human-indicator" -CreateRepo'
    }

    Invoke-Gh repo view $Repository | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $visibilityFlag = "--$Visibility"
        Invoke-Gh repo create $Repository $visibilityFlag | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "GitHub repository creation failed."
        }
    }
}

if ([string]::IsNullOrWhiteSpace($existingRemote)) {
    if ([string]::IsNullOrWhiteSpace($RemoteUrl)) {
        if ([string]::IsNullOrWhiteSpace($Repository)) {
            Stop-WithGuide "No origin remote exists and no repository was provided." 'Example: powershell -ExecutionPolicy Bypass -File .\scripts\setup-github.ps1 -Repository "your-id/human-indicator"'
        }
        $RemoteUrl = "https://github.com/$Repository.git"
    }

    Invoke-Git remote add origin $RemoteUrl
    Write-Host "origin remote added: $RemoteUrl"
} else {
    Write-Host "origin remote already exists: $existingRemote"
}

$baseExists = Invoke-Git ls-remote --heads origin $BaseBranch
if ([string]::IsNullOrWhiteSpace($baseExists)) {
    Write-Host ""
    Write-Host "Warning: origin/$BaseBranch was not found."
    Write-Host "For the first bootstrap PR, the safest path is to create the GitHub repo with a README so $BaseBranch exists."
    Write-Host "Alternatively, push the initial bootstrap directly to main once, then use PR-only workflow afterwards."
}

Write-Host ""
Write-Host "GitHub connection check complete."
Write-Host "Next PR command example:"
Write-Host 'powershell -ExecutionPolicy Bypass -File .\scripts\open-pr.ps1 -Title "Bootstrap human indicator MVP" -Body "Initial MVP scaffold." -CommitMessage "Bootstrap human indicator MVP" -AllowLargePr'
