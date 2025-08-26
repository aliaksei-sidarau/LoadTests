import asyncio
import collections
import ssl
import secrets
import datetime
import logging
import os
import csv
from typing import Optional

# -----------------------------
# App state and stats
# -----------------------------
class AppState:
    def __init__(self, agents_count: int, events_per_batch: int) -> None:
        self._stop = False
        self._ready = False
        self._agents_approved = 0

        self._agents_count = agents_count
        self._events_per_batch = events_per_batch
        self._rate_limit_total_eps = 0.0  # total events/sec budget across all agents, live-updated

        # Stats
        self._batches_sent = 0
        self._confirms = 0
        self._errors = 0
        # Keep moderate list size to bound memory; only p95 needs a few thousand
        self._deque_max_len = 5000
        self._confirm_latencies = collections.deque(maxlen=self._deque_max_len)

        # Protect against rare cross-task races; most ops are single-threaded in the event loop
        self._change_rate_lock = asyncio.Lock()

    @property
    def stopped(self) -> bool:
        return self._stop
    
    def signalToStop(self) -> None:
        self._stop = True
   
    @property
    def ready(self) -> bool:
        return self._ready

    @property
    def events_per_batch(self) -> int:
        return self._events_per_batch

    @property
    def rate_limit_per_agent_eps(self) -> float:
        if self._agents_count == 0:
            return 0.0
        return self._rate_limit_total_eps / self._agents_count

    def is_changing_rate(self) -> bool:
        return self._change_rate_lock.locked()

    async def set_rate_limit_total(self, eps: float, change_rate_delay: float = 5.0) -> None:
        async with self._change_rate_lock:
            self._rate_limit_total_eps = max(0.0, eps)
            await asyncio.sleep(change_rate_delay)
            self.snapshot_and_reset_window()

    def on_agent_approved(self) -> None:
        self._agents_approved += 1
        #logging.info("Agents approved: %d/%d", self._agents_approved, self._agents_count)
        if self._agents_approved == self._agents_count:
            self._ready = True
            logging.info("All agents approved, starting traffic...")

    def on_batch_sent(self) -> None:
        self._batches_sent += 1

    def on_error(self) -> None:
        self._errors += 1

    def on_low_send_rate(self) -> None:
        pass

    def on_confirm_latency(self, seconds: float) -> None:
        self._confirm_latencies.append(seconds)

    def on_confirm(self):
        self._confirms += 1

    def snapshot_and_reset_window(self) -> tuple[collections.deque, int, int, int, str]:
        # Called by scenario controller at step boundaries
        lats = self._confirm_latencies
        batches_sent = self._batches_sent
        confirms = self._confirms
        errors = self._errors
        self._confirm_latencies = collections.deque(maxlen=self._deque_max_len)
        self._batches_sent = 0
        self._confirms = 0
        self._errors = 0
        return lats, batches_sent, confirms, errors
    
    async def start_stats(self) -> None:
        # Periodic overall stats
        while not self._ready and not self._stop:
            await asyncio.sleep(2)

        last_check = datetime.datetime.now()
        last_events_count = self._events_sent

        while not self._stop:
            await asyncio.sleep(5)

            now = datetime.datetime.now()
            delta = (now - last_check).total_seconds()
            last_check = now

            delta_events = self._events_sent - last_events_count
            last_events_count = self._events_sent

            eps = delta_events / delta if delta > 0 else 0.0
            logging.info("Events sent total: %d, recent rate: %.1f events/sec", self._events_sent, eps)

