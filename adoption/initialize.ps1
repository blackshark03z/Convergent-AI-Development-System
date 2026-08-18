[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$Root,
  [Parameter(Mandatory = $true)][string]$AcceptedRef,
  [Parameter(Mandatory = $true)][string]$ProjectName,
  [Parameter(Mandatory = $true)][string]$Purpose,
  [Parameter(Mandatory = $true)][string]$IntendedUse,
  [Parameter(Mandatory = $true)][string]$SuccessDefinition,
  [Parameter(Mandatory = $true)][string]$NonGoals,
  [Parameter(Mandatory = $true)][string]$Constraints,
  [Parameter(Mandatory = $true)][string]$QualityGate,
  [ValidateSet("small-tool", "library", "desktop-app", "production-app", "service", "custom")][string]$ProjectProfile = "small-tool",
  [ValidateSet("greenfield", "existing")][string]$Mode = "greenfield",
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Stop"
$target = (Resolve-Path -LiteralPath $Root).Path
& git -C $target rev-parse --show-toplevel *> $null
if ($LASTEXITCODE -ne 0) { throw "Root must be a Git worktree." }
$policyPath = Join-Path $target ".buildos-policy.json"
if (Test-Path -LiteralPath $policyPath) { throw ".buildos-policy.json already exists; merge documentation_handoff deliberately." }
$example = Get-Content -Raw (Join-Path $PackageRoot "adoption\project-policy.example.json") | ConvertFrom-Json
$example.documentation_handoff.accepted_ref = $AcceptedRef
$example.project_lifecycle.project_profile = $ProjectProfile
$example.project_lifecycle.project_intent.name = $ProjectName
$example.project_lifecycle.project_intent.purpose = $Purpose
$example.project_lifecycle.project_intent.intended_use = $IntendedUse
$example.project_lifecycle.project_intent.success_definition = $SuccessDefinition
$example.project_lifecycle.project_intent.non_goals = $NonGoals
$example.project_lifecycle.project_intent.constraints = $Constraints
$example.project_lifecycle.quality_gates[0].id = "adoption-quality-gate"
$example.project_lifecycle.quality_gates[0].command = $QualityGate
$example | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $policyPath -Encoding utf8

$lifecycle = Join-Path $PackageRoot "skills\project-lifecycle-bootstrap\scripts\project_lifecycle.py"
& python $lifecycle --root $target bootstrap --mode $Mode --verify-gates
if ($LASTEXITCODE -ne 0) { throw "Project Lifecycle bootstrap failed." }

$authority = Join-Path $PackageRoot "skills\project-lifecycle-bootstrap\scripts\execution_authority.py"
& python $authority --root $target --package-root $PackageRoot write-record
if ($LASTEXITCODE -ne 0) { throw "Build OS execution authority record creation failed." }
& python $authority --root $target check
if ($LASTEXITCODE -ne 0) { throw "Build OS execution authority preflight failed." }

Write-Output "PROJECT_LIFECYCLE_ADOPTION=PASS"
Write-Output "SINGLE_ACTIVE_EXECUTION_AUTHORITY=PASS"
Write-Output "Commit the policy and generated Knowledge Pack before Build OS bootstrap; the frozen kernel requires a clean baseline."
Write-Output "Use project-lifecycle-bootstrap for accepted-baseline reconciliation and documentation-handoff-continuity for active tasks. Both are mandatory by adoption contract, not kernel enforcement."
