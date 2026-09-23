param(
    [Parameter(Mandatory=$true)][string]$Deck,
    [Parameter(Mandatory=$true)][string]$SlideContent,
    [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference = 'Stop'
$deckPath = (Resolve-Path -LiteralPath $Deck).Path
$contentPath = (Resolve-Path -LiteralPath $SlideContent).Path
$outputPath = [IO.Path]::GetFullPath($Output)
if (Test-Path -LiteralPath $outputPath) { throw 'Fresh native review directory required' }
if (@(Get-Process POWERPNT -ErrorAction SilentlyContinue).Count) {
    throw 'PowerPoint is already running; leave the user application untouched'
}
New-Item -ItemType Directory -Path $outputPath | Out-Null
$beforeHash = (Get-FileHash -LiteralPath $deckPath).Hash.ToLowerInvariant()
$specs = Get-Content -LiteralPath $contentPath -Raw -Encoding UTF8 | ConvertFrom-Json
$application = $null
$presentation = $null
$rows = @()
try {
    $application = New-Object -ComObject PowerPoint.Application
    if ($application.Presentations.Count -ne 0) { throw 'Unexpected open presentation' }
    $application.AutomationSecurity = 3
    $presentation = $application.Presentations.Open($deckPath, -1, 0, 0)
    $version = $application.Version
    if ($presentation.Slides.Count -ne 37) { throw 'Wrong native slide count' }
    foreach ($spec in $specs) {
        $number = [int]$spec.number
        $slide = $presentation.Slides.Item($number)
        $notes = @()
        foreach ($shape in $slide.NotesPage.Shapes) {
            if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
                $notes += $shape.TextFrame.TextRange.Text
            }
        }
        $actualNotes = ($notes -join "`n") -replace '\s+', ''
        $expectedNotes = $spec.notes -replace '\s+', ''
        $notesMatch = $actualNotes.Contains($expectedNotes)
        if (-not $notesMatch) { throw "Native notes incomplete on slide $number" }
        $tableCount = 0
        $chartCount = 0
        $nativeCells = @()
        $nativeValues = @()
        foreach ($shape in $slide.Shapes) {
            if ($shape.HasTable -eq -1) {
                $tableCount++
                for ($r=1; $r -le $shape.Table.Rows.Count; $r++) {
                    for ($c=1; $c -le $shape.Table.Columns.Count; $c++) {
                        $nativeCells += $shape.Table.Cell($r,$c).Shape.TextFrame.TextRange.Text
                    }
                }
            }
            if ($shape.HasChart -eq -1) {
                $chartCount++
                $nativeValues += @($shape.Chart.SeriesCollection(1).Values)
            }
        }
        if ($number -in @(19,21,33) -and $tableCount -ne 1) { throw "Missing native table on $number" }
        if ($number -eq 32 -and ($chartCount -ne 1 -or ($nativeValues -join ',') -ne '192,192,192,55,84')) {
            throw 'Native chart values differ from the checked source'
        }
        $stem = 'slide-{0:d2}' -f $number
        $slide.Export((Join-Path $outputPath "$stem.png"), 'PNG', 1280, 720)
        $notes | Set-Content -LiteralPath (Join-Path $outputPath "$stem-notes.txt") -Encoding UTF8
        if ($nativeCells.Count) {
            $nativeCells | Set-Content -LiteralPath (Join-Path $outputPath "$stem-table.txt") -Encoding UTF8
        }
        $rows += [PSCustomObject]@{slide=$number;notes_match=$notesMatch;tables=$tableCount;charts=$chartCount;chart_values=($nativeValues -join ',');render="$stem.png"}
        Write-Output "PowerPoint exported and checked slide $number"
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($slide)
    }
    $rows | Export-Csv -LiteralPath (Join-Path $outputPath 'NATIVE-CHECKS.csv') -NoTypeInformation -Encoding UTF8
    @("PowerPoint_version=$version", "slides=$($presentation.Slides.Count)", 'opened_read_only=True',
      'visible_window=False', "input_sha256=$beforeHash", 'native_notes_match=37/37',
      'native_tables=19,21,33', 'native_chart=32', 'native_chart_values=192,192,192,55,84') |
        Set-Content -LiteralPath (Join-Path $outputPath 'APPLICATION.txt') -Encoding UTF8
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $outputPath 'FAILURE.txt') -Encoding UTF8
    throw
} finally {
    if ($presentation) {
        $presentation.Close()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($presentation)
    }
    if ($application) {
        if ($application.Presentations.Count -eq 0) { $application.Quit() }
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($application)
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
    $afterHash = (Get-FileHash -LiteralPath $deckPath).Hash.ToLowerInvariant()
    "input_bytes_unchanged=$($beforeHash -eq $afterHash)" | Set-Content -LiteralPath (Join-Path $outputPath 'UNCHANGED.txt') -Encoding UTF8
    if ($beforeHash -ne $afterHash) { throw 'Input deck changed during read-only review' }
}
