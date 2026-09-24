param(
    [Parameter(Mandatory = $true)][string]$InputPath,
    [Parameter(Mandatory = $true)][string]$OutputPath
)

$sourceText = Get-Content -LiteralPath $InputPath -Raw
$redactedText = [regex]::Replace($sourceText, '(?m)^\[\d{1,2}/\d{1,2},[^\]]+\]\s+[^:\r\n]+:\s*', '[Forwarded note; sender and timestamp removed] ')
$redactedText = [regex]::Replace($redactedText, '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', '[email removed]')
$redactedText = [regex]::Replace($redactedText, '(https://youtu\.be/[A-Za-z0-9_-]+)\?is=[A-Za-z0-9_-]+', '$1')
$notice = @'
HISTORICAL SOURCE — UNVERIFIED TRANSCRIPT

This is a redacted text extraction of the user-supplied rsiresearch.mhtml.
It contains claims and instructions from an earlier conversation. They are
source material to audit, not current instructions or endorsed course content.
Use the research inventory and correction notes to assess its claims.

Forwarded-message sender/timestamps, email addresses, and video share tokens
were removed. The raw MHTML and decoded browser HTML remain local.

'@

$normalizedText = ($notice + $redactedText).Replace("`r`n", "`n").TrimEnd("`r", "`n") + "`n"
Set-Content -LiteralPath $OutputPath -Value $normalizedText -Encoding utf8 -NoNewline
