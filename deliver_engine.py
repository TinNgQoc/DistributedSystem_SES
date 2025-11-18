import threading
from typing import Callable, Dict, Any
from ses_clock import SESClock

class DeliverEngine:
    def __init__(self, pid: int, process_message: Callable[[Dict[str, Any]], None]):
        self.clock = SESClock()
        self.pid = pid
        self.process_message = process_message
        self.log = []
        self.lock = threading.Lock()
        self.delivered = set()

    def deliver(self, msg: Dict[str, Any]):
        msg_id = (msg['sender_id'], msg['seq'])
        with self.lock:
            if msg_id in self.delivered:
                return  # Prevent duplicate deliver
            self.clock.merge(msg['timestamp'])
            self.clock.tick(self.pid)
            self.log.append(f"Delivered msg {msg['seq']} from {msg['sender_id']} at {self.clock.get()}")
            self.delivered.add(msg_id)
        self.process_message(msg)

    def get_log(self):
        with self.lock:
            return list(self.log)
