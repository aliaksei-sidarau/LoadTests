import asyncio
from collections import deque
import secrets
import time
import signal
from agent_common import AgentMessageHelper, AgentConfig

import argparse
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--agents', type=int, default=100)  # number of concurrent agents
    p.add_argument('--spawn-rate', type=int, default=10) # add agents per/sec
    p.add_argument('--event-batch', type=int, default=100) # events per batch
    p.add_argument('--save-to', type=str, default=None)  # file to save results
    p.add_argument('--host', type=str, default='192.168.128.28')
    p.add_argument('--port', type=int, default=8444)
    p.add_argument('--token', type=str, default='SEZVCZKTMIZBQ2PKRV5BAWWFYAKFS4CC26REFJEG3HRAHB6CYROQ')
    return p.parse_args()

# --- Скользящее окно для подсчета events/sec ---
agent_config: AgentConfig = None
events_window: deque = deque(maxlen=10000)
args = parse_args()

# --- TCP-клиент с корректной остановкой ---
async def tcp_client(config: AgentConfig, stop_event):
    writer = None
    confirmation_id = 0
    client_id = secrets.token_hex(8).upper()

    try:
        reader, writer = await asyncio.open_connection(
            config.host, config.port, ssl=config.ssl_context)

        await TcpClientHelper.authenticate(
            client_id, reader, writer, config.token)

        while not stop_event.is_set():
            confirmation_id += 1
            batch = AgentMessageHelper.make_events_batch(
                config.batch_size, confirmation_id)

            await AgentMessageHelper.send_message(writer, batch)
            if stop_event.is_set():
                break

            ack = await TcpClientHelper.read_batch_ack_msg(reader)
            if not ack:
                raise Exception("No batch ACK from server")

            events_window.append(time.time())
            if stop_event.is_set():
                break
            #await asyncio.sleep(0)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[Client {client_id}] error: {e}")
    finally:
        if writer:
            writer.close()
            await writer.wait_closed()

# --- Помощник TCP-клиента --- #
class TcpClientHelper:
    @staticmethod
    async def authenticate(client_id: str, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, token: str, max_try: int = 3) -> None:
        name = f"FakeAgent_{client_id}"
        peerid = f"EA2ULYEX7D6TG4MA{client_id}"

        auth_msg = AgentMessageHelper.make_id_msg(name, peerid, token)
        await AgentMessageHelper.send_message(writer, auth_msg)

        ack = await AgentMessageHelper.read_message(reader)
        while not '"subsystem":"auth"' in ack and not '"status":"approved"' in ack:
            max_try -= 1
            if max_try <= 0:
                return None
            ack = await AgentMessageHelper.read_message(reader)
        if not ack:
            raise Exception("No auth ACK from server")

    @staticmethod
    async def read_batch_ack_msg(reader: asyncio.StreamReader, max_try: int = 3):
        msg = await AgentMessageHelper.read_message(reader)
        while not '"m":"confirm"' in msg:
            max_try -= 1
            if max_try <= 0:
                return None
            msg = await AgentMessageHelper.read_message(reader)
        return msg

# --- Монитор rps и event loop lag ---
async def monitor(config: AgentConfig, stop_event):
    while not stop_event.is_set():
        start = time.time()
        await asyncio.sleep(0)

        now = time.time()
        lag = (now - start) * 1000  # мс
        rps = 0.0
        if len(events_window) > 1:
            duration = now - events_window[0]
            rps = len(events_window) / duration if duration > 0 else 0
            #events_window.clear()

        tasks_count = len(asyncio.all_tasks()) - 2
        print(f"Users: {tasks_count}, Epb: {config.batch_size}, " +
              f"Req/s: {rps:.2f}, Events/sec: {rps * config.batch_size:.2f}, "+
              f"Event loop lag: {lag:.2f}ms", end='\r')
        await asyncio.sleep(2)

# --- Постепенное наращивание агентов ---
async def ramp_up_agents(config: AgentConfig, target_agents, spawn_rate, stop_event):
    tasks = []
    while not stop_event.is_set() and len(tasks) < target_agents:
        new_agents = min(spawn_rate, target_agents - len(tasks))
        if new_agents > 0:
            for _ in range(new_agents):
                task = asyncio.create_task(tcp_client(config, stop_event))
                tasks.append(task)
            await asyncio.sleep(1)
    return tasks

# --- Key listener ---
import msvcrt
import threading
stop_event = asyncio.Event()
batch_sizes = [10, 100, 200, 300, 500, 700, 1000]

def keyboard_listener(config: AgentConfig):
    print("Press + or - to change batch size. Press q to quit.")
    while True:
        if msvcrt.kbhit():
            try:
                key = msvcrt.getch().decode('utf-8')
                if key == '+':
                    config.batch_size = get_next_size(config.batch_size)
                    print(f"\nBatch size increased to {config.batch_size}")
                elif key == '-':
                    config.batch_size = get_next_size(config.batch_size, greater=False)
                    print(f"\nBatch size decreased to {config.batch_size}")
                elif key == 'q':
                    print("\nExiting keyboard listener.")
                    stop_event.set()
                    break
            except Exception as e:
                pass

def get_next_size(current_size, greater: bool = True):
    if greater:
        for _, x in enumerate(batch_sizes):
            if x > current_size:
                return x
    else:
        for _, x in enumerate(reversed(batch_sizes)):
            if x < current_size:
                return x
    return current_size

# --- Основная функция ---
async def main():
    #args.agents = 10
    #args.spawn_rate = 10
    #args.event_batch = 10
    #args.host = '192.168.128.28'
    #args.event_batch = 100
    agent_config = AgentConfig(args.host, args.port, args.token, args.event_batch)
    listener_thread = threading.Thread(
        target=keyboard_listener,
        args=[agent_config],
        daemon=True
    )
    listener_thread.start()

    monitor_task = asyncio.create_task(monitor(agent_config, stop_event))
    agent_tasks = await ramp_up_agents(
        agent_config, args.agents, args.spawn_rate, stop_event)

    # ожидание завершения или Ctrl+C
    await stop_event.wait()
    print("\nStopping agents...")

    # отменяем все агентские задачи
    for task in agent_tasks:
        task.cancel()
    await asyncio.gather(*agent_tasks, return_exceptions=True)

    monitor_task.cancel()
    await asyncio.gather(monitor_task, return_exceptions=True)

    print("All agents stopped and connections closed.")

if __name__ == "__main__":
    try:
        #Uvloop does not support windows
        #import uvloop
        #asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        stop_event.set()
        pass