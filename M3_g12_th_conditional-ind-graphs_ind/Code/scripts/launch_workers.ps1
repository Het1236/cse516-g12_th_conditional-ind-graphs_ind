# Start N detached worker processes (they keep running if you close the window).
# Usage (from rhino_work):  .\scripts\launch_workers.ps1 -Workers 6 -Threads 2 -EnvDir D:\rhino_env -Jobs jobs.csv
# Optional for two machines: -Part 0 -Of 2 on machine A and -Part 1 -Of 2 on machine B.
param(
    [int]$Workers = 4,
    [int]$Threads = 2,
    [string]$EnvDir = "D:\rhino_env",
    [string]$Jobs = "jobs.csv",
    [int]$Part = 0,
    [int]$Of = 1,
    [double]$TimeoutHours = 24
)
$root = (Resolve-Path "$PSScriptRoot\..").Path
$py = "$EnvDir\venv\Scripts\python.exe"
New-Item -ItemType Directory -Force "$root\logs" | Out-Null
for ($i = 0; $i -lt $Workers; $i++) {
    $args = @("-u", "scripts\worker.py", "--jobs", $Jobs, "--threads", $Threads, "--timeout_h", $TimeoutHours, "--part", $Part, "--of", $Of)
    Start-Process -FilePath $py -WorkingDirectory $root -ArgumentList $args -WindowStyle Hidden `
        -RedirectStandardOutput "$root\logs\worker_$i.out" -RedirectStandardError "$root\logs\worker_$i.err"
    Start-Sleep -Seconds 5   # stagger so claims and imports do not collide
}
"$Workers workers started. Progress: Get-ChildItem results\*.json | Measure-Object ; python scripts\collect.py"
