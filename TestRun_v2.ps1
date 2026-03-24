
function Run_LoadTest_v2 {
    param (
        [int]$Agents,
        [int]$EventBatch,
        [int]$SpawnRate = 10
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

    Write-Host "Run_LoadTest -Agents $Agents -EventBatch $EventBatch" -ForegroundColor Magenta

    python Agent_MaxLoad_v2.py --agents $Agents --event-batch $EventBatch `
        --save-to results_v2.csv --spawn-rate $SpawnRate `
        --token LAXKXE64FYRPOTTDOINEZLPPI2L3TAXHCFQHAAV5EBDV2UBQSWNQ --host 192.168.128.59
        # --token JLE7EJNWIF653VMM6RNL66FEOBY5JUU4CXIPXILA2P3JDHK75NMQ --host 127.0.0.1
        
    if ($LASTEXITCODE -ne 0) { Write-Host "Python script failed"; exit 1 }
}

Write-Host "=== Load Test Batch Runner ==="
Write-Host "Starting tests at $(Get-Date)"
Write-Host "Report will be saved to results_v2.csv"
Write-Host "=============================="

#Run_LoadTest_v2 -Agents 1 -EventBatch 1
#Run_LoadTest_v2 -Agents 10 -EventBatch 10
Run_LoadTest_v2 -Agents 10 -EventBatch 1000
#Run_LoadTest_v2 -Agents 200 -EventBatch 1 -SpawnRate 20
#Run_LoadTest_v2 -Agents 300 -EventBatch 100 -SpawnRate 30
#Run_LoadTest_v2 -Agents 500 -EventBatch 100 -SpawnRate 50
#Run_LoadTest_v2 -Agents 700 -EventBatch 100 -SpawnRate 50
#Run_LoadTest_v2 -Agents 1000 -EventBatch 1 -SpawnRate 100
