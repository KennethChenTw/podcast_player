"""
Main Application for Podcast Player

Coordinates all components and provides the main application entry point.
"""

import tkinter as tk
import os
import sys
from typing import Optional, Any

from podcast_player.core import (
    AudioPlayer, RSSProcessor, StationManager, 
    PlaylistManager, ConfigManager, ProgressTracker
)
from podcast_player.ui import MainWindow


class PodcastPlayerApp:
    """Main application class for the Podcast Player."""
    
    def __init__(self, script_dir: Optional[str] = None):
        """
        Initialize the podcast player application.
        
        Args:
            script_dir: Directory containing configuration files
        """
        # Set up file paths
        if script_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up to the project root for config files
            script_dir = os.path.join(script_dir, '..', '..')
        
        self.script_dir = os.path.abspath(script_dir)
        
        # Initialize Tkinter
        self.root = tk.Tk()
        self.root.title("Podcast 播放器")
        
        # Initialize core components
        self.config_manager = ConfigManager(self.script_dir)
        self.audio_player = AudioPlayer()
        self.rss_processor = RSSProcessor(self.config_manager)
        self.station_manager = StationManager(
            os.path.join(self.script_dir, "config", "my_stations.json")
        )
        self.playlist_manager = PlaylistManager(
            history_file=os.path.join(self.script_dir, "data", "podcast_history.json"),
            playlist_file=os.path.join(self.script_dir, "data", "current_playlist.json")
        )
        self.progress_tracker = ProgressTracker()
        
        # Prepare app components for UI
        app_components = {
            'audio_player': self.audio_player,
            'rss_processor': self.rss_processor,
            'station_manager': self.station_manager,
            'playlist_manager': self.playlist_manager,
            'config_manager': self.config_manager,
            'progress_tracker': self.progress_tracker,
            'on_closing': self.on_closing
        }
        
        # Initialize main window (includes UI and event handlers)
        self.main_window = MainWindow(self.root, app_components)
        self.ui = self.main_window.get_ui_component()
        self.event_handlers = self.main_window.get_event_handlers()
        
        # Set up application
        self.setup_application()
    
    def setup_application(self) -> None:
        """Set up the application after initialization."""
        try:
            # Load configuration
            self.config_manager.load_window_settings()
            
            # Apply window geometry
            geometry = self.config_manager.get_geometry()
            self.root.geometry(geometry)
            
            # Load stations and update UI
            print("Loading stations...")
            self.station_manager.load_stations()
            station_names = self.station_manager.get_station_names()
            print(f"Loaded {len(station_names)} stations: {station_names}")
            self.ui.update_station_combobox(station_names)
            print("Station combobox updated")
            
            # Set up window close handler
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            
            # Apply restored state
            self.apply_restored_state()
            
            # Set initial status
            self.ui.update_status("就緒")
            
        except Exception as e:
            print(f"Error setting up application: {e}")
            self.ui.update_status("初始化錯誤")
    
    def apply_restored_state(self) -> None:
        """Apply restored configuration state."""
        try:
            # Get UI components
            volume_var = self.ui.get_widget('volume_var')
            rss_entry = self.ui.get_widget('rss_entry') # This is a tk.Entry widget
            
            # Set volume
            if volume_var:
                volume = self.config_manager.get_volume()
                volume_var.set(volume)
                self.audio_player.set_volume(volume)
            
            # Set last RSS URL
            last_url = self.config_manager.get_last_station_url()
            if last_url and rss_entry:
                # Ensure rss_entry is a valid Entry widget before calling its methods
                if isinstance(rss_entry, tk.Entry):
                    rss_entry.delete(0, tk.END)
                    rss_entry.insert(0, last_url)
                
            # Populate playlist from loaded data
            self.ui.populate_playlist(
                self.playlist_manager.get_playlist_copy(),
                self.playlist_manager.current_index
            )
            
            # Auto-fetch if URL is available, but delay it to ensure UI is ready
            if last_url.strip():
                # Schedule fetch after a short delay to allow UI to fully render
                self.root.after(500, self.event_handlers.handle_fetch_podcast)
            
        except Exception as e:
            print(f"Error applying restored state: {e}")
    
    def save_current_state(self) -> None:
        """Save current application state."""
        try:
            # Get current values
            volume_var = self.ui.get_widget('volume_var')
            rss_entry = self.ui.get_widget('rss_entry') # This is a tk.Entry widget
            
            volume = volume_var.get() if volume_var else 0.7
            
            # Save window settings
            self.config_manager.save_window_settings(
                self.root,
                volume,
                rss_entry, # Pass the widget directly
                self.playlist_manager.get_playlist_copy(),
                self.playlist_manager.current_index
            )
            
            # Save playlist history and current playlist
            self.playlist_manager.save_history()
            self.playlist_manager.save_playlist()
            
        except Exception as e:
            print(f"Error saving current state: {e}")
    
    def on_closing(self) -> None:
        """Handle application closing."""
        try:
            # Save current state
            self.save_current_state()
            
            # Stop audio playback
            self.audio_player.stop()
            
            # Stop RSS processing
            self.rss_processor.cancel_current_operation()
            
            # Stop progress tracking
            self.progress_tracker.stop_tracking()
            
            # Before destroying the window, ensure theme manager doesn't try to access it
            if self.main_window and self.main_window.theme_manager:
                self.main_window.theme_manager.root = None # Break the reference

            # Destroy window - ensure all background tasks are stopped before this
            self.root.destroy()
            
            # Give a small delay to allow threads to terminate gracefully
            import time
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error during application shutdown: {e}")
            self.root.destroy()
    
    def run(self) -> None:
        """Run the application main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\\nApplication interrupted by user")
            self.on_closing()
        except Exception as e:
            print(f"Error in main loop: {e}")
            self.on_closing()
    
    def get_component(self, component_name: str):
        """
        Get a component by name for external access.
        
        Args:
            component_name: Name of component to get
            
        Returns:
            Component instance or None if not found
        """
        components = {
            'audio_player': self.audio_player,
            'rss_processor': self.rss_processor,
            'station_manager': self.station_manager,
            'playlist_manager': self.playlist_manager,
            'config_manager': self.config_manager,
            'progress_tracker': self.progress_tracker,
            'ui': self.ui,
            'event_handlers': self.event_handlers,
            'root': self.root
        }
        
        return components.get(component_name)


def main():
    """Main entry point for the application."""
    try:
        # Create and run application
        app = PodcastPlayerApp()
        app.run()
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
