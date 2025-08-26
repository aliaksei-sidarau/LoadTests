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
    p.add_argument('--soak-frac', type=float, default=0.75) # 70–80% of capacity
    p.add_argument('--soak-min', type=float, default=60) # 1–3 hours recommended (set 60 for demo)
    p.add_argument('--host', type=str, default='127.0.0.1')
    p.add_argument('--port', type=int, default=8444)
    p.add_argument('--token', type=str, default='MG2LIICYMYF4ANGRNUSQXWYAZTSK67DHSBFDRCZWEBQZEB6RUJKQ')
    #p.add_argument('--token', type=str, required=True)
    return p.parse_args()

args = parse_args()

# -----------------------------
# Scenario controller
# -----------------------------
async def scenario_controller(app_state: AppState):
    # Phase 1: Warm-up at 50% of target capacity
    if args.warmup_min > 0:
        warmup_eps = args.target_eps * 0.5
        await app_state.set_rate_limit_total(warmup_eps)
        logging.info("Warm-up: setting total EPS to %.0f for %.1f min", warmup_eps, args.warmup_min)
        await asyncio.sleep(args.warmup_min * 60)
        log_stats(app_state, int(args.soak_min * 60))

    # Phase 2: Soak at 70–80% of capacity
    soak_eps = args.target_eps * args.soak_frac
    await app_state.set_rate_limit_total(soak_eps)
    logging.info("Soak: setting total EPS to %.0f for %.1f min", soak_eps, args.soak_min)

    interval = 30 # Log stats every 30 seconds
    soak_seconds = int(args.soak_min * 60)
    while soak_seconds > 0:
        time_to_sleep = interval
        if soak_seconds < interval:
            time_to_sleep = soak_seconds
        await asyncio.sleep(time_to_sleep)
        soak_seconds -= time_to_sleep
        log_stats(app_state, soak_seconds)

    logging.info("Scenario complete. Stopping soon...")

def log_stats(app_state: AppState, time_left_seconds: int):
    _, low_send_rates, confirms, errors = app_state.snapshot_and_reset_window()
    err_rate = (errors / max(1, (confirms + errors)))
    hours, remainder = divmod(time_left_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    logging.info("Step result: confirms=%d, errors=%d (err_rate=%.3f), %s time left", confirms, errors, err_rate, time_str)
    if len(low_send_rates) > 0:
            logging.warning("Low send rate detected: %d (rate_dev=%.3f)",
                len(low_send_rates), statistics.mean(low_send_rates))

# -----------------------------
# Entrypoint
# -----------------------------
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    args.agents = 100
    args.event_batch = 100
    args.target_eps = 10000
    args.soak_frac = 0.75
    args.soak_min = 60

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
    await asyncio.sleep(3) # Allow some time for agents to finish
    await asyncio.gather(*[agent.disconnect() for agent in agents]);

    # Wait for all agents to finish
    await asyncio.gather(*agent_tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
