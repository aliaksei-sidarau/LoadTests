Here’s a practical plan and how to implement it with k6. Short answer on test type: run a capacity/breakpoint test to discover max sustainable msg/s, plus a shorter spike and a longer soak.

Pick test types
Capacity/breakpoint: ramp message rate until you hit SLO violation (errors/latency) to find max sustainable throughput.
Spike: brief 2–5x burst to verify resilience.
Soak: 1–3 hours at 70–80% of capacity to catch leaks and slowdowns.
Define SLIs/SLOs
Ack/confirm latency p95/p99 (e.g., p95 < 500 ms).
Error rate < 1%.
Connection failure rate < 0.1%.
CPU/RAM/I/O on servers below agreed thresholds.
Model “agent” behavior
Persistent connection per agent.
Handshake (id message), wait for “approved”.
Send length-prefixed JSON batches; wait for “confirm” before next batch.
Pace by events/sec per agent or seconds-between-batches.
Important note about k6 and your protocol
Your Python agents use custom TLS over raw TCP with 4-byte length prefix. k6 core does not support raw TCP/TLS.
Use one of:
If your system can expose a WebSocket or HTTP/gRPC ingress that mirrors this protocol, use k6 (recommended).
Or build k6 with a TCP/TLS extension (xk6). If that’s not an option, keep Python or use Locust (Python) to reuse your existing logic.

-----------------------------------------

Run (Windows PowerShell):

choco install k6 (or download from k6.io)
k6 run -e HOST=wss://your-host:8444/ws -e AGENTS=500 -e BATCH=100 -e SEC_PER_BATCH=0.2 -e TOKEN=abc -e INSECURE_TLS=true load-agents-ws.js
Option B: k6 with TCP/TLS extension (only if WS/HTTP/GRPC is not possible)

Build k6 with a TCP/TLS xk6 extension that can open TLS sockets and send/recv raw bytes.
Implement 4-byte big-endian length prefix framing like your Python code.
If an extension isn’t an option, prefer Locust (Python) and reuse your existing asyncio logic.
Suggested experiment steps

1. Warm-up: 5–10 minutes at expected traffic (e.g., 50% target).
2. Step/capacity: Increase traffic in steps (e.g., +10% every 3–5 minutes) until SLO violation.
3. Spike: Jump to 2× capacity for 1–2 minutes, then back.
4. Soak: Run 1–3 hours at 70–80% of measured capacity.

Measure on server: CPU, RAM, GC, thread pool, sockets, storage I/O, queue depths. Export to Grafana/Prometheus if available.
What to report

Max sustainable msg/s before SLO breach.
p50/p95/p99 confirm latency per step.
Error types and rates (connect, auth, send, confirm timeouts).
Resource headroom at capacity.
If your system only accepts the custom TLS protocol, k6 needs an extension; otherwise, expose WS or gRPC for k6, or stick with Python/Locust for speed of implementation.

