$ErrorActionPreference = 'Stop'
$resumeDirectory = Join-Path $PSScriptRoot '../../output/resume'
$resumeDocxPath = (Resolve-Path -LiteralPath (Join-Path $resumeDirectory 'updated_resume.docx')).Path
$resumePdfPath = [System.IO.Path]::GetFullPath((Join-Path $resumeDirectory 'updated_resume.pdf'))
$resumeWord = $null
$resumeDocument = $null
try {
    Write-Output 'Starting Word export'
    $resumeWord = New-Object -ComObject Word.Application
    Write-Output 'Word started'
    $resumeWord.Visible = $false
    $resumeWord.DisplayAlerts = 0
    $resumeDocument = $resumeWord.Documents.Open($resumeDocxPath, $false, $true, $false)
    Write-Output 'Resume opened'
    $resumeDocument.Repaginate()
    $resumePageCount = $resumeDocument.ComputeStatistics(2)
    $resumeDocument.ExportAsFixedFormat($resumePdfPath, 17)
    Write-Output "Exported $resumePdfPath ($resumePageCount page(s))"
}
finally {
    if ($null -ne $resumeDocument) { $resumeDocument.Close(0) }
    if ($null -ne $resumeWord) { $resumeWord.Quit() }
}
