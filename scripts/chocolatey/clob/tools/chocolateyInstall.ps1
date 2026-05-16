$ErrorActionPreference = 'Stop'

$packageName = 'clob'
$version     = '0.2.0'

Write-Host "Installing clob $version via pip..." -ForegroundColor Cyan

# Ensure pip is available
try {
    $pythonCmd = Get-Command python -ErrorAction Stop
} catch {
    throw "Python not found. Install Python 3.12+ first: choco install python312"
}

# Check Python version
$pyVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pyVersion -lt [version]"3.12") {
    throw "clob requires Python 3.12+. Found: $pyVersion. Run: choco upgrade python312"
}

# Install clob via pip
& python -m pip install "clob==$version" --quiet
if ($LASTEXITCODE -ne 0) {
    throw "pip install failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "clob $version installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Quick start:" -ForegroundColor Yellow
Write-Host "  1. Set your API key:"
Write-Host "       setx OPENROUTER_API_KEY 'your-key-here'"
Write-Host "  2. Launch the TUI:"
Write-Host "       clob"
Write-Host "  3. Or send a message:"
Write-Host "       clob chat 'Hello, world!'"
Write-Host ""
Write-Host "Config file: $env:USERPROFILE\.config\clob\config.toml"
Write-Host "Documentation: https://github.com/crishacks/clob"
