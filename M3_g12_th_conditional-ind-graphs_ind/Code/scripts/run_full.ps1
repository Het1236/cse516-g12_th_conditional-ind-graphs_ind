# Unattended full run. Keeps N workers busy on jobs.csv, keeps the PC awake while it runs, and calls collect.py at the end.
# Start detached from any terminal (from rhino_work):
#   Start-Process powershell -WindowStyle Hidden -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File scripts\run_full.ps1'
# Stop everything: stop the worker.py processes and then this script (it is a powershell running run_full.ps1).
param(
    [int]$Workers = 16,
    [int]$Threads = 2,
    [string]$Jobs = "jobs.csv",
    [double]$TimeoutHours = 24
)
$root = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $root
$py = "$root\rhino_env\venv\Scripts\python.exe"
Add-Type -Namespace Win -Name Power -MemberDefinition '[System.Runtime.InteropServices.DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f);'
$ids = (Import-Csv $Jobs).job_id
$log = "$root\logs\run_full.log"
function Say($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Add-Content $log }
Say "run_full start: $($ids.Count) jobs, target $Workers workers x $Threads threads"
$n = 0
while ($true) {
    [void][Win.Power]::SetThreadExecutionState(0x80000001)   # ES_CONTINUOUS | ES_SYSTEM_REQUIRED: no sleep while this loop runs
    $done = 0; $open = 0
    foreach ($id in $ids) {
        if (Test-Path "$root\results\$id.json") { $done++ }
        elseif (-not (Test-Path "$root\results\$id.claim")) { $open++ }
    }
    $running = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'venv\\Scripts\\python\.exe.*scripts.worker\.py' }).Count
    if ($done -ge $ids.Count) { break }
    if ($open -eq 0 -and $running -eq 0) { Say "no workers and no open jobs left; $done of $($ids.Count) done (rest are crashed claims or still-missing results)"; break }
    $want = [Math]::Min($Workers - $running, $open)
    for ($i = 0; $i -lt $want; $i++) {
        $n++
        $a = @("-u", "scripts\worker.py", "--jobs", $Jobs, "--threads", $Threads, "--timeout_h", $TimeoutHours)
        Start-Process -FilePath $py -WorkingDirectory $root -ArgumentList $a -WindowStyle Hidden `
            -RedirectStandardOutput "$root\logs\full_worker_$n.out" -RedirectStandardError "$root\logs\full_worker_$n.err"
        Start-Sleep -Seconds 5
    }
    if ($want -gt 0) { Say "started $want workers (running before: $running, open jobs: $open, done: $done)" }
    Start-Sleep -Seconds 60
}
Say "finished loop: $done of $($ids.Count) results"
& $py scripts\collect.py *>&1 | Add-Content $log
Say "collect.py done. See results_all.csv"
[void][Win.Power]::SetThreadExecutionState(0x80000000)
