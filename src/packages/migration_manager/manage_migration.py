import os

from packages.database_manager import DatabaseManager
from packages.migration_manager import MigrationManager

def manage_migration(db_manager: DatabaseManager):
    with MigrationManager(os.getenv('EXCEL_FILE_PATH')) as migration_manager:
        pass