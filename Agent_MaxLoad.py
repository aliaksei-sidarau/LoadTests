import asyncio
import logging
import statistics
from agent_common import AgentConfig, AgentSocket, AppState, FileHelper

# -----------------------------
# Configuration and defaults
# -----------------------------
import argparse
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--agents', type=int, default=200)  # number of concurrent agents
    p.add_argument('--event-batch', type=int, default=100) # events per batch
    p.add_argument('--target-eps', type=float, default=5000) # expected total events/sec (used to set warm-up)
    p.add_argument('--warmup-min', type=float, default=5) # 5–10 minutes recommended
    p.add_argument('--step-min', type=float, default=3) # 3–5 minutes recommended
    p.add_argument('--step-inc', type=float, default=0.10) # +10% per step
    p.add_argument('--slo-p95-sec', type=float, default=0.5) # p95 confirm latency threshold
    p.add_argument('--slo-err-rate', type=float, default=0.01) # <1% errors
    p.add_argument('--save-to', type=str, default=None)  # file to save results
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

    # Phase 2: Step/capacity until SLO breach
    best_sustainable = 0
    best_confirmed = 0
    step_sent = 0
    step_confirmed = 0
    step_p95 = 0
    step_eps = args.target_eps

    i_limit = 1000
    for i in range(1, i_limit + 1):
        step_eps = step_eps * (1.0 + args.step_inc)
        await app_state.set_rate_limit_total(step_eps)
        logging.info("Step: increased total EPS to %.0f, running for %.1f min", step_eps, args.step_min)

        # run this step window
        step_time = args.step_min * 60
        await asyncio.sleep(step_time)

        # evaluate window SLOs
        lats, batches_sent, confirms, errors = app_state.snapshot_and_reset_window()
        p95 = statistics.quantiles(lats, n=100)[94] if len(lats) >= 100 else (max(lats) if lats else 0.0)
        mean_lat = statistics.mean(lats)
        confirmed_eps = confirms * args.event_batch / step_time
        err_rate = (errors / max(1, (confirms + errors)))
        logging.info(
            "Step result: p95=%.3fs, mean_lat=%.1fs sent=%d, confirms=%d, confirmed_eps=%d, errors=%d (err_rate=%.3f)",
            p95, mean_lat, batches_sent, confirms, confirmed_eps, errors, err_rate
        )

        step_sent = batches_sent
        step_confirmed = confirms
        step_p95 = p95
        if best_confirmed < confirmed_eps:
            best_confirmed = confirmed_eps

        if (confirmed_eps < step_eps * 0.85) or (p95 and p95 > args.slo_p95_sec) or (err_rate > args.slo_err_rate):
            logging.warning(
                "SLO breached at EPS=%.0f (eps=%.1f%% of target, p95=%.3fs, err_rate=%.3f). Using previous step as capacity.", 
                confirmed_eps, 100 * confirmed_eps / step_eps, p95, err_rate)
            break

        if (confirmed_eps > best_sustainable):
            best_sustainable = confirmed_eps

        if i == i_limit:
            logging.info("Reached maximum steps (%d).", i_limit)

    if args.save_to:
        FileHelper.save_results_csv(args.save_to,
            ['Agents Count', 'Batch Size', 'Sent', 'Confirmed', 'P95', 'Best Eps', 'Best Confirmed'],
            [args.agents, args.event_batch, step_sent, step_confirmed,"%.2f" % step_p95, "%d" % best_sustainable, "%d" % best_confirmed]
        )

    logging.info("Best sustainable capacity: %.0f EPS", best_sustainable)
    logging.info("Scenario complete. Stopping soon...")

# -----------------------------
# Entrypoint
# -----------------------------
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    
    # Load test parameters (for check)
    #args.agents = 1
    #args.host = '192.168.128.28'
    #args.event_batch = 100
    #args.target_eps = 4000
    #args.warmup_min = 0
    #args.step_min = 0.5
    #args.step_inc = 0.1
    #args.slo_p95_sec = 0.5
    #args.slo_err_rate = 0.01

    config = AgentConfig(args.host, args.port, args.token, args.event_batch)
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
        #Uvloop is not supported on windows
        #import uvloop
        #asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
