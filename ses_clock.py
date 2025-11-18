import threading
from typing import List

class SESClock:
    def __init__(self, size: int = 15):
        self.size = size
        self.clock = [0] * size
        self.lock = threading.Lock()

    def tick(self, pid: int):
        with self.lock:
            self.clock[pid] += 1

    def merge(self, other: List[int]):
        with self.lock:
            self.clock = [max(self.clock[i], other[i]) for i in range(self.size)]

    def get(self) -> List[int]:
        with self.lock:
            return list(self.clock)

    def update_on_receive(self, pid: int, other: List[int]):
        with self.lock:
            self.clock = [max(self.clock[i], other[i]) for i in range(self.size)]
            self.clock[pid] += 1
