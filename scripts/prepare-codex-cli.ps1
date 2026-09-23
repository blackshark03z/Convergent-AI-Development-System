$ErrorActionPreference = "Stop"
$app = Get-AppxPackage -Name OpenAI.Codex
if (-not $app) { throw "OpenAI.Codex package not found" }
$srcDir = Join-Path $app.InstallLocation "app\resources"
$dst = "D:\CADS-Benchmark\tools\codex-cli"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item (Join-Path $srcDir "codex.exe") (Join-Path $dst "codex.exe") -Force
Copy-Item (Join-Path $srcDir "codex-code-mode-host.exe") (Join-Path $dst "codex-code-mode-host.exe") -Force
Write-Output ("CODEX=" + (Join-Path $dst "codex.exe"))
& (Join-Path $dst "codex.exe") --version
