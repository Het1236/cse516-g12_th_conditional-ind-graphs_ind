# Second M4 export: EXACT edge probabilities from the saved model.pt files. Read-only on M3 data, no training.
#   powershell -ExecutionPolicy Bypass -File .\run_m4_exact.ps1 -Root D:\Het\rhino_work_transfer\rhino_work
# Result: m4_exact_report.txt and M4_qG_exact_return.zip in this folder. Send the zip back.
param([string]$Root = "D:\rhino_work", [string]$Py = "")
$ErrorActionPreference = "Stop"
$kit = $PSScriptRoot
$report = Join-Path $kit "m4_exact_report.txt"
"M4 exact export report" | Out-File -FilePath $report -Encoding utf8
function Log([string]$m) { Write-Host $m; Add-Content -Path $report -Value $m -Encoding utf8 }
Log "date: $(Get-Date -Format s)   host: $env:COMPUTERNAME   root: $Root"
if (-not (Test-Path $Root)) { Log "ERROR: root not found. Pass -Root <folder with results and runs>."; exit 1 }
if (-not $Py) {
    foreach ($c in @((Join-Path $Root "rhino_env\venv\Scripts\python.exe"), "D:\rhino_env\venv\Scripts\python.exe",
                     (Join-Path (Split-Path $Root -Parent) "rhino_env\venv\Scripts\python.exe"))) { if (Test-Path $c) { $Py = $c; break } }
}
if (-not $Py) { $g = Get-Command python -ErrorAction SilentlyContinue; if ($g) { $Py = $g.Source } }
if (-not $Py) { Log "ERROR: no python found. Pass -Py <path>."; exit 1 }
Log "python: $Py"
Log (& $Py -c "import sys, numpy, torch; print('python', sys.version.split()[0], 'numpy', numpy.__version__, 'torch', torch.__version__)")
$jobs = @(Get-ChildItem $Root -Filter "jobs*.csv" | ForEach-Object { $_.Name })

# smoke test on 3 jobs first
$smoke = Join-Path $kit "qG_exact_smoke"
if (Test-Path $smoke) { Remove-Item $smoke -Recurse -Force }
$l = & $Py (Join-Path $kit "export_exact_q.py") --root $Root --jobs $jobs --out $smoke --methods rhino --max_jobs 3
$l | ForEach-Object { Log ([string]$_) }
if (((Get-ChildItem $smoke -Filter *.npz -ErrorAction SilentlyContinue | Measure-Object).Count) -eq 0) {
    Log "ERROR: smoke test exported nothing. See the lines above (look for FAILED or skip). Stop here and report them."; exit 1 }

$out = Join-Path $kit "qG_exact"
if (Test-Path $out) { Remove-Item $out -Recurse -Force }
$lines = & $Py (Join-Path $kit "export_exact_q.py") --root $Root --jobs $jobs --out $out --methods auto
$lines | ForEach-Object { Log ([string]$_) }
$zip = Join-Path $kit "M4_qG_exact_return.zip"
Compress-Archive -Path $out, $report -DestinationPath $zip -Force
Log "wrote $zip  ($([math]::Round((Get-Item $zip).Length/1MB,2)) MB)"
Log "DONE. Send M4_qG_exact_return.zip back (Drive or mail)."
