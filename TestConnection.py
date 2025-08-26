import asyncio
import secrets
import logging
import datetime
from typing import Optional
from agent_common import AgentConfig, AgentMessageHelper

# -----------------------------
# Agent socket
# -----------------------------
class AgentSocket:
    def __init__(self, config: AgentConfig) -> None:
        self._config = config

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
            self._log("Connecting...")
            self._reader, self._writer = await asyncio.open_connection(
                self._config.host, self._config.port, ssl=self._config.ssl_context
            )
            await AgentMessageHelper.send_id_message(
                self._writer, self._name, self._peerid, self._config.token)

            while self._writer and not self._writer.is_closing():
                msg = await AgentMessageHelper.read_message(self._reader)
                self._log(f"Received message: {msg}")

                if '"subsystem":"auth"' in msg and '"status":"approved"' in msg:
                    self._log("Agent approved, starting traffic...")
                    self._ready = True
                elif '"m":"confirm"' in msg:
                    # record latency for the last batch
                    if self._last_send_monotonic > 0.0:
                        latency = datetime.datetime.now().timestamp() - self._last_send_monotonic
                        self._log("Confirmation received, latency:" + str(latency) + "seconds")
                    # record confirmation for the last batch
                    if self._confirmationFuture and not self._confirmationFuture.done():
                        self._confirmationFuture.set_result(None)

        except Exception as ex:
            self._error("Lost connection", ex)
            await self.disconnect()

    async def send_message(self) -> None:
         # honor "one in flight" rule
        if self._confirmationFuture:
            await self._confirmationFuture

        self._log("Send Message...")
        self._last_send_monotonic = datetime.datetime.now().timestamp()

        self._confirmationId += 1
        loop = asyncio.get_running_loop()
        self._confirmationFuture = loop.create_future()
        
        batch_msg = AgentMessageHelper.make_events_batch(10, self._confirmationId)
        await AgentMessageHelper.send_message(self._writer, batch_msg)

    async def disconnect(self):
        self._reader = False
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
        self._writer = None
        self._reader = None

# -----------------------------
# Entrypoint
# -----------------------------
async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    HOST = "127.0.0.1"
    PORT = 8444
    TOKEN = "SUAYNE4444LBE2SOTESC2DO5UVDTFWVWJKQ3T2OXQE2MGZ53Y3XQ"
    config = AgentConfig(HOST, PORT, TOKEN)
        
    sock = AgentSocket(config)
    asyncio.create_task(sock.connect())
    await asyncio.sleep(5)

    if (not sock.ready):
        await sock.disconnect()
        logging.error("Agent is not ready, cannot send messages.")
        return

    await sock.send_message()
    await asyncio.sleep(5)

    await sock.send_message()
    await asyncio.sleep(5)

    await sock.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass