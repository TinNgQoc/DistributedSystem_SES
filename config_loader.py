import json
import os
from typing import List, Dict, Any

class ConfigManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.error = None
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_path):
            self.error = f"Config file not found: {self.config_path}"
            self.config = None
            return
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.error = f"Error reading config: {e}"
            self.config = None

    def validate(self) -> bool:
        if self.config is None:
            return False
        processes = self.config.get('processes')
        if not isinstance(processes, list) or len(processes) != 15:
            self.error = "Config must contain exactly 15 processes."
            return False
        ports = set()
        for idx, proc in enumerate(processes):
            if 'ip' not in proc or 'port' not in proc:
                self.error = f"Process {idx} missing ip or port."
                return False
            if proc['port'] in ports:
                self.error = f"Duplicate port found: {proc['port']}"
                return False
            ports.add(proc['port'])
        return True

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def get_error(self) -> str:
        return self.error
