import asyncio
import logging
import statistics
from agent_common import AgentConfig, AgentSocket, AppState

# -----------------------------
# Configuration and defaults
# -----------------------------
import argparse
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--agents', type=int, default=200)  # number of concurrent agents
    p.add_argument('--event-batch', type=int, default=100) # events per batch
    p.add_argument('--target-eps', type=float, default=5000) # expected total events/sec (used to set warm-up)
    p.add_argument('--warmup-min', type=float, default=1) # 5–10 minutes recommended
    p.add_argument('--step-min', type=float, default=3) # 3–5 minutes recommended
    p.add_argument('--step-inc', type=float, default=0.10) # +10% per step
    p.add_argument('--spike-x', type=float, default=2.0) # 2× capacity
    p.add_argument('--spike-min', type=float, default=2) # 1–2 minutes
    p.add_argument('--soak-frac', type=float, default=0.75) # 70–80% of capacity
    p.add_argument('--soak-min', type=float, default=60) # 1–3 hours recommended (set 60 for demo)
    p.add_argument('--slo-p95-sec', type=float, default=0.5) # p95 confirm latency threshold
    p.add_argument('--slo-err-rate', type=float, default=0.01) # <1% errors
    p.add_argument('--host', type=str, default='127.0.0.1')
    p.add_argument('--port', type=int, default=8444)
    p.add_argument('--token', type=str, default='SUAYNE4444LBE2SOTESC2DO5UVDTFWVWJKQ3T2OXQE2MGZ53Y3XQ')
    #p.add_argument('--token', type=str, required=True)
    return p.parse_args()

args = parse_args()

# -----------------------------
# Scenario controller
# -----------------------------
async def scenario_controller(app_state: AppState):
    # Phase 1: Warm-up at 50% of target capacity
    warmup_eps = args.target_eps * 0.5
    await app_state.set_rate_limit_total(warmup_eps)
    logging.info("Warm-up: setting total EPS to %.0f for %.1f min", warmup_eps, args.warmup_min)
    await asyncio.sleep(args.warmup_min * 60)

    # Phase 2: Step/capacity until SLO breach
    step_eps = warmup_eps
    best_sustainable = step_eps
    while True:
        step_eps = step_eps * (1.0 + args.step_inc)
        await app_state.set_rate_limit_total(step_eps)
        logging.info("Step: increased total EPS to %.0f, running for %.1f min", step_eps, args.step_min)

        # run this step window
        await asyncio.sleep(args.step_min * 60)

        # evaluate window SLOs
        lats, confirms, errors = app_state.snapshot_and_reset_window()
        p95 = statistics.quantiles(lats, n=100)[94] if len(lats) >= 100 else (max(lats) if lats else 0.0)
        err_rate = (errors / max(1, (confirms + errors)))
        logging.info("Step result: p95=%.3fs, confirms=%d, errors=%d (err_rate=%.3f)",
                     p95, confirms, errors, err_rate)

        if (p95 and p95 > args.slo_p95_sec) or (err_rate > args.slo_err_rate):
            logging.warning("SLO breached at EPS=%.0f (p95=%.3fs, err_rate=%.3f). Using previous step as capacity.",
                            step_eps, p95, err_rate)
            break
        best_sustainable = step_eps

    # Phase 3: Spike to 2× capacity
    spike_eps = best_sustainable * args.spike_x
    await app_state.set_rate_limit_total(spike_eps)
    logging.info("Spike: setting total EPS to %.0f for %.1f min", spike_eps, args.spike_min)
    await asyncio.sleep(args.spike_min * 60)

    # Return to capacity quickly (optional small settle)
    await app_state.set_rate_limit_total(best_sustainable)
    await asyncio.sleep(10)

    # Phase 4: Soak at 70–80% of capacity
    soak_eps = best_sustainable * args.soak_frac
    await app_state.set_rate_limit_total(soak_eps)
    logging.info("Soak: setting total EPS to %.0f for %.1f min", soak_eps, args.soak_min)
    await asyncio.sleep(args.soak_min * 60)

    logging.info("Best sustainable capacity: %.0f EPS", best_sustainable)
    logging.info("Scenario complete. Stopping soon...")

# -----------------------------
# Entrypoint
# -----------------------------
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    config = AgentConfig(args.host, args.port, args.token)
    app_state = AppState(args.agents, args.event_batch)

    agents = [AgentSocket(config, app_state) for _ in range(args.agents)]

    # Start agent tasks
    agent_tasks = [asyncio.create_task(agent.start()) for agent in agents]

    # Start scenario controller
    scenario_task = asyncio.create_task(scenario_controller(app_state))

    # Wait for scenario to finish
    await scenario_task

    # Signal to stop and disconnect agents
    app_state.signalToStop()
    await asyncio.gather(*[agent.disconnect() for agent in agents]);

    # Wait for all agents to finish
    await asyncio.gather(*agent_tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
