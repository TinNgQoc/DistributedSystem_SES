import threading
import time
import random
from datetime import datetime
from typing import List, Dict, Any

class Message:
    def __init__(self, sender_id: int, receiver_id: int, seq: int, payload: str):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.seq = seq
        self.timestamp = datetime.now().isoformat()
        self.payload = payload
    def to_dict(self):
        return {
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "seq": self.seq,
            "timestamp": self.timestamp,
            "payload": self.payload
        }

class ProcessNode:
    def __init__(self, node_id: int, all_ids: List[int], messages_per_thread: int = 150):
        self.node_id = node_id
        self.other_ids = [i for i in all_ids if i != node_id]
        self.messages_per_thread = messages_per_thread
        self.threads = []
        self.log = []
        self.log_lock = threading.Lock()

    def send_messages(self, receiver_id: int):
        for seq in range(1, self.messages_per_thread + 1):
            msg = Message(self.node_id, receiver_id, seq, payload=f"Hello {receiver_id} #{seq}")
            with self.log_lock:
                self.log.append(msg.to_dict())
            # Simulate random send rate (10-100 msg/min)
            sleep_time = 60.0 / random.randint(10, 100)
            time.sleep(sleep_time)
            print(f"[Node {self.node_id}] Sent to {receiver_id}: seq={seq}")

    def start(self):
        for rid in self.other_ids:
            t = threading.Thread(target=self.send_messages, args=(rid,))
            t.start()
            self.threads.append(t)

    def wait_all(self):
        for t in self.threads:
            t.join()

    def get_log(self):
        return self.log

if __name__ == "__main__":
    # Demo: run node 0 in a 15-node system
    all_ids = list(range(15))
    node = ProcessNode(0, all_ids)
    node.start()
    node.wait_all()
    print(f"Total messages sent: {len(node.get_log())}")
