from pathlib import Path
import json
from typing import Union

class RecordManager:

    def __init__(self, file_path: str):
        if not file_path:
            raise ValueError("Failed to provide a file path to record storage.")
        
        path_obj = Path(file_path)
        if path_obj.suffix != ".json":
            raise TypeError("Record storage must be a json file.")
        
        self.path_obj = path_obj
    
    def __enter__(self):
        if not self.path_obj.exists():
            self.records = []
        else:
            with open(self.path_obj, 'r', encoding='utf-8') as record_file:
                self.records = json.load(record_file)

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            with open(self.path_obj, 'w+', encoding='utf-8') as record_file:
                json.dump(self.records, record_file, indent=4)
        except Exception as err:
            raise Exception(f"An error occured while attempting to save records to file: {err}")
        
    def add_record(self, record_data: dict):
        self.records.append(record_data)

    def remove_record(self, conditions: Union[int, dict]):
        if isinstance(conditions, int):
            self.records.pop(conditions)
        elif isinstance(conditions, dict):
            for record in self.records[:]:
                if self.follows_conditions(record, conditions):
                    self.records.remove(record)

    def find_record(self, record_data: dict) -> list[dict]:
        # return [record for record in self.records if self.follows_conditions(record, record_data)]
        collection = []
        for index, record in enumerate(self.records):
            if self.follows_conditions(record, record_data):
                record['index'] = index
                collection.append(record)
        return collection
    
    @staticmethod
    def follows_conditions(record: dict, conditions: dict):
        return all(record.get(key) == value for key, value in conditions.items())

    @staticmethod
    def _merge_dicts(base, updates):
        """Recursively merge nested dictionaries."""
        for key, value in updates.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                RecordManager._merge_dicts(base[key], value)
            else:
                base[key] = value