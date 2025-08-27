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
3. Agent_Spike.py
4. Agent_Soak.py

## BeServer
This is a C# app to immitate server backend consuming Agent events (with SSL connection, self-signed certificate).
It allows connections to "localhost: 8444", and approve every message recieved.

## LoadAnalyzer 
This is a C# app to to analyse test output, e.g. 
1. Build heatmap f(x, y) = BestEPS(Agents-Count, Batch-Size)
2. Draw some graphics, etc.

# Tuning OS

## Windows
Check you can have enough descriptors:
```netsh int ipv4 show dynamicport tcp
```netsh int ipv4 set dynamicport tcp start=10000 num=55535

Set execution policy to run script
```Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

