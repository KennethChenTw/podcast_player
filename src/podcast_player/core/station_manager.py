"""
Station Manager for Podcast Player

Handles management of favorite podcast stations including
loading, saving, importing, exporting, and CRUD operations.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from tkinter import filedialog, messagebox


class StationManager:
    """Manages podcast station favorites and persistence."""
    
    def __init__(self, stations_file: str):
        """
        Initialize station manager.
        
        Args:
            stations_file: Path to stations JSON file
        """
        self.stations_file = stations_file
        self.stations: Dict[str, str] = {}
        self.load_stations()
    
    def load_stations(self) -> bool:
        """
        Load stations from JSON file.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.stations_file):
                with open(self.stations_file, 'r', encoding='utf-8') as f:
                    self.stations = json.load(f)
                return True
            else:
                self.stations = {}
                return False
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading stations: {e}")
            self.stations = {}
            return False
    
    def save_stations(self) -> bool:
        """
        Save stations to JSON file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(self.stations_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(self.stations_file, 'w', encoding='utf-8') as f:
                json.dump(self.stations, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError) as e:
            print(f"Error saving stations: {e}")
            return False
    
    def add_station(self, name: str, url: str) -> bool:
        """
        Add a new station.
        
        Args:
            name: Station name
            url: RSS feed URL
            
        Returns:
            bool: True if added successfully, False if name already exists
        """
        if not name or not url:
            return False
        
        if name in self.stations:
            return False
        
        self.stations[name] = url
        return self.save_stations()
    
    def update_station(self, old_name: str, new_name: str, new_url: str) -> bool:
        """
        Update an existing station.
        
        Args:
            old_name: Current station name
            new_name: New station name
            new_url: New RSS feed URL
            
        Returns:
            bool: True if updated successfully, False otherwise
        """
        if not new_name or not new_url:
            return False
        
        if old_name not in self.stations:
            return False
        
        # If name changed, check for conflicts
        if old_name != new_name and new_name in self.stations:
            return False
        
        # Remove old entry if name changed
        if old_name != new_name:
            del self.stations[old_name]
        
        self.stations[new_name] = new_url
        return self.save_stations()
    
    def delete_station(self, name: str) -> bool:
        """
        Delete a station.
        
        Args:
            name: Station name to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
        """
        if name not in self.stations:
            return False
        
        del self.stations[name]
        return self.save_stations()
    
    def get_station_url(self, name: str) -> Optional[str]:
        """
        Get URL for a station.
        
        Args:
            name: Station name
            
        Returns:
            str or None: Station URL if found, None otherwise
        """
        return self.stations.get(name)
    
    def get_station_names(self) -> List[str]:
        """
        Get all station names sorted alphabetically.
        
        Returns:
            List[str]: Sorted list of station names
        """
        return sorted(self.stations.keys())
    
    def get_all_stations(self) -> Dict[str, str]:
        """
        Get copy of all stations.
        
        Returns:
            Dict[str, str]: Copy of stations dictionary
        """
        return self.stations.copy()
    
    def station_exists(self, name: str) -> bool:
        """
        Check if a station exists.
        
        Args:
            name: Station name to check
            
        Returns:
            bool: True if station exists, False otherwise
        """
        return name in self.stations
    
    def get_station_count(self) -> int:
        """
        Get number of stations.
        
        Returns:
            int: Number of stations
        """
        return len(self.stations)
    
    def clear_all_stations(self) -> bool:
        """
        Clear all stations.
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        self.stations.clear()
        return self.save_stations()
    
    def import_stations(self, parent_window=None) -> Tuple[bool, str]:
        """
        Import stations from JSON file.
        
        Args:
            parent_window: Tkinter parent window for dialog
            
        Returns:
            Tuple[bool, str]: (Success status, message)
        """
        try:
            file_path = filedialog.askopenfilename(
                parent=parent_window,
                title="Import Stations",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return False, "Import cancelled"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_stations = json.load(f)
            
            if not isinstance(imported_stations, dict):
                return False, "Invalid file format: expected JSON object"
            
            # Count new and existing stations
            new_count = 0
            updated_count = 0
            
            for name, url in imported_stations.items():
                if not isinstance(name, str) or not isinstance(url, str):
                    continue
                
                if name in self.stations:
                    updated_count += 1
                else:
                    new_count += 1
                
                self.stations[name] = url
            
            if new_count == 0 and updated_count == 0:
                return False, "No valid stations found in file"
            
            success = self.save_stations()
            if success:
                message = f"Imported {new_count} new stations"
                if updated_count > 0:
                    message += f", updated {updated_count} existing stations"
                return True, message
            else:
                return False, "Error saving imported stations"
                
        except json.JSONDecodeError:
            return False, "Invalid JSON file format"
        except OSError as e:
            return False, f"Error reading file: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def export_stations(self, parent_window=None) -> Tuple[bool, str]:
        """
        Export stations to JSON file.
        
        Args:
            parent_window: Tkinter parent window for dialog
            
        Returns:
            Tuple[bool, str]: (Success status, message)
        """
        try:
            if not self.stations:
                return False, "No stations to export"
            
            file_path = filedialog.asksaveasfilename(
                parent=parent_window,
                title="Export Stations",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return False, "Export cancelled"
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.stations, f, indent=2, ensure_ascii=False)
            
            return True, f"Exported {len(self.stations)} stations to {file_path}"
            
        except OSError as e:
            return False, f"Error writing file: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def search_stations(self, query: str) -> Dict[str, str]:
        """
        Search stations by name or URL.
        
        Args:
            query: Search query
            
        Returns:
            Dict[str, str]: Matching stations
        """
        if not query:
            return self.stations.copy()
        
        query_lower = query.lower()
        results = {}
        
        for name, url in self.stations.items():
            if query_lower in name.lower() or query_lower in url.lower():
                results[name] = url
        
        return results
    
    def get_stations_by_url(self, url: str) -> List[str]:
        """
        Get station names that use a specific URL.
        
        Args:
            url: RSS feed URL
            
        Returns:
            List[str]: Station names using this URL
        """
        return [name for name, station_url in self.stations.items() if station_url == url]
    
    def validate_station_data(self, stations_data: Dict) -> Tuple[bool, str]:
        """
        Validate station data format.
        
        Args:
            stations_data: Dictionary to validate
            
        Returns:
            Tuple[bool, str]: (Is valid, error message if invalid)
        """
        if not isinstance(stations_data, dict):
            return False, "Data must be a dictionary"
        
        for name, url in stations_data.items():
            if not isinstance(name, str) or not isinstance(url, str):
                return False, f"Invalid station entry: {name} -> {url}"
            
            if not name.strip():
                return False, "Station names cannot be empty"
            
            if not url.strip():
                return False, f"URL for station '{name}' cannot be empty"
        
        return True, "Valid"
    
    def backup_stations(self, backup_path: str) -> bool:
        """
        Create a backup of current stations.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            bool: True if backup created successfully, False otherwise
        """
        try:
            # Ensure directory exists
            directory = os.path.dirname(backup_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.stations, f, indent=2, ensure_ascii=False)
            return True
        except OSError as e:
            print(f"Error creating backup: {e}")
            return False