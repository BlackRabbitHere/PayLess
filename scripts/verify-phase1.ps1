param(
    [string]$FrontendUrl = 'http://localhost:5173',
    [string]$BackendUrl = 'http://localhost:8080',
    [string]$ScraperUrl = 'http://localhost:8000'
)
$ErrorActionPreference = 'Stop'
$frontend = Invoke-WebRequest -Uri $FrontendUrl -TimeoutSec 10
if ($frontend.StatusCode -ne 200) { throw 'Frontend did not start.' }
$backend = Invoke-RestMethod "$BackendUrl/actuator/health" -TimeoutSec 10
if ($backend.status -ne 'UP') { throw 'Backend is not healthy.' }
$scraper = Invoke-RestMethod "$ScraperUrl/health" -TimeoutSec 10
if ($scraper.status -ne 'ok') { throw 'Scraper is not healthy.' }
$connections = Invoke-RestMethod "$BackendUrl/api/v1/system/status" -TimeoutSec 35
if ($connections.backend -ne 'UP' -or $connections.scraper.status -ne 'UP') { throw 'Spring-to-scraper connectivity failed.' }
foreach ($pair in @(
    @{provider='GYFTR'; merchant='SWIGGY'},
    @{provider='YATRA'; merchant='YATRA'},
    @{provider='EASEMYTRIP'; merchant='EASEMYTRIP'}
)) {
    $mapped = Invoke-RestMethod "$BackendUrl/api/v1/optimization/scraper-check" -Method Post -ContentType 'application/json' -Body ($pair | ConvertTo-Json -Compress) -TimeoutSec 35
    if ($mapped.status -notin @('SUCCESS','PARTIAL') -or $mapped.observations.Count -lt 1) { throw 'No mapped observations returned.' }
    if ($mapped.provider -ne $pair.provider) { throw 'Provider mapping mismatch.' }
    if ($mapped.fixture -and $pair.provider -eq 'GYFTR' -and $mapped.observations[0].voucherSellingPrice -ne '487.50') { throw 'Decimal-string mapping failed.' }
    Write-Output ("PASS: {0}/{1} -> {2} mapped observations (fixture={3})" -f $pair.provider,$pair.merchant,$mapped.observations.Count,$mapped.fixture)
}
Write-Output "PASS: React $FrontendUrl, Spring $BackendUrl, FastAPI $ScraperUrl, Spring-to-scraper JSON mapping."
