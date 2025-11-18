import threading
import time
from typing import List, Dict, Any

class ConsoleUI:
    def __init__(self):
        self.logs = []
        self.lock = threading.Lock()
        self.filter_type = None

    def add_log(self, log_type: str, msg: str, timestamp: str = None):
        with self.lock:
            entry = {'type': log_type, 'msg': msg, 'timestamp': timestamp or time.strftime('%Y-%m-%d %H:%M:%S')}
            self.logs.append(entry)
            if self.filter_type is None or self.filter_type == log_type:
                print(self.format_log(entry))

    def format_log(self, entry: Dict[str, Any]) -> str:
        return f"[{entry['timestamp']}] {entry['type'].upper()}: {entry['msg']}"

    def set_filter(self, log_type: str):
        with self.lock:
            self.filter_type = log_type

    def show_logs(self, limit: int = 100):
        with self.lock:
            logs = self.logs[-limit:]
            for entry in logs:
                if self.filter_type is None or self.filter_type == entry['type']:
                    print(self.format_log(entry))
