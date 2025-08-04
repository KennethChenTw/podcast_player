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
            'window_x': None,
            'window_y': None,
            'window_width': 1000,
            'window_height': 750,
            'window_maximized': False,
            'paned_window_positions': {},  # For PanedWindow positions
            'column_widths': {},  # For Treeview column widths
            'volume': 0.7,
            'last_station_url': '',
            'last_playlist_index': 0,
            'theme': 'light',
            'episode_load_mode': 'all',  # 'all' or 'latest'
            'latest_episode_count': 10,
            'font_scale': 1.0  # Font scaling factor (0.6 to 2.0)
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
            # Get window geometry details
            geometry = root.geometry()
            is_maximized = root.state() == 'zoomed'
            
            # Parse geometry (e.g., "1000x750+100+50")
            window_width, window_height, window_x, window_y = None, None, None, None
            try:
                size_part, pos_part = geometry.split('+', 1)
                window_width, window_height = map(int, size_part.split('x'))
                if '+' in pos_part:
                    x_str, y_str = pos_part.split('+', 1)
                    window_x, window_y = int(x_str), int(y_str)
                else:
                    window_x = int(pos_part.split('-')[0]) if '-' in pos_part else int(pos_part)
                    window_y = int(pos_part.split('-')[1]) if '-' in pos_part else 0
            except (ValueError, IndexError):
                # Fallback to defaults if parsing fails
                pass
            
            # Update settings in memory
            self.settings.update({
                'geometry': geometry,
                'window_width': window_width or self.defaults['window_width'],
                'window_height': window_height or self.defaults['window_height'],
                'window_x': window_x,
                'window_y': window_y,
                'window_maximized': is_maximized,
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
    
    def save_paned_window_position(self, widget_name: str, position: int) -> None:
        """
        Save PanedWindow sash position.
        
        Args:
            widget_name: Unique identifier for the paned window  
            position: Sash position to save
        """
        if 'paned_window_positions' not in self.settings:
            self.settings['paned_window_positions'] = {}
        self.settings['paned_window_positions'][widget_name] = position
    
    def get_paned_window_position(self, widget_name: str, default: int = 300) -> int:
        """
        Get saved PanedWindow sash position.
        
        Args:
            widget_name: Unique identifier for the paned window
            default: Default position if not found
            
        Returns:
            Saved position or default
        """
        positions = self.get_setting('paned_window_positions', {})
        return positions.get(widget_name, default)
    
    def save_column_width(self, tree_name: str, column: str, width: int) -> None:
        """
        Save Treeview column width.
        
        Args:
            tree_name: Unique identifier for the treeview
            column: Column identifier
            width: Width to save
        """
        if 'column_widths' not in self.settings:
            self.settings['column_widths'] = {}
        if tree_name not in self.settings['column_widths']:
            self.settings['column_widths'][tree_name] = {}
        self.settings['column_widths'][tree_name][column] = width
    
    def get_column_width(self, tree_name: str, column: str, default: int = 100) -> int:
        """
        Get saved Treeview column width.
        
        Args:
            tree_name: Unique identifier for the treeview
            column: Column identifier
            default: Default width if not found
            
        Returns:
            Saved width or default
        """
        widths = self.get_setting('column_widths', {})
        tree_widths = widths.get(tree_name, {})
        return tree_widths.get(column, default)
    
    def get_window_state(self) -> Dict[str, Any]:
        """
        Get detailed window state information.
        
        Returns:
            Dictionary containing window state details
        """
        return {
            'width': self.get_setting('window_width', self.defaults['window_width']),
            'height': self.get_setting('window_height', self.defaults['window_height']),
            'x': self.get_setting('window_x', self.defaults['window_x']),
            'y': self.get_setting('window_y', self.defaults['window_y']),
            'maximized': self.get_setting('window_maximized', self.defaults['window_maximized']),
            'geometry': self.get_setting('geometry', self.defaults['geometry'])
        }
    
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
    
    def get_font_scale(self) -> float:
        """
        Get font scale setting.
        
        Returns:
            Font scale factor (0.6 to 2.0)
        """
        scale = self.get_setting('font_scale', self.defaults['font_scale'])
        return max(0.6, min(2.0, scale))  # 確保在有效範圍內
    
    def set_font_scale(self, scale: float) -> None:
        """
        Set font scale setting.
        
        Args:
            scale: Font scale factor (0.6 to 2.0)
        """
        # 確保縮放值在有效範圍內
        validated_scale = max(0.6, min(2.0, scale))
        self.set_setting('font_scale', validated_scale)
    
    def get_font_scale_percentage(self) -> int:
        """
        Get font scale as percentage.
        
        Returns:
            Scale percentage (60-200)
        """
        return int(self.get_font_scale() * 100)
    
    def save_basic_settings(self) -> bool:
        """
        Save basic settings without requiring window state parameters.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Load existing settings
            settings = {}
            if os.path.exists(self.settings_file):
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                except:
                    pass
            
            # Update with current in-memory settings
            settings.update(self.settings)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            # Save to file
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving basic settings: {e}")
            return False
