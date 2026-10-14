# Open a workbook read-only in Excel (COM), recalculate, and report formula errors and the cells holding a given total.
#   powershell -File xlsx_check.ps1 PATH TOTAL
param([string]$Path, [double]$Total)
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
try {
    $wb = $xl.Workbooks.Open($Path, 0, $true)
    $xl.CalculateFull()
    $errors = 0
    $hits = @()
    foreach ($ws in $wb.Worksheets) {
        $ur = $ws.UsedRange
        $vals = $ur.Value2
        $rows = $ur.Rows.Count
        $cols = $ur.Columns.Count
        for ($r = 1; $r -le $rows; $r++) {
            for ($c = 1; $c -le $cols; $c++) {
                $v = if ($rows -eq 1 -and $cols -eq 1) { $vals } else { $vals[$r, $c] }
                if ($v -is [int]) { $errors++ }                 # COM returns error cells as Int32 codes
                elseif ($v -is [double] -and [math]::Abs($v - $Total) -lt 0.005) {
                    $hits += ('{0}!R{1}C{2}' -f $ws.Name, ($r + $ur.Row - 1), ($c + $ur.Column - 1))
                }
            }
        }
    }
    Write-Output ('{0}: formula errors {1}; cells equal to {2}: {3}' -f (Split-Path $Path -Leaf), $errors, $Total, ($hits -join ', '))
    $wb.Close($false)
} finally {
    $xl.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($xl) | Out-Null
}
