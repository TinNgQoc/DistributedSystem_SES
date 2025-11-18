import threading
import time
import os

class LoggerSES:
    def __init__(self, process_id: int, log_dir: str = "demo_logs"):
        self.process_id = process_id
        self.log_dir = log_dir
        self.file_path = os.path.join(log_dir, f"log_{process_id}.txt")
        os.makedirs(log_dir, exist_ok=True)
        self.lock = threading.Lock()
        self.buffer = []
        self.flush_interval = 100  # flush every 100 logs
        self._open_file()

    def _open_file(self):
        self.file = open(self.file_path, 'a', encoding='utf-8')

    def log(self, event_type: str, msg: str, timestamp: str):
        entry = f"[{timestamp}] {event_type.upper()}: {msg}\n"
        with self.lock:
            self.buffer.append(entry)
            if len(self.buffer) >= self.flush_interval:
                self._flush()

    def _flush(self):
        with self.lock:
            self.file.writelines(self.buffer)
            self.file.flush()
            self.buffer.clear()

    def close(self):
        with self.lock:
            if self.buffer:
                self._flush()
            self.file.close()

    def __del__(self):
        self.close()
