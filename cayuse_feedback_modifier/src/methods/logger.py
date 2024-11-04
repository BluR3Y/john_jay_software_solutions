import json
import os
import datetime

# Method will create/update the file that will contain the logs
def save_logs(self):
    # Write the data to the JSON file
    with open(self.logs_path, 'w') as json_file:
        json.dump(self.logs, json_file, indent=4) # indent=4 for pretty printing

# Method will add logs to the logger
def append_logs(self, sheet, logs):
    # Retrieve the current datetime and format it
    current_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Get all logs for the current moment
    moment_logs = self.logs.get(current_date_time, {})
    # If no prior logs have been created for the provided sheet, initialize the property in the logger
    if sheet not in moment_logs:
        moment_logs[sheet] = logs
    else:
        moment_logs[sheet].update(logs)
    # Assign the new logs to the current datetime
    self.logs[current_date_time] = moment_logs


# Future Features:
    # Roleback changes