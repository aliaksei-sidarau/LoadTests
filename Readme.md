# App Components
This complex combined solution should allow us to test load to our cluster. 
It cosists of 2 parts: Generator (python) and BE server (C#) for generator load testing.

## Python generator:
1. agent_common.py - common logic. Contains
    - AgentConfig, 
    - AgentSocket,
    - AppState,
    - FileHelper (to write results to csv)
2. Agent_MaxLoad.py - load test, monotonically increase rate of EPS to find max.
3. Agent_MaxLoad_v1.py - load test, with interactive change of Agents count and Batch size.
4. Agent_Spike.py
5. Agent_Soak.py

## BeServer
This is a C# app to immitate server backend consuming Agent events (with SSL connection, self-signed certificate).
It allows connections to "localhost: 8444", and approve every message recieved.

## LoadAnalyzer 
This is a C# app to to analyse test output, e.g. 
1. Build heatmap f(x, y) = BestEPS(Agents-Count, Batch-Size)
2. Draw some graphics, etc.

## Locust
Locust load tests, based on AgentUser.
``` pip install locust
``` locust -f Locust/AgentB300.py

1. AgentUser.py - basic file with Agent logic. Support socket TLS connection to MC console.
2. AgentB10.py - simple load test with 10 epb (events per batch)
3. AgentB100.py - load test with 100 epb and StageShape (100 users every 10s, by 100 per time)
4. AgentB300.py - load test with 300 epb and StageShape (100 users every 10s, by 100 per time)
5. AgentB500.py - load test with 500 epb and StageShape (100 users every 10s, by 100 per time)
6. AgentB1000.py - load test with 1000 epb and StageShape (100 users every 10s, by 100 per time)
7. AgentB3000.py - load test with 3000 epb and StageShape (steps by dictionary)

# Tuning OS

## Windows
Check you can have enough descriptors:
```netsh int ipv4 show dynamicport tcp
```netsh int ipv4 set dynamicport tcp start=10000 num=55535

Set execution policy to run script
```Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

