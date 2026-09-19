param(
    [ValidateSet('local', 'test', 'docker', 'production')]
    [string]$Profile = 'local',
    [switch]$Fixture
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if ($Profile -eq 'production' -and $Fixture) { throw 'Fixture mode is forbidden in production.' }
$candidates = @(
    $env:SCRAPER_PYTHON,
    (Join-Path $repoRoot 'scraper/.venv/Scripts/python.exe'),
    (Join-Path $repoRoot 'Scrapper/scraper/.venv/Scripts/python.exe')
)
$pythonExe = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $pythonExe) { throw 'Create scraper/.venv with Python 3.12+ and install requirements.lock, or set SCRAPER_PYTHON.' }
$env:PYTHONPATH = Join-Path $repoRoot 'scraper/src'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:APP_ENV = $Profile
$env:DATA_DIR = Join-Path $repoRoot 'data/runtime/scraper'
$env:FIXTURE_DIR = if ($Fixture) { Join-Path $repoRoot 'scraper/tests/fixtures' } else { '' }
if ($Fixture) {
    $env:PLAYWRIGHT_ENABLED = 'false'
    $env:SAVE_RAW_HTML = 'false'
}
Push-Location (Join-Path $repoRoot 'scraper')
try {
    & $pythonExe -m uvicorn payment_scraper.api.app:app --host 127.0.0.1 --port 8000
    exit $LASTEXITCODE
} finally { Pop-Location }
