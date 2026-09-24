param(
  [Parameter(Mandatory=$true)][string]$Workspace,
  [Parameter(Mandatory=$true)][ValidateSet('search','score')][string]$Action
)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$pythonPath = Join-Path $repoRoot '.venv/Scripts/python.exe'
$driverPath = Join-Path $PSScriptRoot 'evaluate_discovery.py'
$runPath = (Resolve-Path -LiteralPath $Workspace).Path
if (-not $IsWindows) { throw 'This helper is only for Windows; use the ordinary driver elsewhere.' }
Add-Type @'
using System.Runtime.InteropServices;
public static class RsiEvaluationPower {
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern uint SetThreadExecutionState(uint flags);
}
'@
$record = Join-Path $runPath "POWER-$Action.md"
if (Test-Path -LiteralPath $record) { throw 'Preserve the existing power-session record; review before another session.' }
$previous = [RsiEvaluationPower]::SetThreadExecutionState([uint32]2147483649)
if ($previous -eq 0) { throw 'Could not request temporary idle-sleep prevention' }
try {
    @("# Temporary idle-sleep prevention", '', "Action: $Action", "PID: $PID",
      "Started UTC: $([datetime]::UtcNow.ToString('o'))",
      'ES_CONTINUOUS and ES_SYSTEM_REQUIRED apply to this execution thread only.',
      'No persistent power setting was changed.') | Set-Content -LiteralPath $record
    & $pythonPath $driverPath $Action --workspace $runPath
    $driverExit = $LASTEXITCODE
    Add-Content -LiteralPath $record -Value "Driver exit code: $driverExit"
    if ($driverExit -ne 0) { throw "Evaluation driver exited with code $driverExit" }
}
finally {
    $released = [RsiEvaluationPower]::SetThreadExecutionState([uint32]2147483648)
    Add-Content -LiteralPath $record -Value "Released UTC: $([datetime]::UtcNow.ToString('o')); API return: $released"
}
