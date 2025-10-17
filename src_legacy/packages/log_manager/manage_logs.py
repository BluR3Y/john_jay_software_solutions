from typing import TYPE_CHECKING
from pprint import pprint
from ...modules.utils import (
    single_select_input,
    multi_select_input
)

if TYPE_CHECKING:
    from packages.log_manager import LogManager

def manage_logs(log_manager: "LogManager"):
    log_dates = list(log_manager.get_runtime_dates())
    if not log_dates:
        print(f"Resource does not contain any logs.")
        return
    
    selected_date = single_select_input("Input date of logs", log_dates)
    date_logs = log_manager.get_runtime_logs(selected_date)

    pprint(date_logs, indent=4)

def revert_changes(log_manager: "LogManager", create_fn: object, update_fn: object, delete_fn: object):
    pass