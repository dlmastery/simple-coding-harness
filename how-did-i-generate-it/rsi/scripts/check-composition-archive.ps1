$ErrorActionPreference = 'Stop'
$archivePrefix = 'rsi/evidence/2026-09-22/composition-repair/'
$manifestRows = @(Import-Csv ($archivePrefix + 'ARCHIVE-MANIFEST.csv'))
$archivePaths = @($manifestRows | ForEach-Object { $archivePrefix + $_.path })
$rawBlobHashes = @($archivePaths | git hash-object --no-filters --stdin-paths)
if ($LASTEXITCODE -ne 0 -or $rawBlobHashes.Count -ne $manifestRows.Count) { throw 'Raw blob hashing failed' }
$staged = @{}
foreach ($entry in @(git ls-files -s -- $archivePrefix)) {
    if ($entry -notmatch '^100644 ([0-9a-f]+) 0\t(.+)$') { throw "Unexpected staged entry: $entry" }
    $staged[$Matches[2]] = $Matches[1]
}
if ($staged.Count -ne $manifestRows.Count + 2) { throw 'Expected original files, manifest and authored README' }
$verdicts = for ($index = 0; $index -lt $manifestRows.Count; $index++) {
    $sourceHash = (Get-FileHash -LiteralPath $archivePaths[$index] -Algorithm SHA256).Hash.ToLowerInvariant()
    [pscustomobject]@{
        path = $manifestRows[$index].path
        original_sha256_matches = $sourceHash -eq $manifestRows[$index].sha256
        staged_blob_matches = $staged[$archivePaths[$index]] -eq $rawBlobHashes[$index]
    }
}
$verdicts | Export-Csv how-did-i-generate-it/rsi/validation/COMPOSITION-ARCHIVE-INDEX-CHECK.csv -NoTypeInformation
if (@($verdicts | Where-Object { -not $_.original_sha256_matches -or -not $_.staged_blob_matches }).Count) { throw 'Archive identity mismatch' }
Write-Output "All $($manifestRows.Count) original files match their manifest and staged Git blobs; summary and manifest also tracked."
