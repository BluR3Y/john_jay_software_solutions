import json
import datetime
import os

class LogManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.runtime_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.logs = self._load_existing_logs()

    def _load_existing_logs(self):
        """Load existing logs from file if they exist."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as json_file:
                    return json.load(json_file)
            except (IOError, json.JSONDecodeError) as e:
                print(f"Error loading logs: {e}")
        return {}
    
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
        """Save logs to the JSON file."""
        try:
            with open(self.file_path, 'w') as json_file:
                json.dump(self.logs, json_file, indent=4)
        except IOError as e:
            print(f"Error saving logs: {e}")