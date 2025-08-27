
function Run_LoadTest {
    param (
        [int]$Agents,
        [int]$EventBatch,
        [int]$Eps,
        [float]$WarmupMin = 0.0
    )
    $HostPath = "E:\PROJECTS\LoadTests\data\reporting.db"
    $ContainerId = "ab157e9a54a5f24165043883a81ba5479dc928244d4d6304a365e55b820ea6b7"
    $ContainerPath = "/app/var/mchost"

    #docker exec $ContainerId rm -f "$($ContainerPath)/reporting.db"
    #if ($LASTEXITCODE -ne 0) { Write-Host "docker exec rm failed 1"; exit 1 }

    #docker exec $ContainerId rm -f "$($ContainerPath)/reporting.db.wal"
    #if ($LASTEXITCODE -ne 0) { Write-Host "docker exec rm failed 2"; exit 1 }

    #docker cp $HostPath "$($ContainerId):$($ContainerPath)/reporting.db"
    #if ($LASTEXITCODE -ne 0) { Write-Host "docker cp failed"; exit 1 }

    Write-Host "Run_LoadTest -Agents $Agents -EventBatch $EventBatch -Eps $Eps" -ForegroundColor Magenta

    python Agent_MaxLoad.py --agents $Agents --event-batch $EventBatch --target-eps $Eps `
        --save-to results.csv --warmup-min $WarmupMin --step-min 0.5 --step-inc 0.1 --slo-p95-sec 60.0 `
        --token 6ULPCCQQRPE7WH7FLKSDCDGV7KMCZQCUL5JLY5GNKQTDWJ3Y7BWQ --host 192.168.128.28
    if ($LASTEXITCODE -ne 0) { Write-Host "Python script failed"; exit 1 }
}

Write-Host "=== Load Test Batch Runner ==="
Write-Host "Starting tests at $(Get-Date)"
Write-Host "Report will be saved to _data/output/results.csv"
Write-Host "=============================="

<#  1.2mln
Run_LoadTest -Agents 1 -EventBatch 10 -Eps 200
Run_LoadTest -Agents 1 -EventBatch 100 -Eps 4000
Run_LoadTest -Agents 1 -EventBatch 500 -Eps 10000
Run_LoadTest -Agents 1 -EventBatch 1000 -Eps 15000
Run_LoadTest -Agents 1 -EventBatch 3000 -Eps 18000
Run_LoadTest -Agents 1 -EventBatch 5000 -Eps 20000
#>

<#  12mln
Run_LoadTest -Agents 10 -EventBatch 10 -Eps 1200
Run_LoadTest -Agents 10 -EventBatch 100 -Eps 9000
Run_LoadTest -Agents 10 -EventBatch 500 -Eps 20000
Run_LoadTest -Agents 10 -EventBatch 1000 -Eps 35000
Run_LoadTest -Agents 10 -EventBatch 3000 -Eps 50000
Run_LoadTest -Agents 10 -EventBatch 5000 -Eps 55000
#>

<# 13mln
Run_LoadTest -Agents 100 -EventBatch 10 -Eps 1000
Run_LoadTest -Agents 100 -EventBatch 100 -Eps 10000
Run_LoadTest -Agents 100 -EventBatch 500 -Eps 30000
Run_LoadTest -Agents 100 -EventBatch 1000 -Eps 40000
Run_LoadTest -Agents 100 -EventBatch 3000 -Eps 40000
Run_LoadTest -Agents 100 -EventBatch 5000 -Eps 40000
#>

<#
Run_LoadTest -Agents 500 -EventBatch 10 -Eps 2000
Run_LoadTest -Agents 500 -EventBatch 100 -Eps 10000
Run_LoadTest -Agents 500 -EventBatch 500 -Eps 20000
Run_LoadTest -Agents 500 -EventBatch 1000 -Eps 30000
Run_LoadTest -Agents 500 -EventBatch 3000 -Eps 25000
Run_LoadTest -Agents 500 -EventBatch 5000 -Eps 25000
#>

Run_LoadTest -Agents 500 -EventBatch 5000 -Eps 100000

<#
Run_LoadTest -Agents 1000 -EventBatch 10 -Eps 1000
Run_LoadTest -Agents 1000 -EventBatch 100 -Eps 5000
Run_LoadTest -Agents 1000 -EventBatch 500 -Eps 1200
Run_LoadTest -Agents 1000 -EventBatch 1000 -Eps 6000
Run_LoadTest -Agents 1000 -EventBatch 3000 -Eps 7000
#>

<#
Run_LoadTest -Agents 5000 -EventBatch 10 -Eps 1500
Run_LoadTest -Agents 5000 -EventBatch 100 -Eps 7000
Run_LoadTest -Agents 5000 -EventBatch 500 -Eps 2000
Run_LoadTest -Agents 5000 -EventBatch 1000 -Eps 7000
Run_LoadTest -Agents 5000 -EventBatch 3000 -Eps 8000
#>
