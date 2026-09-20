param([string]$ScraperUrl = 'http://127.0.0.1:8000')
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$health = Invoke-RestMethod "$ScraperUrl/health" -TimeoutSec 10
if ($health.status -ne 'ok' -or $health.mode -ne 'live') {
    throw 'The Phase 2 checkpoint requires the frozen scraper running in live mode.'
}
$previousRunLive = $env:RUN_LIVE_SCRAPER
$previousScraperUrl = $env:SCRAPER_BASE_URL
Push-Location (Join-Path $repoRoot 'backend')
try {
    $env:RUN_LIVE_SCRAPER = 'true'
    $env:SCRAPER_BASE_URL = $ScraperUrl
    & ./mvnw.cmd -B -ntp -Plive-scraper '-Dtest=LiveScraperCheckpointTest' test
    if ($LASTEXITCODE -ne 0) { throw 'The live Phase 2 checkpoint failed. Review Maven output.' }
    Write-Output 'PASS: sentence -> Spring -> live FastAPI -> GyFTR DTO -> domain offers; cache and forceRefresh verified.'
    Write-Output 'Evidence: data/verification/phase2/'
} finally {
    $env:RUN_LIVE_SCRAPER = $previousRunLive
    $env:SCRAPER_BASE_URL = $previousScraperUrl
    Pop-Location
}
