import argparse
from classes.FeedBackModifier import FeedBackModifier

# Run the program
if __name__ == "__main__":
    # Create a class instance
    my_instance = FeedBackModifier()

    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Parser handles command-line flags.")

    # Add optional flags and arguments
    parser.add_argument('--sheet', '-s', type=str, help="The name of the workbook sheet that the process belongs to.")
    parser.add_argument('--process', '-p', action="append", help='Add process to call.')

    # Parse the arguments
    args = parser.parse_args()
    user_passed_args = any(val for key, val in args._get_kwargs())
    if user_passed_args:
        selected_sheet = args.sheet
        selected_processes = args.process
        if selected_sheet and selected_processes:
            if selected_sheet in my_instance.processes:
                for method in selected_processes:
                    if method in my_instance.processes[selected_sheet]:
                        my_instance.processes[selected_sheet][method].logic()
                    else:
                        raise Exception(f"The process '{method}' does not exist for the sheet '{selected_sheet}'.")
            else:
                raise Exception(f"The sheet '{selected_sheet}' does not exist in the workbook.")
            
            # Save changes
            my_instance.save_changes()
        else:
            raise Exception("Not all required arguments were passed.")
    else:
        while True:
            action_string = "Select an action to perform:\n\t1 - Modify data\n\t2 - View Logs\n\t0 - Quit Program\n"
            selected_action = input(action_string)
            numeric_action = int(selected_action) if selected_action.isnumeric() else None
            match numeric_action:
                case 0:
                    break
                case 1:
                    process_sheets = list(my_instance.processes.keys())
                    modify_string = "Select a sheet to modify:\n"
                    for index, sheet in enumerate(process_sheets):
                        modify_string += f"\t{index} - '{sheet}'\n"
                    
                    selected_sheet = input(modify_string)
                    numeric_sheet = int(selected_sheet) if selected_sheet.isnumeric() else None
                    if numeric_sheet != None and (0 <= numeric_sheet < len(process_sheets)):
                        availabile_sheet_processes = list(my_instance.processes[process_sheets[numeric_sheet]].keys())
                        selected_processes = list()
                        while availabile_sheet_processes:
                            process_string = f"Select {"another" if len(selected_processes) else "a"} process you wish to run:\n\t0 - Finish selecting processes\n"
                            for index, key in enumerate(availabile_sheet_processes, start=1):
                                process_string += f"\t{index} - {key}\n"
                            selected_process = input(process_string)
                            numeric_process = int(selected_process) if selected_process.isnumeric() else None
                            if numeric_process != None and (0 <= numeric_process <= len(availabile_sheet_processes)):
                                if not numeric_process:
                                    break
                                else:
                                    selected_processes.append(availabile_sheet_processes[numeric_process - 1])
                                    availabile_sheet_processes.pop(numeric_process - 1)
                            else:
                                print("Invalid process selected.")
                        for process in selected_processes:
                            my_instance.processes[process_sheets[numeric_sheet]][process].logic()
                        my_instance.save_changes()
                    else:
                        print("Invalid sheet selected.")
                case 2:
                    print('view')
                case _:
                    print("Invalid action selected.")