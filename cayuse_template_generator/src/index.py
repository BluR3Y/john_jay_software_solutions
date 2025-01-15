from classes.MigrationManager import MigrationManager
import warnings
warnings.filterwarnings('ignore')

# Run the program
if __name__ == "__main__":
    # Create a class instance
    with MigrationManager() as my_instance:
        my_instance.start_migration()