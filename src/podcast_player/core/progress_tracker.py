"""
Progress Tracker for Podcast Player

Handles progress tracking and UI updates for audio playback
with threading support for non-blocking operations.
"""

import threading
import time
from typing import Callable, Optional


class ProgressTracker:
    """Tracks audio playback progress and manages UI updates."""
    
    def __init__(self):
        """Initialize progress tracker."""
        self.is_tracking = False
        self._tracking_thread: Optional[threading.Thread] = None
        self._stop_requested = False
        self.update_interval = 1.0  # Update every second
    
    def start_tracking(self, 
                      audio_player,
                      progress_callback: Callable[[int, int], None],
                      completion_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Start tracking playback progress.
        
        Args:
            audio_player: AudioPlayer instance to track
            progress_callback: Function called with (current_pos, duration)
            completion_callback: Function called when playback completes
        """
        # Stop any existing tracking
        self.stop_tracking()
        
        def _tracking_worker():
            try:
                self.is_tracking = True
                self._stop_requested = False
                
                while not self._stop_requested and audio_player.is_playing:
                    if not audio_player.is_paused:
                        current_pos = audio_player.get_position()
                        duration = audio_player.get_duration()
                        
                        # Call progress callback
                        try:
                            progress_callback(current_pos, duration)
                        except Exception as e:
                            print(f"Error in progress callback: {e}")
                    
                    # Wait for next update
                    for _ in range(int(self.update_interval * 10)):
                        if self._stop_requested:
                            break
                        time.sleep(0.1)
                
                # Check if playback completed naturally
                if not self._stop_requested and not audio_player.is_playing and completion_callback:
                    try:
                        completion_callback()
                    except Exception as e:
                        print(f"Error in completion callback: {e}")
                        
            except Exception as e:
                print(f"Error in progress tracking: {e}")
            finally:
                self.is_tracking = False
                self._tracking_thread = None
        
        # Start tracking thread
        self._tracking_thread = threading.Thread(target=_tracking_worker, daemon=True)
        self._tracking_thread.start()
    
    def stop_tracking(self) -> None:
        """Stop progress tracking."""
        self._stop_requested = True
        self.is_tracking = False
        
        # Wait for thread to finish (with timeout)
        if self._tracking_thread and self._tracking_thread.is_alive():
            self._tracking_thread.join(timeout=1.0)
        
        self._tracking_thread = None
    
    def set_update_interval(self, interval: float) -> None:
        """
        Set progress update interval.
        
        Args:
            interval: Update interval in seconds
        """
        self.update_interval = max(0.1, interval)  # Minimum 0.1 seconds
    
    def is_active(self) -> bool:
        """
        Check if progress tracking is currently active.
        
        Returns:
            bool: True if tracking is active, False otherwise
        """
        return self.is_tracking and self._tracking_thread is not None and self._tracking_thread.is_alive()


class UIUpdateManager:
    """Manages UI updates for the podcast player."""
    
    def __init__(self):
        """Initialize UI update manager."""
        self.update_callbacks = {}
        self._ui_thread: Optional[threading.Thread] = None
        self._stop_ui_updates = False
    
    def register_callback(self, name: str, callback: Callable) -> None:
        """
        Register a UI update callback.
        
        Args:
            name: Callback name for identification
            callback: Function to call for UI updates
        """
        self.update_callbacks[name] = callback
    
    def unregister_callback(self, name: str) -> None:
        """
        Unregister a UI update callback.
        
        Args:
            name: Callback name to remove
        """
        self.update_callbacks.pop(name, None)
    
    def update_play_ui(self, is_playing: bool, is_paused: bool, is_loading: bool) -> None:
        """
        Update UI based on playback state.
        
        Args:
            is_playing: Whether audio is playing
            is_paused: Whether audio is paused
            is_loading: Whether audio is loading
        """
        state = {
            'is_playing': is_playing,
            'is_paused': is_paused,
            'is_loading': is_loading
        }
        
        # Call registered callbacks
        for name, callback in self.update_callbacks.items():
            try:
                callback('playback_state', state)
            except Exception as e:
                print(f"Error in UI callback '{name}': {e}")
    
    def update_progress_ui(self, current_pos: int, duration: int) -> None:
        """
        Update UI with progress information.
        
        Args:
            current_pos: Current position in seconds
            duration: Total duration in seconds
        """
        progress_data = {
            'current_pos': current_pos,
            'duration': duration,
            'percentage': (current_pos / duration * 100) if duration > 0 else 0
        }
        
        # Call registered callbacks
        for name, callback in self.update_callbacks.items():
            try:
                callback('progress', progress_data)
            except Exception as e:
                print(f"Error in UI progress callback '{name}': {e}")
    
    def update_playlist_ui(self, current_index: int, total_tracks: int, track_title: str = "") -> None:
        """
        Update UI with playlist information.
        
        Args:
            current_index: Current track index
            total_tracks: Total number of tracks
            track_title: Current track title
        """
        playlist_data = {
            'current_index': current_index,
            'total_tracks': total_tracks,
            'track_title': track_title,
            'has_previous': current_index > 0,
            'has_next': current_index < total_tracks - 1
        }
        
        # Call registered callbacks
        for name, callback in self.update_callbacks.items():
            try:
                callback('playlist', playlist_data)
            except Exception as e:
                print(f"Error in UI playlist callback '{name}': {e}")
    
    def start_ui_updates(self, update_interval: float = 0.5) -> None:
        """
        Start periodic UI updates.
        
        Args:
            update_interval: Update interval in seconds
        """
        def _ui_update_worker():
            while not self._stop_ui_updates:
                # Perform periodic updates here if needed
                time.sleep(update_interval)
        
        self.stop_ui_updates()
        self._stop_ui_updates = False
        self._ui_thread = threading.Thread(target=_ui_update_worker, daemon=True)
        self._ui_thread.start()
    
    def stop_ui_updates(self) -> None:
        """Stop periodic UI updates."""
        self._stop_ui_updates = True
        
        if self._ui_thread and self._ui_thread.is_alive():
            self._ui_thread.join(timeout=1.0)
        
        self._ui_thread = None
    
    def clear_callbacks(self) -> None:
        """Clear all registered callbacks."""
        self.update_callbacks.clear()


def format_time(seconds: int) -> str:
    """
    Format time in seconds to HH:MM:SS or MM:SS format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        str: Formatted time string
    """
    if seconds < 0:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def calculate_progress_percentage(current: int, total: int) -> float:
    """
    Calculate progress as percentage.
    
    Args:
        current: Current position
        total: Total duration
        
    Returns:
        float: Progress percentage (0.0 to 100.0)
    """
    if total <= 0:
        return 0.0
    return min(100.0, max(0.0, (current / total) * 100.0))