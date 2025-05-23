import json
import datetime
import os

class LogManager:
    operations = ["create", "update", "delete"]

    """Class that manages the changes made to a resource and writes logs to a JSON file."""
    def __init__(self, file_path: str):
        """
        Initalizes an instance of the Logger.
        
        Args:
            file_path: The path of the json file that stores the logs.
        """
        if not file_path:
            raise ValueError("An empty file path was provided to the LogManager")
        
        self.file_path = file_path

    def __enter__(self):
        self.logs = self._load_logs(self.file_path) or []
        self.runtime_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if not self.get_runtime_logs(self.runtime_date_time):
            print(f"No logs to create. Exiting LogManager.")
            return
        
        formatted_data = [self._convert_to_json_serializable(log) for log in self.logs]
        
        try:
            with open(self.file_path, 'w', encoding='utf-8') as log_file:
                json.dump(formatted_data, log_file, indent=4)
        except IOError as err:
            raise Exception(f"An error occured while attempting to save logs to file: {err}")
        
    def __iter__(self):
        yield self.logs
    
    def find_logs(self, conditions: dict):
        """
        Returns indices of logs matching all key-value pairs in `conditions`.
        """
        indices = []
        for index, log in enumerate(self.logs):
            if all(log.get(k) == v for k,v in conditions.items()):
                indices.append(index)
        return indices

    def get_runtime_dates(self):
        """
        Returns all distinct timestamps in the log list.
        """
        return list({log['timestamp'] for log in self.logs})
    
    def get_runtime_logs(self, timestamp: str):
        """
        Returns logs created during this runtime session.
        """
        return [self.logs[log_index] for log_index in self.find_logs({"timestamp":timestamp})]
    
    def append_runtime_log(self, process: str, operation: str, table: str, record_id: any, properties: dict):
        """
        Appends a new log or updates an existing one if a match is found.

        Args:
            process: Name of the process being logged (Acts as a transaction in typical SQL fasion)
            operation: Type of operation ("create", "update", "delete").
            table: Affected database table.
            record_id: ID of the affected record.
            properties: Dict of additional details.
        """
        if operation not in self.operations:
            raise ValueError("Invalid operation selected")

        record_props = {
            "timestamp": self.runtime_date_time,
            "process": process,
            "operation": operation,
            "table": table,
            "record_id": record_id
        }

        existing_indices = self.find_logs(record_props)
        if existing_indices:
            self._merge_dicts(self.logs[existing_indices[0]], {"properties": properties})
        else:
            self.logs.append({**record_props, "properties": properties})
        
    @staticmethod
    def _load_logs(file_path):
        """Load existing logs from json file."""
        if not os.path.exists(file_path):
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as json_file:
                return json.load(json_file)
        except (IOError, json.JSONDecodeError) as err:
            raise Exception(f"An error occured while attempting to retrieve logs from file: {err}")

    @staticmethod
    def _merge_dicts(base, updates):
        """Recursively merge nested dictionaries."""
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                LogManager._merge_dicts(base[key], value)
            else:
                base[key] = value
    
    @staticmethod
    def _convert_to_json_serializable(obj):
        """Convert Python data types into JSON-serializable types."""
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj  # Already JSON serializable
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, (list, tuple, set)):
            return [LogManager._convert_to_json_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {str(key): LogManager._convert_to_json_serializable(value) for key, value in obj.items()}
        elif hasattr(obj, '__dict__'):
            return LogManager._convert_to_json_serializable(obj.__dict__)
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        else:
            return str(obj)  # Fallback: convert to string