# -----------------------------
# File logic
# -----------------------------
class FileHelper:
    @staticmethod
    def save_results_csv(filename: str, titles: tuple[str, ...], data: tuple):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, filename)
        file_exists = os.path.isfile(filename)
        with open(filename, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(titles)

            writer.writerow(data)

# -----------------------------
# Agent logic
# -----------------------------
class AgentConfig:
    def __init__(self, host, port, token) -> None:
        self._host = host
        self._port = port
        self._token = token

        self._ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self._ssl_ctx.check_hostname = False
        self._ssl_ctx.verify_mode = ssl.VerifyMode.CERT_NONE

    @property
    def host(self): return self._host
    @property
    def port(self): return self._port
    @property
    def token(self): return self._token
    @property
    def ssl_context(self): return self._ssl_ctx

class AgentMessageHelper:
    @staticmethod
    async def send_id_message(
        writer: asyncio.StreamWriter,
        name: str, peerid: str, token: str) -> None:

        id_msg = """{
            "bind_port": 22676,
            "can_restart": false,
            "client_token": "",
            "bootstrap_token": "%TOKEN%",
            "cpu_model": "Intel(R) Core(TM) i7-6700 CPU @ 3.40GHz",
            "hostname": "%NAME%",
            "m": "id",
            "macros": {
                "%DOWNLOADS%": "C:\\\\Users\\\\WDAGUtilityAccount\\\\Downloads",
                "%FOLDERS_STORAGE%": "",
                "%HOME%": "C:\\\\Users\\\\WDAGUtilityAccount",
                "%USERPROFILE%": "C:\\\\Users\\\\WDAGUtilityAccount",
                "/": "\\\\"
            },
            "name": "%NAME%",
            "os": "win64",
            "os_user": "WDAGUtilityAccount",
            "os_version": "10.0.19041_workstation_x64",
            "peer": "%PEERID%",
            "settings": {
                "bandwidth": {
                    "down": -1,
                    "up": -1
                },
                "foldersStorage": "",
                "restrictedAccess": false
            },
            "storage": "C:\\\\Users\\\\WDAGUtilityAccount\\\\Downloads",
            "tags": [],
            "initialTags": {
                "VIRTUAL": "true"
            },
            "ts": 1674567131,
            "uiv": "3.5.0.1111",
            "v": "3.5.0.1111"
        }""".replace('%NAME%', name).replace('%PEERID%', peerid).replace('%TOKEN%', token)
        await AgentMessageHelper.send_message(writer, id_msg)

    @staticmethod
    async def send_message(writer: asyncio.StreamWriter, msg: str) -> None:
        if writer is None:
            return
        msg_bytes = msg.encode()
        msg_len = len(msg_bytes).to_bytes(4, byteorder="big")
        writer.write(msg_len + msg_bytes)
        await writer.drain()

    @staticmethod
    async def read_message(reader: asyncio.StreamReader) -> str:
        if reader is None:
            return ""
        size_bytes = await reader.readexactly(4)
        size = int.from_bytes(size_bytes, byteorder="big")
        echo_data = await reader.readexactly(size)
        return echo_data.decode("utf-8")

    @staticmethod
    def make_event(ts: int) -> str:
        return f'{{"id":0,"eid":1,"ts":{ts},"tick":0,"t":3,"e":"Startup","src":"App","data":{{"time":0}}}}'

    @staticmethod
    def make_events_batch(events_count: int, confirmationId: int) -> str:
        ts = int(datetime.datetime.now().timestamp())
        events = ",".join(AgentMessageHelper.make_event(ts) for _ in range(events_count))
        return f'{{"m":"events","priority":0,"ts":{ts},"events":[{events}],"confirmId":"{confirmationId}"}}'

class AgentSocket:
    def __init__(self, config: AgentConfig, app_state: AppState) -> None:
        self._config = config
        self._app_state = app_state

        suffix = secrets.token_hex(8).upper()
        self._name = f"FakeAgent_{suffix}"
        self._peerid = f"EA2ULYEX7D6TG4MA{suffix}"

        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

        self._ready = False
        self._confirmationId = 1
        self._confirmationFuture: Optional[asyncio.Future] = None
        self._last_send_monotonic: float = 0.0

    @property
    def ready(self): return self._ready

    def _log(self, msg):  # enable as needed
        logging.info("[%s] %s", self._name, msg)
        return

    def _error(self, msg, exc: Optional[BaseException] = None):
        if exc:
            logging.error("[%s] %s: %s", self._name, msg, exc)
        else:
            logging.error("[%s] %s", self._name, msg)

    async def connect(self):
        try:
            #self._log("Connecting...")
            self._reader, self._writer = await asyncio.open_connection(
                self._config.host, self._config.port, ssl=self._config.ssl_context
            )
            await AgentMessageHelper.send_id_message(
                self._writer, self._name, self._peerid, self._config.token)

            while not self._app_state.stopped:
                msg = await AgentMessageHelper.read_message(self._reader)

                if '"subsystem":"auth"' in msg and '"status":"approved"' in msg:
                    if not self._ready:
                        self._ready = True
                        self._app_state.on_agent_approved()
                        asyncio.create_task(self._start_spam())
                elif '"m":"confirm"' in msg:
                    # record latency for the last batch
                    if self._last_send_monotonic > 0.0:
                        latency = datetime.datetime.now().timestamp() - self._last_send_monotonic
                        self._app_state.on_confirm_latency(latency)
                        self._app_state.on_confirm()
                    # record confirmation for the last batch
                    if self._confirmationFuture and not self._confirmationFuture.done():
                        self._confirmationFuture.set_result(None)

        except Exception as ex:
            if not self._app_state.stopped:
                # Log the error, update stats, and return to stop the loop
                self._app_state.on_error()
                self._error("Lost connection", ex)
                await self.disconnect()
                return

    async def disconnect(self):
        self._ready = False
        try:
            if self._confirmationFuture and not self._confirmationFuture.done():
                self._confirmationFuture.set_result(None)
            if self._writer:
                self._writer.close()
                await self._writer.wait_closed()
        except Exception as ex:
            if not self._app_state.stopped:
                self._error("Error closing writer", ex)
        self._writer = None
        self._reader = None

    async def start(self) -> None:
        await self.connect()

    async def _start_spam(self) -> None:
        # wait until all agents approved
        while not self._app_state.ready:
            await asyncio.sleep(1)

        # small delay to stagger
        await asyncio.sleep(1)
        #self._log(f"Start to send messages. EPS per agent={self._app_state.rate_limit_per_agent_eps}")

        events_per_batch = self._app_state.events_per_batch
        while self._ready:
            # honor "one in flight" rule
            if self._confirmationFuture:
                await self._confirmationFuture

            if self._app_state.stopped:
                return
            
            # honor change rate
            while self._app_state.is_changing_rate():
                await asyncio.sleep(0.1)

            start_send_time = datetime.datetime.now().timestamp()
            try:
                await self._send_next_events_batch(events_per_batch)
            except Exception as ex:
                if not self._app_state.stopped:
                    # Log the error, update stats, and return to stop the loop
                    self._app_state.on_error()
                    self._error("Error on send events", ex)
                    return 0.0
            end_send_time = datetime.datetime.now().timestamp()

            # check if rate limit per agent is being honored
            per_agent_eps = self._app_state.rate_limit_per_agent_eps
            seconds_per_batch = (events_per_batch / per_agent_eps) if per_agent_eps > 0 else 0.0
            if seconds_per_batch > 0:
                #if passed_seconds > seconds_per_batch:
                #    self._app_state.on_low_send_rate()
                # Not an error!? - self._app_state.on_error()
                sleep_time = max(0.0, seconds_per_batch - (end_send_time - start_send_time))
                await asyncio.sleep(sleep_time)

    async def _send_next_events_batch(self, events_per_batch: int) -> float:
        self._confirmationId += 1
        loop = asyncio.get_running_loop()
        self._confirmationFuture = loop.create_future()

        batch_msg = AgentMessageHelper.make_events_batch(
            events_per_batch, self._confirmationId
        )
        self._last_send_monotonic = datetime.datetime.now().timestamp()
        await AgentMessageHelper.send_message(self._writer, batch_msg)

        self._app_state.on_batch_sent()
        return self._last_send_monotonic
