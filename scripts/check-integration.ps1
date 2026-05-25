$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$PreviousRunOpenAiIntegrationTests = $env:RUN_OPENAI_INTEGRATION_TESTS

Set-Location $ProjectRoot

if (-not (Test-Path $VenvPython)) {
    throw "Expected virtual environment Python was not found at $VenvPython. Run scripts/setup-dev.ps1 first."
}

function Invoke-PythonModule {
    & $VenvPython -m @args
    if ($LASTEXITCODE -ne 0) {
        throw "python -m $($args[0]) failed with exit code $LASTEXITCODE."
    }
}

try {
    $env:RUN_OPENAI_INTEGRATION_TESTS = "1"
    Invoke-PythonModule pytest integration_tests
}
finally {
    if ($null -eq $PreviousRunOpenAiIntegrationTests) {
        Remove-Item Env:\RUN_OPENAI_INTEGRATION_TESTS -ErrorAction SilentlyContinue
    }
    else {
        $env:RUN_OPENAI_INTEGRATION_TESTS = $PreviousRunOpenAiIntegrationTests
    }
}
