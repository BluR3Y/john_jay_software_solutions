import os

from packages.database_manager import DatabaseManager
from packages.migration_manager import MigrationManager

PROCESS_NAME = "Migration Manager"

def manage_migration(db_path: str):
    # with MigrationManager(os.getenv('EXCEL_FILE_PATH'), os.getenv('SAVE_PATH')) as migration_manager:
    #     pass
    
    with DatabaseManager(db_path, PROCESS_NAME) as db_manager:
        migration_manager = MigrationManager(db_manager, os.getenv('EXCEL_FILE_PATH'), os.getenv('SAVE_PATH'))
        migration_manager.__enter__()
        print(migration_manager.DISCIPLINES)