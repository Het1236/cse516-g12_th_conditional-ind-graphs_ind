# One-shot M4 export. Read-only on the M3 data: it only reads results\ and runs\ and writes inside this kit folder.
# Usage (PowerShell, from the kit folder):
#   powershell -ExecutionPolicy Bypass -File .\run_m4_export.ps1 -Root D:\rhino_work
# Result: m4_export_report.txt and M4_qG_export_return.zip in this folder. Send the zip back.
param(
    [string]$Root = "D:\rhino_work",   # folder that contains results\, runs\ and causica\ from M3
    [string]$Py = ""                   # python of the M3 environment; found automatically if empty
)
$ErrorActionPreference = "Stop"
$kit = $PSScriptRoot
$report = Join-Path $kit "m4_export_report.txt"
"M4 export report" | Out-File -FilePath $report -Encoding utf8
function Log([string]$m) { Write-Host $m; Add-Content -Path $report -Value $m -Encoding utf8 }

Log "date: $(Get-Date -Format s)   host: $env:COMPUTERNAME   root: $Root"
if (-not (Test-Path $Root)) { Log "ERROR: root folder not found. Pass -Root <folder with results and runs>."; exit 1 }

if (-not $Py) {
    $cands = @("D:\rhino_env\venv\Scripts\python.exe",
               (Join-Path (Split-Path $Root -Parent) "rhino_env\venv\Scripts\python.exe"),
               "C:\rhino_env\venv\Scripts\python.exe")
    foreach ($c in $cands) { if (Test-Path $c) { $Py = $c; break } }
}
if (-not $Py) { $g = Get-Command python -ErrorAction SilentlyContinue; if ($g) { $Py = $g.Source } }
if (-not $Py) { Log "ERROR: no python found. Pass -Py <path to python.exe>."; exit 1 }
Log "python: $Py"
Log (& $Py -c "import sys, numpy; print('python', sys.version.split()[0], 'numpy', numpy.__version__)")

$nres = (Get-ChildItem (Join-Path $Root "results") -Filter *.json -ErrorAction SilentlyContinue | Measure-Object).Count
$npy = Get-ChildItem (Join-Path $Root "runs") -Recurse -Filter adj_matrices.npy -ErrorAction SilentlyContinue
Log "result json files: $nres"
Log "adj_matrices.npy files: $(($npy | Measure-Object).Count)"
if ($npy) { Log "example: $($npy[0].FullName)" }
$jobs = @(Get-ChildItem $Root -Filter "jobs*.csv" | ForEach-Object { $_.Name })
Log "job lists found: $($jobs -join ', ')"

$out = Join-Path $kit "qG_export"
if (Test-Path $out) { Remove-Item $out -Recurse -Force }   # only this kit's own earlier output
$lines = & $Py (Join-Path $kit "export_qG.py") --root $Root --jobs $jobs --out $out --methods auto
$lines | ForEach-Object { Log ([string]$_) }

$zip = Join-Path $kit "M4_qG_export_return.zip"
Compress-Archive -Path $out, $report -DestinationPath $zip -Force
Log "wrote $zip  ($([math]::Round((Get-Item $zip).Length/1MB,2)) MB)"
Log "DONE. Send M4_qG_export_return.zip back (Drive or mail)."
