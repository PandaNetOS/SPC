# finalize_round.ps1 — Generate manifest draft from git diff
# Usage: .\finalize_round.ps1 -RoundName round18 [-BaseCommit HEAD~N]

param(
    [Parameter(Mandatory=$true)]
    [string]$RoundName,
    [string]$BaseCommit = "HEAD~1"
)

$ErrorActionPreference = "Stop"
Set-Location "D:\PNOS\SPC"

Write-Host "=== Finalize: $RoundName ===" -ForegroundColor Cyan

# 1. Changed files
Write-Host "`n[1/4] Changed files:" -ForegroundColor Yellow
$changedFiles = git diff --name-only "$BaseCommit..HEAD"
$changedFiles | ForEach-Object { Write-Host "  $_" }

# 2. Detect strategy update
$strategyUpdated = $false
foreach ($f in @("labs/lottery/studies/dlt/strategy/strategy.json", "labs/lottery/studies/dlt/strategy/STRATEGY_GUIDE.md")) {
    if ($changedFiles -contains $f) {
        $strategyUpdated = $true
        Write-Host "  [!] Strategy file changed: $f" -ForegroundColor Red
    }
}

# 3. Deliverables
Write-Host "`n[2/4] Deliverables:" -ForegroundColor Yellow
$deliverables = @()
foreach ($f in $changedFiles) {
    if ($f -like ".git/*") { continue }
    $kind = "other"
    if ($f -like "*/scripts/*.py") { $kind = "script" }
    elseif ($f -like "*/iterations/*/FINDINGS.md") { $kind = "findings" }
    elseif ($f -like "*/iterations/*/HANDOFF.md") { $kind = "handoff" }
    elseif ($f -like "*/iterations/*/TASK_BRIEF.md") { $kind = "task_brief" }
    elseif ($f -like "*/iterations/*/manifest.json") { $kind = "manifest" }
    elseif ($f -like "*.md") { $kind = "doc" }
    elseif ($f -like "*.py") { $kind = "code" }
    elseif ($f -like "*.jsonl") { $kind = "data" }
    elseif ($f -like "*.json") { $kind = "config" }
    $deliverables += [pscustomobject]@{ path = $f; kind = $kind }
    Write-Host "  $f ($kind)"
}

# 4. Manifest draft
Write-Host "`n[3/4] Generating manifest draft..." -ForegroundColor Yellow
$manifest = [ordered]@{
    round = $RoundName
    game = "dlt"
    title = "<fill-in>"
    status = "delivered"
    started_at = "2026-10-12"
    finished_at = "2026-10-12"
    executor = "AI"
    supersedes_round = $null
    inputs = [ordered]@{
        data_version = "dlt_full_2933"
        upstream_fact_ids = @()
        previous_handoff = "labs/lottery/studies/dlt/iterations/<prev>/HANDOFF.md"
        task_brief = "labs/lottery/studies/dlt/iterations/$RoundName/TASK_BRIEF.md"
    }
    outputs = [ordered]@{
        new_fact_ids = @()
        updated_fact_ids = @()
        refuted_fact_ids = @()
        strategy_updated = $strategyUpdated
        strategy_landed = @()
        actual_updates = @($changedFiles)
        framework_revision = [ordered]@{
            proposed = @(); accepted = @(); rejected = @()
        }
    }
    deliverables = $deliverables
}

$draftPath = "labs/lottery/studies/dlt/iterations/$RoundName/manifest.json.draft"
$manifest | ConvertTo-Json -Depth 10 | Out-File $draftPath -Encoding UTF8
Write-Host "`n[4/4] Draft: $draftPath" -ForegroundColor Green

if ($strategyUpdated) {
    Write-Host "`n[!] Strategy changed: must sync STRATEGY_GUIDE.md and bump versions.json iteration" -ForegroundColor Red
}
