import threading
from typing import List, Dict, Any

class BufferManager:
    def __init__(self):
        self.buffer = []
        self.lock = threading.Lock()
        self.log = []

    def buffer_message(self, msg: Dict[str, Any], waiting_for: Any):
        with self.lock:
            self.buffer.append(msg)
            self.log.append(f"msg {msg['seq']} buffered vì chờ msg {waiting_for}")

    def deliver_message(self, msg: Dict[str, Any]):
        with self.lock:
            self.log.append(f"msg {msg['seq']} delivered")
            # Unbuffer messages that can now be delivered
            delivered = [msg]
            unbuffered = []
            for buffered in self.buffer[:]:
                if self.can_deliver(buffered):
                    self.buffer.remove(buffered)
                    self.log.append(f"msg {msg['seq']} delivered → msg {buffered['seq']} được unbuffer và deliver")
                    delivered.append(buffered)
                    unbuffered.append(buffered)
            return delivered, unbuffered

    def can_deliver(self, msg: Dict[str, Any]) -> bool:
        # Placeholder: implement SES condition check
        return msg.get('ready', False)

    def get_log(self):
        with self.lock:
            return list(self.log)

    def get_buffer(self):
        with self.lock:
            return list(self.buffer)
