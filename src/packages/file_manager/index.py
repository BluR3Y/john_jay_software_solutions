import shutil
import platform
from pathlib import Path
from modules.utils import find_closest_match

class FileManager:
    """
    Manages the copying of a directory structure from a source to a destination

    The FileManager ensures that the destination directory is clean before copying and handles file paths relative to the source directory. It uses a context manager to handle setup and cleanup.
    """
    def __init__(self, save_path: str, source_dir: str):
        """
        Initializes the FileManager.

        Args:
            save_path: The root path where the source directory will be copied to.
            source_dir: The path to the directory to be copied.
            
        Raises:
            ValueError: if either save_path or source_dir is empty or not a directory.
            FileExistsError: If the source directory does not exist.
        """
        if not save_path or not source_dir:
            raise ValueError("Empty paths were provided to FileManager")
        
        self.source_dir = Path(source_dir)
        if not self.source_dir.exists():
            raise FileExistsError(f"Source path does not exist: {self.source_dir}")
        if not self.source_dir.is_dir():
            raise ValueError(f"Source path is not a directory")
        
        self.save_dir = Path(save_path) / self.source_dir.name
        self.paths = set()
        
    def __enter__(self):
        """
        Enters the context manager. Creates the save directory.

        Raises:
            OSError: If an error occurs while creating the save directory.
        
        Returns:
            FileManager: Returns the instance of the FileManager.
        """
        if self.save_dir.exists():
            print(self.save_dir)
            self._delete_directory(self.save_dir)

        # Ensure save path exists
        self.save_dir.mkdir(
            parents=True,  # Ensures parent directories are created automatically.
            exist_ok=False   #Throw error if the directory already exists
        )
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the context manager. Copies files from the source directory to the save directory.

        Args:
            exc_type: The type of exception that occured, if any.
            exc_value: The exception instance, if any.
            traceback: A traceback object, if any.
        Raises:
            Exception: If an error occurs during file copying.
        """
        if exc_type is not None:
            print(f"An error occured: {exc_type}")
        
        errors = []
        for file_path in self.paths:
            source_path = self._safe_path(self.source_dir / file_path)
            destination_path = self._safe_path(self.save_dir / file_path)

            if not source_path.exists():
                errors.append(f"Missing source file: {source_path}")
                continue

            try:
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination_path)
            except Exception as err:
                errors.append(f"Failed copying {source_path}: {str(err)}")

        if errors:
            raise Exception(f"Errors during file copying:\n" + "\n".join(errors))
        
    def add_file(self, file_path: str):
        """
        Adds a file to be copied. The file path should be relative to the source directory provided in the constructor.

        Args:
            file_path: The path to the file, relative to the source directory.
        
        Raises:
            FileExistsError: If the file does not exist.
            ValueError: If the path does not point to a file.
        """
        if file_path in self.paths:
            raise ValueError(f"File with path '{file_path}' already assigned to be copied")
        
        file_path_obj = self._safe_path(self.source_dir / file_path) # Combine with source dir
        if not file_path_obj.exists():
            raise FileExistsError(f"File does not exist at path: {file_path}")
        if not file_path_obj.is_file():
            raise IsADirectoryError(f"The path '{file_path}' does not point to a file")
        self.paths.add(file_path)

    def find_closest_file(self, file_path: str):
        """
        Finds the closest matching relative path within the FileManager's source directory for the given file path.

        Args:
            file_path (str): The file path to find the closest match for, relative to the FileManager's source directory.

        Returns:
            Path: Relative Path object or None if no close match is found or the source directory doesn't exist.
        """
        base_dir_obj = self.source_dir
        file_path_obj = Path(file_path)
        relative_path = Path()  # Stores the closest matching relative path

        for part in file_path_obj.parts:

            # Get list of directories and files in the current base directory
            all_items = [f.name for f in base_dir_obj.iterdir()]
            
            closest_item = find_closest_match(part, all_items)
            if not closest_item:
                return None  # No close match found

            relative_path /= closest_item   # Build the relative closest path
            base_dir_obj /= closest_item  # Move deeper into the structure

        # return base_dir_obj if base_dir_obj.exists() else None  # Return closest match
        return relative_path  # Return only the relative closest path
    
    @staticmethod
    def _delete_directory(dir_path: str):
        """
        Deletes the specified directory and all its contents.
        
        Args:
            dir_path: The path to the directory to delete.

        Raises:
            OSError: If an error occurs during directory deletion.
        """
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            try:
                shutil.rmtree(path)
            except OSError as err:
                raise Exception(f"An error occured while deleting the directory: {dir_path}")
            
    @staticmethod
    def _safe_path(path: Path) -> Path:
        """
        Converts a path to an extended-length path on Windows to avoid MAX_PATH issues.
        """
        if platform.system() == "Windows":
            # Avoid double \\?\\ prefix
            p = str(path)
            if not p.startswith("\\\\?\\"):
                return Path(r"\\?\\" + p)
        return path