from classes.LogManager.LogManager import LogManager

# Use inheritance to create a child class for Database logs
class DatabaseLogManager(LogManager):
    def __init__(self, log_file_path):
        # Call the parent class constructor
        super().__init__(log_file_path)

    def append_log(self, process, table, row_identifier, rows, updates):
        logs = dict()
        for row in rows:
            row_log = dict()
            for col in row.keys():
                if col != row_identifier:
                    row_log[col] = f"{row[col]}:{updates[col]}"
            logs[row[row_identifier]] = row_log
        new_logs = {table: logs}

        # Use the parent class method to append the process logs
        super().append_runtime_log(process, new_logs)
        # Use the parent class method to save the logs
        super().save_logs()