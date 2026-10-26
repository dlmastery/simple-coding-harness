param(
    [Parameter(Mandatory)][string]$Repository,
    [Parameter(Mandatory)][string]$Workspace
)
$ErrorActionPreference = 'Stop'
$courseRoot = (Resolve-Path -LiteralPath $Repository).Path
$runRoot = [System.IO.Path]::GetFullPath($Workspace)
$logRoot = "$runRoot-command-log"
if ((Test-Path -LiteralPath $runRoot) -or (Test-Path -LiteralPath $logRoot)) {
    throw 'Use a new workspace; keep all existing evidence.'
}
$null = New-Item -ItemType Directory -Path $logRoot
$pythonPath = Join-Path $courseRoot '.venv/Scripts/python.exe'
$driverPath = Join-Path $courseRoot 'how-did-i-generate-it/rsi/scripts/run-two-generations.py'
$protocolPath = Join-Path $courseRoot 'how-did-i-generate-it/rsi/validation/TWO-GENERATION-PROTOCOL.md'
$script:commandRows = [System.Collections.Generic.List[object]]::new()

function Invoke-RecordedAction {
    param([string]$Label, [string[]]$ActionArguments, [int]$ExpectedExit = 0)
    $arguments = @($driverPath, '--repo', $courseRoot, '--workspace', $runRoot) + $ActionArguments
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = $pythonPath
    $startInfo.WorkingDirectory = $courseRoot
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.Environment['PYTHONUTF8'] = '1'
    foreach ($argument in $arguments) { $startInfo.ArgumentList.Add($argument) }
    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $startInfo
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    $null = $process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit(60000)) {
        $process.Kill($true)
        $process.WaitForExit()
        $exitCode = 124
    } else { $exitCode = $process.ExitCode }
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    $timer.Stop()
    $script:commandRows.Add([pscustomobject]@{
        action = $Label
        exit_status = $exitCode
        expected_exit = $ExpectedExit
        wall_seconds = $timer.Elapsed.TotalSeconds
    })
    $logPath = Join-Path $logRoot ('{0:D2}-{1}.md' -f $script:commandRows.Count, $Label)
    $lines = @('# Recorded command', '', "Action: $Label", "Exit: $exitCode; expected: $ExpectedExit.", "Wall seconds: $($timer.Elapsed.TotalSeconds).", '', 'Arguments in order:', '')
    $lines += @($pythonPath) + $arguments | ForEach-Object { '- ' + $_ }
    $lines += @('', 'Standard output:', '', '```text', $stdout, '```', '', 'Standard error:', '', '```text', $stderr, '```')
    $lines | Set-Content -LiteralPath $logPath -Encoding utf8NoBOM
    $script:commandRows | Export-Csv -LiteralPath (Join-Path $logRoot 'COMMANDS.csv') -NoTypeInformation -Encoding utf8NoBOM
    $process.Dispose()
    Write-Output "$Label`: exit $exitCode, $($timer.Elapsed.TotalSeconds.ToString('F2')) seconds"
    if ($exitCode -ne $ExpectedExit) { throw "Unexpected exit; preserved $logPath" }
}

Invoke-RecordedAction 'initialize' @('--action','init','--protocol',$protocolPath)
Invoke-RecordedAction 'fixed-generation-1' @('--action','compare','--path','baseline')
Invoke-RecordedAction 'fixed-generation-2' @('--action','compare','--path','baseline')
Invoke-RecordedAction 'recursive-proposal-1' @('--action','propose','--path','recursive')
Invoke-RecordedAction 'resume-status-1' @('--action','status')
Invoke-RecordedAction 'recursive-comparison-1' @('--action','compare','--path','recursive')
Invoke-RecordedAction 'recursive-proposal-2' @('--action','propose','--path','recursive')
Invoke-RecordedAction 'resume-status-2' @('--action','status')
Invoke-RecordedAction 'recursive-comparison-2' @('--action','compare','--path','recursive')
Invoke-RecordedAction 'refuse-fixed-generation-3' @('--action','compare','--path','baseline') 1
Invoke-RecordedAction 'refuse-recursive-generation-3' @('--action','propose','--path','recursive') 1
Invoke-RecordedAction 'audit' @('--action','audit')

Copy-Item -LiteralPath $logRoot -Destination (Join-Path $runRoot 'outer-commands') -Recurse
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $runRoot 'journey.source.ps1')
Write-Output "Retained execution and command logs: $runRoot"
