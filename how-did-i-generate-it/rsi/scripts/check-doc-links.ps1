param([string]$RepositoryRoot = (Get-Location).Path)

$recordRoot = Join-Path $RepositoryRoot 'how-did-i-generate-it/rsi'
$skillRoot = Join-Path $RepositoryRoot 'skills/build-research-codelabs'
$documents = @(Get-ChildItem -LiteralPath $recordRoot,$skillRoot -Recurse -Filter '*.md')
$broken = @()
$checked = 0
foreach ($document in $documents) {
    $content = Get-Content -LiteralPath $document.FullName -Raw
    foreach ($match in [regex]::Matches($content, '\[[^\]]+\]\(([^)\r\n]+)\)')) {
        $destination = $match.Groups[1].Value.Trim('<','>')
        if ($destination -match '^[a-zA-Z][a-zA-Z0-9+.-]*:' -or $destination.StartsWith('#')) { continue }
        $relativePath = ($destination -split '#', 2)[0]
        if (-not $relativePath) { continue }
        $resolved = Join-Path $document.DirectoryName $relativePath
        $checked++
        if (-not (Test-Path -LiteralPath $resolved)) {
            $broken += "$($document.FullName): $destination"
        }
    }
}
if ($broken.Count -gt 0) {
    $broken | Write-Output
    throw "$($broken.Count) broken local links"
}
Write-Output "Checked $checked local links across $($documents.Count) Markdown files; no broken targets."
