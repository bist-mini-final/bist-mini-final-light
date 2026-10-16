<#
.SYNOPSIS
Install project-local PostgreSQL/pgvector and optionally CUDA llama.cpp models.
.DESCRIPTION
Run from an ASCII checkout. DatabaseOnly prepares the OpenAI path without GPU
downloads. SkipModels prepares local GPU binaries but requires existing GGUFs.
Existing system PostgreSQL and its databases are not modified.
#>
param([switch]$SkipModels, [switch]$DatabaseOnly)
$ErrorActionPreference = 'Stop'
foreach ($RequiredCommand in @('uv', 'tar')) {
    if (-not (Get-Command $RequiredCommand -ErrorAction SilentlyContinue)) {
        throw "Missing $RequiredCommand. See docs/ONBOARDING.md before running setup."
    }
}
if (-not $DatabaseOnly -and -not (Get-Command nvidia-smi -ErrorAction SilentlyContinue)) {
    throw 'NVIDIA driver not found. Use -DatabaseOnly for OpenAI, or install the driver first.'
}
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

# Pinned build matching the verified local GPU runtime. CUDA toolkit is not required.
if (-not $DatabaseOnly) {
$LlamaPath = Join-Path $ProjectRoot '.runtime\llama'
New-Item -ItemType Directory -Path $LlamaPath -Force | Out-Null
$ReleaseRoot = 'https://github.com/ggml-org/llama.cpp/releases/download/b11429'
$Assets = @{
    'llama-b11429-bin-win-cuda-12.4-x64.zip' = 'dd6df685c1024e6aa55ca55ad35038692d5e284d4dc895e7a646c3245d3d14ff'
    'cudart-llama-bin-win-cuda-12.4-x64.zip' = '8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6'
}
foreach ($Asset in $Assets.Keys) {
    $ZipPath = Join-Path $InstallerPath $Asset
    if (-not (Test-Path -LiteralPath $ZipPath) -or (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash -ne $Assets[$Asset]) {
        Invoke-WebRequest "$ReleaseRoot/$Asset" -OutFile $ZipPath
    }
    if ((Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash -ne $Assets[$Asset]) {
        throw "SHA-256 mismatch: $Asset. Rerun setup to download again."
    }
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $LlamaPath -Force
}
}
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
if (-not $SkipModels -and -not $DatabaseOnly) {
    uv run --with 'huggingface_hub[hf_xet]' python scripts/download_models.py
    if ($LASTEXITCODE -ne 0) { throw 'GGUF download failed; rerun to resume' }
}
if ($DatabaseOnly) {
    uv run python scripts/configure_local.py --database-only
} else {
    uv run python scripts/configure_local.py
}
if ($LASTEXITCODE -ne 0) { throw 'Local profile configuration failed' }
Write-Output 'Ready: uv run python run.py'
