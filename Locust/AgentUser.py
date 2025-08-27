import socket
import ssl
import secrets
import time
from locust import User, run_single_user, task, constant

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent_common import AgentMessageHelper

"""
locust -f AgentUser.py --users 1 --spawn-rate 1 --run-time 1m --headless
"""
class AgentUser(User):
    abstract = True
    """
    When True then locust does not create it.
    """
    wait_time = constant(1)
    """
    Pause between batches.
    """
    batch_size: int = 10  # количество событий в батче
    """
    Size of events batch to be sent.
    """
    token: str = 'SEZVCZKTMIZBQ2PKRV5BAWWFYAKFS4CC26REFJEG3HRAHB6CYROQ'
    """
    Token for Agent authentication.
    """
    _confirmation_id: int = 0

    def on_start(self):
        """Подключение при старте виртуального пользователя через SSL/TLS"""
        raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        self.sock = context.wrap_socket(raw_sock, server_hostname=None)
        self.sock.connect(("192.168.128.28", 8444))
        self._authenticate(self.token)
        
    def on_stop(self):
        """Закрыть соединение"""
        self.sock.close()

    @task
    def send_batch(self):
        self._confirmation_id += 1
        events = AgentMessageHelper.make_events_batch(
            self.batch_size, self._confirmation_id)

        start_time = time.time()
        response_length = 0
        exception = None
        try:
            AgentMessageHelper.send_sock_message(self.sock, events)
            ack = self._read_batch_ack_msg()
            if not ack:
                raise Exception("No batch ACK from server")
            response_length = len(ack)
        except Exception as e:
            exception = e

        if self.environment:
            response_time = int((time.time() - start_time) * 1000)
            self.environment.events.request.fire(
                request_type="tcp",
                name="send_batch",
                response_time=response_time,
                response_length=response_length,
                exception=exception,
            )

    def _authenticate(self, token: str):
        suffix = secrets.token_hex(8).upper()
        name = f"FakeAgent_{suffix}"
        peerid = f"EA2ULYEX7D6TG4MA{suffix}"

        auth_msg = AgentMessageHelper.make_id_msg(name, peerid, token)
        AgentMessageHelper.send_sock_message(self.sock, auth_msg)
        ack = self._read_auth_ack_msg()
        if not ack:
            raise Exception("No auth ACK from server")

    def _read_auth_ack_msg(self, max_try: int = 3):
        msg = AgentMessageHelper.read_sock_message(self.sock)
        while not '"subsystem":"auth"' in msg and not '"status":"approved"' in msg:
            max_try -= 1
            if max_try <= 0:
                return None
            msg = AgentMessageHelper.read_sock_message(self.sock)
        return msg

    def _read_batch_ack_msg(self, max_try: int = 3):
        msg = AgentMessageHelper.read_sock_message(self.sock)
        while not '"m":"confirm"' in msg:
            max_try -= 1
            if max_try <= 0:
                return None
            msg = AgentMessageHelper.read_sock_message(self.sock)
        return msg
    
if __name__ == "__main__":
    # For step-by-step debugging
    run_single_user(AgentUser)
