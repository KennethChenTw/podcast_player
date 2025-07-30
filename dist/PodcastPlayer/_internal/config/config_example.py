#!/usr/bin/env python3
"""
Example usage of ConfigManager class.

This demonstrates how to use the ConfigManager independently of the main PodcastPlayer class.
"""

from config_manager import ConfigManager


def example_usage():
    """Demonstrate ConfigManager usage."""
    
    # Initialize ConfigManager
    config = ConfigManager()
    
    print("=== ConfigManager Example ===")
    
    # Show file paths
    paths = config.get_file_paths()
    print(f"Configuration files will be stored in:")
    for key, path in paths.items():
        print(f"  {key}: {path}")
    
    # Load existing settings (if any)
    settings = config.load_window_settings()
    print(f"\nLoaded settings: {settings}")
    
    # Show individual setting getters
    print(f"Window geometry: {config.get_geometry()}")
    print(f"Volume: {config.get_volume()}")
    print(f"Last station URL: {config.get_last_station_url()}")
    print(f"Last playlist index: {config.get_last_playlist_index()}")
    
    # Update some settings in memory
    config.update_setting('test_setting', 'test_value')
    config.update_setting('geometry', '800x600')
    
    print(f"\nAfter updating settings:")
    print(f"Test setting: {config.get_setting('test_setting')}")
    print(f"Window geometry: {config.get_geometry()}")
    
    # Example of how it would be used with real tkinter widgets
    # (This is just a demonstration - not functional without real widgets)
    print(f"\n=== Mock GUI Integration ===")
    
    class MockWidget:
        def __init__(self, initial_value=""):
            self.value = initial_value
        
        def get(self):
            return self.value
        
        def delete(self, start, end):
            self.value = ""
        
        def insert(self, pos, text):
            self.value = text
        
        def set(self, value):
            self.value = value
    
    class MockRoot:
        def geometry(self):
            return "1000x750"
    
    # Mock widgets
    mock_root = MockRoot()
    mock_volume_var = MockWidget(70)
    mock_rss_entry = MockWidget("http://example.com/feed.xml")
    
    # Save example settings
    success = config.save_window_settings(
        mock_root, 
        0.8,  # volume 
        mock_rss_entry,
        [{'title': 'Episode 1', 'url': 'http://example.com/ep1.mp3'}],  # playlist
        0  # current_index
    )
    
    print(f"Settings saved successfully: {success}")
    
    # Apply settings example
    def mock_fetch_callback():
        print("Mock fetch callback called")
    
    def mock_index_callback(index):
        print(f"Mock index callback called with index: {index}")
    
    def mock_ui_callback(track, index):
        print(f"Mock UI callback called with track: {track['title']}, index: {index}")
    
    config.apply_restored_state(
        mock_volume_var,
        mock_rss_entry,
        mock_fetch_callback,
        [{'title': 'Episode 1', 'url': 'http://example.com/ep1.mp3', 'duration': 120}],
        mock_index_callback,
        mock_ui_callback
    )
    
    print(f"Volume after restoration: {mock_volume_var.get()}")
    print(f"RSS entry after restoration: {mock_rss_entry.get()}")


if __name__ == "__main__":
    example_usage()