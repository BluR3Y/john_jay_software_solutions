import shutil
import platform
import logging
from pathlib import Path
from ..modules.utils import find_closest_match

from ..modules.logger import logger

class ContentManager:
    """
    Manages copying files from a source directory to a structured destination.
    Supports fuzzy path matching, safe path handling for Windows, and context-based setup.
    """

    def __init__(self, source_path: str, dest_path: str, force_delete: bool = False):
        if not source_path or not dest_path:
            raise ValueError("Empty paths were provided to ContentManager.")

        source_dir = Path(source_path)
        if not source_dir.exists():
            raise FileExistsError(f"Source path does not exist: {source_path}")
        if not source_dir.is_dir():
            raise ValueError("Source path is not a directory.")

        self.source_dir = source_dir
        self.dest_dir = Path(dest_path) / source_dir.name
        self.force_delete = force_delete

    def __enter__(self):
        if self.dest_dir.exists() and self.force_delete:
            logger.get_logger().info(f"Deleting existing destination directory: {self.dest_dir}")
            self._delete_directory(self.dest_dir)

        self.dest_dir.mkdir(parents=True, exist_ok=True)
        logger.get_logger().info(f"Created destination directory: {self.dest_dir}")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # No cleanup required
        pass

    def copy_file(self, file_path: str):
        if Path(file_path).is_absolute():
            raise ValueError("Expected a relative file path, but got an absolute path.")

        source_file_path = self._safe_path(self.source_dir / file_path)
        dest_file_path = self._safe_path(self.dest_dir / file_path)

        if not source_file_path.exists():
            raise FileExistsError(f"Missing source file: {source_file_path}")

        if dest_file_path.exists():
            logger.get_logger().info(f"Skipping existing file: {dest_file_path}")
            return

        dest_file_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file_path, dest_file_path)
        logger.get_logger().info(f"Copied file: {source_file_path} → {dest_file_path}")

    def copy_all_files(self):
        """
        Recursively copies all files from source_dir to dest_dir, maintaining directory structure.
        """
        for file in self.source_dir.rglob("*"):
            if file.is_file():
                rel_path = file.relative_to(self.source_dir)
                self.copy_file(str(rel_path))

    def find_closest_relative_file(self, file_path: str):
        """
        Finds the closest matching relative path within the ContentManager's source directory for the given file path.

        Args:
            file_path (str): The file path to find the closest match for, relative to the ContentManager's source directory.

        Returns:
            Path: Relative Path object or None if no close match is found.
        """
        base_dir_obj = self.source_dir
        file_path_obj = Path(file_path)
        relative_path = Path()

        for part in file_path_obj.parts:
            all_items = [f.name for f in base_dir_obj.iterdir()]
            closest_item = find_closest_match(part, all_items)[0]
            if not closest_item:
                return None
            relative_path /= closest_item
            base_dir_obj /= closest_item

        return relative_path

    def relative_source_file_exists(self, file_path: str) -> bool:
        """
        Checks whether the relative file path exists and is a file.

        Returns:
            bool: True if file exists and is a file, False otherwise.
        """
        file_path_obj = self._safe_path(self.source_dir / file_path)
        return file_path_obj.is_file()
    
    def relative_dest_file_exists(self, file_path: str) -> bool:
        file_path_obj = self._safe_path(self.dest_dir / file_path)
        return file_path_obj.is_file()

    @staticmethod
    def _delete_directory(dir_path: Path):
        """
        Deletes the specified directory and all its contents.

        Args:
            dir_path: The Path object to the directory to delete.

        Raises:
            Exception: If an error occurs during directory deletion.
        """
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                logger.get_logger().info(f"Deleted directory: {dir_path}")
            except OSError as err:
                raise Exception(f"An error occurred while deleting the directory: {err}")

    @staticmethod
    def _safe_path(path: Path) -> Path:
        """
        Converts a path to an extended-length path on Windows to avoid MAX_PATH issues.
        """
        if platform.system() == "Windows":
            p = str(path)
            if not p.startswith("\\\\?\\"):
                return Path(r"\\?\\" + p)
        return path
