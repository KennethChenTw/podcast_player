"""
File utility functions for the Podcast Player application.

This module provides common file operations and utilities.
"""

import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Union


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def ensure_directory_exists(directory_path: Union[str, Path]) -> Path:
        """
        Ensure that a directory exists, creating it if necessary.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Path object for the directory
        """
        path = Path(directory_path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
        """
        Safely load JSON data from a file.
        
        Args:
            file_path: Path to the JSON file
            default: Default value to return if file doesn't exist or is invalid
            
        Returns:
            Loaded JSON data or default value
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            return default
    
    @staticmethod
    def safe_json_save(file_path: Union[str, Path], data: Any, backup: bool = True) -> bool:
        """
        Safely save JSON data to a file.
        
        Args:
            file_path: Path to the JSON file
            data: Data to save
            backup: Whether to create a backup of existing file
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            
            # Create backup if requested and file exists
            if backup and file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                shutil.copy2(file_path, backup_path)
            
            # Ensure parent directory exists
            FileUtils.ensure_directory_exists(file_path.parent)
            
            # Write to temporary file first, then rename (atomic operation)
            with tempfile.NamedTemporaryFile(
                mode='w',
                encoding='utf-8',
                dir=file_path.parent,
                delete=False
            ) as temp_file:
                json.dump(data, temp_file, indent=2, ensure_ascii=False)
                temp_path = temp_file.name
            
            # Atomic rename
            os.rename(temp_path, file_path)
            return True
            
        except (IOError, OSError) as e:
            print(f"Error saving JSON file {file_path}: {e}")
            # Clean up temporary file if it exists
            try:
                if 'temp_path' in locals():
                    os.unlink(temp_path)
            except:
                pass
            return False
    
    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> Optional[int]:
        """
        Get the size of a file in bytes.
        
        Args:
            file_path: Path to the file
            
        Returns:
            File size in bytes, or None if file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except (FileNotFoundError, OSError):
            return None
    
    @staticmethod
    def is_file_readable(file_path: Union[str, Path]) -> bool:
        """
        Check if a file exists and is readable.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is readable, False otherwise
        """
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and os.access(path, os.R_OK)
        except OSError:
            return False
    
    @staticmethod
    def is_file_writable(file_path: Union[str, Path]) -> bool:
        """
        Check if a file location is writable.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if location is writable, False otherwise
        """
        try:
            path = Path(file_path)
            
            # If file exists, check if it's writable
            if path.exists():
                return os.access(path, os.W_OK)
            
            # If file doesn't exist, check if parent directory is writable
            parent = path.parent
            return parent.exists() and os.access(parent, os.W_OK)
            
        except OSError:
            return False
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """
        Clean a filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Cleaned filename
        """
        import re
        
        # Remove or replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        cleaned = re.sub(invalid_chars, '_', filename)
        
        # Remove leading/trailing whitespace and dots
        cleaned = cleaned.strip(' .')
        
        # Ensure filename is not empty
        if not cleaned:
            cleaned = "untitled"
        
        # Limit length
        if len(cleaned) > 255:
            cleaned = cleaned[:255]
        
        return cleaned
    
    @staticmethod
    def get_available_filename(file_path: Union[str, Path]) -> Path:
        """
        Get an available filename by appending numbers if necessary.
        
        Args:
            file_path: Desired file path
            
        Returns:
            Available file path
        """
        path = Path(file_path)
        
        if not path.exists():
            return path
        
        # Extract base name and extension
        base_name = path.stem
        extension = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{extension}"
            new_path = parent / new_name
            
            if not new_path.exists():
                return new_path
            
            counter += 1
            
            # Prevent infinite loop
            if counter > 9999:
                raise ValueError(f"Unable to find available filename for {file_path}")
    
    @staticmethod
    def copy_file_safe(source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Safely copy a file with error handling.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if copy was successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Ensure source exists and is readable
            if not FileUtils.is_file_readable(source_path):
                return False
            
            # Ensure destination directory exists
            FileUtils.ensure_directory_exists(dest_path.parent)
            
            # Copy file
            shutil.copy2(source_path, dest_path)
            return True
            
        except (IOError, OSError) as e:
            print(f"Error copying file {source} to {destination}: {e}")
            return False
    
    @staticmethod
    def create_temp_directory(prefix: str = "podcast_player_") -> Optional[str]:
        """
        Create a temporary directory.
        
        Args:
            prefix: Prefix for the temporary directory name
            
        Returns:
            Path to the temporary directory, or None if creation failed
        """
        try:
            return tempfile.mkdtemp(prefix=prefix)
        except OSError as e:
            print(f"Error creating temporary directory: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_directory(temp_dir: Union[str, Path]) -> bool:
        """
        Clean up a temporary directory.
        
        Args:
            temp_dir: Path to the temporary directory
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir)
            return True
        except OSError as e:
            print(f"Error cleaning up temporary directory {temp_dir}: {e}")
            return False