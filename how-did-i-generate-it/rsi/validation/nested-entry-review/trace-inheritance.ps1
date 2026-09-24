param([Parameter(Mandatory=$true)][string]$Repository, [Parameter(Mandatory=$true)][string]$Output)
$evaluation = Join-Path $Repository 'rsi/evidence/2026-09-22/nested-research-evaluation'
$development = Join-Path $Repository 'rsi/evidence/2026-09-22/nested-research-development'
$generation = Import-Csv (Join-Path $development 'GENERATION-TWO.csv') | Where-Object improver -EQ 'i1'
$childPath = Join-Path $development $generation.source
$childHash = (Get-FileHash -LiteralPath $childPath).Hash.ToLowerInvariant()
if ($childHash -ne $generation.child_sha256) { throw 'Inherited child mismatch' }
$parentPath = Join-Path $development 'generations/2/i1/PARENT.py'
$parentHash = (Get-FileHash -LiteralPath $parentPath).Hash.ToLowerInvariant()
if ($parentHash -ne $generation.parent_sha256) { throw 'Inherited parent mismatch' }
$verdict = Import-Csv (Join-Path $development 'VERDICTS.csv') | Where-Object improver -EQ 'i1'
if ($verdict.promote -ne 'True') { throw 'No retained development child' }
$firstChild = Join-Path $development 'generations/1/i1/researcher.py'
if ((Get-FileHash -LiteralPath $firstChild).Hash.ToLowerInvariant() -ne $parentHash) { throw 'Second generation did not inherit the retained child' }
$choices = Import-Csv (Join-Path $evaluation 'CHOICES.csv')
$records = foreach ($task in @('43','45','361260')) {
  $sourcePath = Join-Path $evaluation "runs/$task/i1/researcher.py"
  if ((Get-FileHash -LiteralPath $sourcePath).Hash.ToLowerInvariant() -ne $childHash) { throw "Wrong later researcher: $task" }
  $ledger = Import-Csv (Join-Path $evaluation "runs/$task/i1/LEDGER.csv")
  if ($ledger.Count -ne 12 -or @($ledger | Where-Object researcher_sha256 -NE $childHash).Count) { throw "Later ledger mismatch: $task" }
  $choice = $choices | Where-Object { $_.task -eq $task -and $_.arm -eq 'i1' }
  $selected = $ledger | Where-Object step -EQ $choice.step
  if ($selected.candidate_sha256 -ne $choice.candidate_sha256) { throw "Choice mismatch: $task" }
  [PSCustomObject]@{task=$task;improver='i1';retained_parent_sha256=$parentHash;later_researcher_sha256=$childHash;attempts=$ledger.Count;selected_step=$choice.step;selected_template=$choice.template;selected_candidate_sha256=$choice.candidate_sha256;later_source_verified=$true}
}
$records | Export-Csv -LiteralPath (Join-Path $Output 'INHERITED-SOURCE-TRACE.csv') -NoTypeInformation
Write-Output 'Three selected cases trace a retained development child into the second researcher and all twelve later attempts; zero fits.'
