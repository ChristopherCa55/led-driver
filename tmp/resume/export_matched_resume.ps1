$ErrorActionPreference = 'Stop'
$resumeDocxPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../../output/resume/updated_resume_pdf_matched.docx')).Path
$resumePdfPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'pdf_matched_check.pdf'))
$resumeWord = $null
$resumeDocument = $null
try {
    $resumeWord = New-Object -ComObject Word.Application
    $resumeWord.Visible = $false
    $resumeWord.DisplayAlerts = 0
    $resumeDocument = $resumeWord.Documents.Open($resumeDocxPath, $false, $true, $false)
    $resumeDocument.Repaginate()
    $resumePageCount = $resumeDocument.ComputeStatistics(2)
    $resumeDocument.ExportAsFixedFormat($resumePdfPath, 17)
    Write-Output "Rendered corrected DOCX ($resumePageCount page(s)): $resumePdfPath"
}
finally {
    if ($null -ne $resumeDocument) { $resumeDocument.Close(0) }
    if ($null -ne $resumeWord) { $resumeWord.Quit() }
}
