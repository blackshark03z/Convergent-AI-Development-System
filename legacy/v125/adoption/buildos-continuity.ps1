[CmdletBinding(PositionalBinding = $false)]
param(
  [Parameter(Mandatory = $true)][string]$Root,
  [Parameter(Mandatory = $true)][ValidateSet("bootstrap", "record-commit", "validate")][string]$Command,
  [string]$TaskId,
  [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments,
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
# Preserve an injected --check command as one argument when PowerShell 7 is used.
if (Get-Variable -Name PSNativeCommandArgumentPassing -ErrorAction SilentlyContinue) { $PSNativeCommandArgumentPassing = 'Standard' }
$continuity = Join-Path $PackageRoot "skills\documentation-handoff-continuity\scripts\continuity.py"
$facade = Join-Path $PackageRoot "scripts\ai.py"
if ($Command -eq "record-commit") {
  if (-not $TaskId) { throw "record-commit requires -TaskId so the pre-record docs gate targets the active sidecar." }
  & python $continuity --root $Root --task-id $TaskId docs-check
  if ($LASTEXITCODE -ne 0) { throw "Documentation impact gate failed before record-commit." }
  & python $facade --root $Root record-commit
  exit $LASTEXITCODE
}
if ($Command -eq "validate") {
  # The validation command must already contain the injected docs-check from bootstrap.
  & python $facade --root $Root validate @Arguments
  exit $LASTEXITCODE
}
$taskIndex = [array]::IndexOf($Arguments, "--task-id")
if (-not $TaskId -and $taskIndex -ge 0 -and $taskIndex -lt ($Arguments.Count - 1)) { $TaskId = $Arguments[$taskIndex + 1] }
if (-not $TaskId) { throw "bootstrap requires --task-id or -TaskId." }
& python $facade --root $Root bootstrap @Arguments --skill documentation-handoff-continuity --check "python `"$continuity`" --root `"$Root`" --task-id $TaskId docs-check"
$bootstrapExit = $LASTEXITCODE
if ($bootstrapExit -ne 0) { exit $bootstrapExit }
& python $continuity --root $Root --task-id $TaskId bootstrap --next-safe-action "classify documentation impact before product commit" --documentation-impact UNKNOWN --documentation-rationale "classification pending"
exit $LASTEXITCODE
