param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

Write-Host "Initializing git repository in $PWD"

if (-not (Test-Path ".git")) {
    git init
}

git branch -M $Branch
git add .

try {
    git commit -m "Initial commit"
}
catch {
    Write-Host "Commit may already exist or there are no staged changes."
}

$remoteExists = $false
try {
    $null = git remote get-url origin
    $remoteExists = $true
}
catch {
    $remoteExists = $false
}

if ($remoteExists) {
    git remote set-url origin $RepoUrl
}
else {
    git remote add origin $RepoUrl
}

git push -u origin $Branch
