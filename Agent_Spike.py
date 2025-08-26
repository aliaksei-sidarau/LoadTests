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
    p.add_argument('--spikes', type=int, default=2) # 2-3 time
    p.add_argument('--spike-x', type=float, default=2.0) # 2× capacity
    p.add_argument('--spike-min', type=float, default=2) # 1–2 minutes
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
        log_stats(app_state)

    # Phase 2: Spike to SPIKE_× of capacity
    for spike_num in range(1, args.spikes + 1):
        spike_eps = args.target_eps * args.spike_x
        await app_state.set_rate_limit_total(spike_eps)
        logging.info(
            "Spike #%d setting total EPS to %.1fx of %.0f for %.1f min",
            spike_num, args.spike_x, args.target_eps, args.spike_min
        )
        await asyncio.sleep(args.spike_min * 60)
        log_stats(app_state)

        # Return to capacity quickly (optional small settle)
        logging.info("Spike #%d: mitigate load to 70%% of %.0f for 30 secs", spike_num, args.target_eps)
        await app_state.set_rate_limit_total(args.target_eps * 0.7)
        await asyncio.sleep(30)
        log_stats(app_state)

    logging.info("Scenario complete. Stopping soon...")

def log_stats(app_state: AppState):
    _, low_send_rates, confirms, errors = app_state.snapshot_and_reset_window()
    err_rate = (errors / max(1, (confirms + errors)))
    logging.info("Step result: confirms=%d, errors=%d (err_rate=%.3f)", confirms, errors, err_rate)
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
    args.spikes = 3
    args.spike_x = 2.0
    args.spike_min = 2.0

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
