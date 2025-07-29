"""
Configuration Manager for Podcast Player

Handles loading, saving, and managing application settings including
window geometry, volume, RSS URLs, and playlist state.
"""

import json
import os
from typing import Dict, Any, Optional, Callable


class ConfigManager:
    """Manages application configuration and settings persistence."""
    
    def __init__(self, script_dir: Optional[str] = None):
        """
        Initialize ConfigManager.
        
        Args:
            script_dir: Directory containing config files. If None, uses current file's directory.
        """
        self.script_dir = script_dir or os.path.dirname(os.path.abspath(__file__))
        self.settings_file = os.path.join(self.script_dir, "config", "window_settings.json")
        self.stations_file = os.path.join(self.script_dir, "config", "my_stations.json")
        self.history_file = os.path.join(self.script_dir, "data", "podcast_history.json")
        
        # Default settings
        self.defaults = {
            'geometry': '1000x750',
            'volume': 0.7,
            'last_station_url': '',
            'last_playlist_index': 0,
            'theme': 'light',
            'episode_load_mode': 'all',  # 'all' or 'latest'
            'latest_episode_count': 10
        }
        
        # Current settings in memory
        self.settings: Dict[str, Any] = {}
    
    def get_file_paths(self) -> Dict[str, str]:
        """Get all configuration file paths."""
        return {
            'settings': self.settings_file,
            'stations': self.stations_file,
            'history': self.history_file
        }
    
    def load_window_settings(self) -> bool:
        """
        Load window settings from JSON file.
        
        Returns:
            bool: True if settings were loaded successfully, False otherwise.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                return True
            else:
                self.settings = self.defaults.copy()
                return False
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading settings: {e}")
            self.settings = self.defaults.copy()
            return False
    
    def save_window_settings(self, root, volume: float, rss_entry, 
                           playlist: list, current_index: int) -> bool:
        """
        Save current window settings to JSON file.
        
        Args:
            root: Tkinter root window
            volume: Current volume level (0.0-1.0)
            rss_entry: RSS URL entry widget
            playlist: Current playlist
            current_index: Current playlist index
            
        Returns:
            bool: True if settings were saved successfully, False otherwise.
        """
        try:
            # Update settings in memory
            self.settings.update({
                'geometry': root.geometry(),
                'volume': volume,
                'last_station_url': rss_entry.get() if rss_entry else '',
                'last_playlist_index': current_index if playlist else 0
            })
            
            # Ensure directory exists
            directory = os.path.dirname(self.settings_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError) as e:
            print(f"Error saving settings: {e}")
            return False
    
    def apply_restored_state(self, volume_var, rss_entry, fetch_callback: Callable,
                           playlist: list, index_callback: Callable, 
                           ui_callback: Callable) -> None:
        """
        Apply loaded settings to UI components.
        
        Args:
            volume_var: Tkinter variable for volume
            rss_entry: RSS URL entry widget
            fetch_callback: Function to call for fetching RSS feed
            playlist: Playlist to populate
            index_callback: Function to call for setting playlist index
            ui_callback: Function to call for UI updates
        """
        # Set volume
        if volume_var:
            volume_var.set(self.get_volume())
        
        # Set RSS URL and fetch if available
        last_url = self.get_last_station_url()
        if last_url and rss_entry:
            rss_entry.delete(0, 'end')
            rss_entry.insert(0, last_url)
            if fetch_callback:
                fetch_callback()
        
        # Set playlist index
        last_index = self.get_last_playlist_index()
        if playlist and last_index < len(playlist):
            if index_callback:
                index_callback(last_index)
        
        # Update UI
        if ui_callback:
            ui_callback()
    
    def get_geometry(self) -> str:
        """Get window geometry or default."""
        return self.get_setting('geometry', self.defaults['geometry'])
    
    def get_volume(self) -> float:
        """Get volume level or default."""
        return self.get_setting('volume', self.defaults['volume'])
    
    def get_last_station_url(self) -> str:
        """Get last used RSS URL or empty string."""
        return self.get_setting('last_station_url', self.defaults['last_station_url'])
    
    def get_last_playlist_index(self) -> int:
        """Get last playlist position or 0."""
        return self.get_setting('last_playlist_index', self.defaults['last_playlist_index'])
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value or default.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def update_setting(self, key: str, value: Any) -> None:
        """
        Update a setting in memory.
        
        Args:
            key: Setting key
            value: New value
        """
        self.settings[key] = value
    
    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a setting value and save to file.
        
        Args:
            key: Setting key
            value: New value
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Update in memory
            self.settings[key] = value
            
            # Ensure directory exists
            directory = os.path.dirname(self.settings_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError) as e:
            print(f"Error saving setting '{key}': {e}")
            return False
    
    def clear_settings(self) -> None:
        """Clear all settings from memory."""
        self.settings.clear()
    
    def delete_settings_file(self) -> bool:
        """
        Delete the settings file from disk.
        
        Returns:
            bool: True if file was deleted successfully, False otherwise.
        """
        try:
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
                return True
            return False
        except OSError as e:
            print(f"Error deleting settings file: {e}")
            return False
