import json
import datetime
import os

class LogManager:
    def __init__(self, file_path: str):
        if not file_path:
            raise ValueError("A file path was not provided to the LogManager.")
        
        self.file_path = file_path
        self.runtime_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logs = self.load_existing_logs()
        
    def load_existing_logs(self) -> dict:
        """Load existing logs from logs file."""
        if not os.path.exists(self.file_path):
            return {}
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as json_file:
                return json.load(json_file)
        except (IOError, json.JSONDecodeError) as err:
            raise Exception(f"An error occured while attempting to retrieve logs from file: {err}")
        
    def append_runtime_log(self, process, log):
        """Add or update logs for the current runtime."""
        runtime_logs = self.logs.setdefault(self.runtime_date_time, {})
        if process in runtime_logs:
            self._merge_dicts(runtime_logs[process], log)
        else:
            runtime_logs[process] = log
            
    @staticmethod
    def _merge_dicts(base, updates):
        """Recursively merge nested dictionaries."""
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                LogManager._merge_dicts(base[key], value)
            else:
                base[key] = value
                
    def save_logs(self):
        """Save logs to the Json file."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as json_file:
                json.dump(self.logs, json_file, indent=4)
        except IOError as err:
            raise Exception(f"An error occured while attempting to save logs to file: {err}")