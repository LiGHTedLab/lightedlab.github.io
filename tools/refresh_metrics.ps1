# Refresh Google Scholar metrics from this PC and publish them.
# Google Scholar blocks GitHub's servers, so the weekly GitHub Action alone cannot always update the numbers.
# Run this by hand (right-click > Run with PowerShell) or from Windows Task Scheduler.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

git pull --quiet --rebase
python tools/update_metrics.py
git diff --quiet -- data/metrics.json
if ($LASTEXITCODE -ne 0) {
    git add data/metrics.json
    git commit --quiet -m "Update Google Scholar metrics"
    git push --quiet
    Write-Host "Pushed new metrics; the site will rebuild in about a minute."
} else {
    Write-Host "Metrics unchanged."
}
