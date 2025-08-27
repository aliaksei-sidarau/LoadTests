
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
        --save-to results_maxBe_r.csv --warmup-min $WarmupMin --step-min 0.5 --step-inc 0.1 --slo-p95-sec 30.0 `
        --token MG2LIICYMYF4ANGRNUSQXWYAZTSK67DHSBFDRCZWEBQZEB6RUJKQ
    if ($LASTEXITCODE -ne 0) { Write-Host "Python script failed"; exit 1 }
}

Write-Host "=== Load Test Batch Runner ==="
Write-Host "Starting tests at $(Get-Date)"
Write-Host "Report will be saved to results_maxBe_r.csv"
Write-Host "=============================="

<#
Run_LoadTest -Agents 1 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 1 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 1 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 1 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 1 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 1 -EventBatch 5000 -Eps 10000000

Run_LoadTest -Agents 10 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 10 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 10 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 10 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 10 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 10 -EventBatch 5000 -Eps 10000000

Run_LoadTest -Agents 100 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 100 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 100 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 100 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 100 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 100 -EventBatch 5000 -Eps 10000000

Run_LoadTest -Agents 500 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 500 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 500 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 500 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 500 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 500 -EventBatch 5000 -Eps 10000000

Run_LoadTest -Agents 1000 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 1000 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 1000 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 1000 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 1000 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 1000 -EventBatch 5000 -Eps 10000000

Run_LoadTest -Agents 5000 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 5000 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 5000 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 5000 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 5000 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 5000 -EventBatch 5000 -Eps 10000000

Run_LoadTest -Agents 10000 -EventBatch 10 -Eps 10000000
Run_LoadTest -Agents 10000 -EventBatch 100 -Eps 10000000
Run_LoadTest -Agents 10000 -EventBatch 500 -Eps 10000000
Run_LoadTest -Agents 10000 -EventBatch 1000 -Eps 10000000
Run_LoadTest -Agents 10000 -EventBatch 3000 -Eps 10000000
Run_LoadTest -Agents 10000 -EventBatch 5000 -Eps 10000000
#>
