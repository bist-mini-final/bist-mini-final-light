param([switch]$SkipModels)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ($ProjectRoot -match '[^\x00-\x7F]') {
    throw 'Windows PostgreSQL requires an ASCII path. Clone into C:\Repos\bist-mini-final-light and run this script there.'
}
Set-Location -LiteralPath $ProjectRoot
$InstallerPath = Join-Path $ProjectRoot '.runtime\installer'
New-Item -ItemType Directory -Path $InstallerPath -Force | Out-Null

# Official micromamba plus conda-forge's matching PostgreSQL/pgvector builds.
$MambaBinary = Join-Path $InstallerPath 'Library\bin\micromamba.exe'
if (-not (Test-Path -LiteralPath $MambaBinary)) {
    Invoke-WebRequest 'https://micro.mamba.pm/api/micromamba/win-64/latest' -OutFile (Join-Path $InstallerPath 'micromamba.tar.bz2')
    tar -xjf (Join-Path $InstallerPath 'micromamba.tar.bz2') -C $InstallerPath
    if ($LASTEXITCODE -ne 0) { throw 'micromamba extraction failed' }
}
& $MambaBinary create -y -p (Join-Path $ProjectRoot '.runtime\postgres') -c conda-forge 'postgresql=16' 'pgvector>=0.8'
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL/pgvector installation failed' }

# Pinned CUDA 13.1 build: supports the RTX 50 series without requiring a toolkit.
$LlamaPath = Join-Path $ProjectRoot '.runtime\llama'
New-Item -ItemType Directory -Path $LlamaPath -Force | Out-Null
$ReleaseRoot = 'https://github.com/ggml-org/llama.cpp/releases/download/b9000'
foreach ($Asset in @('llama-b9000-bin-win-cuda-13.1-x64.zip', 'cudart-llama-bin-win-cuda-13.1-x64.zip')) {
    $ZipPath = Join-Path $InstallerPath $Asset
    Invoke-WebRequest "$ReleaseRoot/$Asset" -OutFile $ZipPath
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $LlamaPath -Force
}
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
if (-not $SkipModels) {
    uv run --with 'huggingface_hub[hf_xet]' python scripts/download_models.py
    if ($LASTEXITCODE -ne 0) { throw 'GGUF download failed; rerun to resume' }
}
uv run python scripts/configure_local.py
if ($LASTEXITCODE -ne 0) { throw 'Local profile configuration failed' }
Write-Output 'Ready: uv run python run.py'
