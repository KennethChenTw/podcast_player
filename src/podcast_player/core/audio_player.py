"""
Audio Player for Podcast Player

Handles audio playback using python-vlc with support for various
audio formats, volume control, seeking, and progress tracking.
"""

import os
import tempfile
import shutil
import threading
import time
from typing import Optional, Callable, Dict, Any

# Import vlc
import vlc

from .error_handler import ErrorHandler, AudioError, NetworkError, safe_execute
from .logger import PodcastLogger, PerformanceMonitor


class AudioPlayer:
    """Handles audio playback functionality."""
    
    def __init__(self, logger: Optional[PodcastLogger] = None, 
                 error_handler: Optional[ErrorHandler] = None):
        """
        Initialize the audio player.
        
        Args:
            logger: Logger instance for audio events
            error_handler: Error handler for audio errors
        """
        self.is_playing = False
        self.is_paused = False
        self.current_pos = 0
        self.duration = 0
        self.volume = 0.7
        self.current_temp_dir: Optional[str] = None
        self.is_loading = False
        self.play_request_id = 0 # Used to cancel old playback requests
        self.playback_speed = 1.0  # Normal speed
        self.supported_speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        
        # Enhanced error handling and logging
        self.logger = logger
        self.error_handler = error_handler
        
        # Initialize vlc player
        self.vlc_instance: Optional[vlc.Instance] = None
        self.player: Optional[vlc.MediaPlayer] = None
        self.init_player()
    
    def init_player(self) -> None:
        """Initialize vlc player."""
        if self.logger:
            self.logger.info("Initializing audio player with python-vlc")
        
        try:
            # Pass --no-xlib to prevent X11 errors on some systems
            self.vlc_instance = vlc.Instance("--no-xlib")
            self.player = self.vlc_instance.media_player_new()
            self.player.audio_set_volume(int(self.volume * 100)) # VLC volume is 0-100
            
            if self.logger:
                self.logger.info("Audio player initialized successfully")
                
        except Exception as e:
            error = AudioError(f"Failed to initialize python-vlc: {e}")
            if self.error_handler:
                self.error_handler.handle_error(error, "AudioPlayer.init_player")
            elif self.logger:
                self.logger.error(f"Error initializing audio player: {e}")
            else:
                print(f"Error initializing audio player: {e}")
            raise
    
    def play_track(self, url: str, title: str = "", 
                  progress_callback: Optional[Callable[[int, int], None]] = None,
                  completion_callback: Optional[Callable[[], None]] = None,
                  error_callback: Optional[Callable[[str], None]] = None) -> None:
        """
        Play an audio track from URL.
        
        Args:
            url: Audio file URL
            title: Track title for display
            progress_callback: Called with (current_pos, duration) during playback
            completion_callback: Called when track finishes
            error_callback: Called with error message on failure
        """
        if self.logger:
            self.logger.info(f"Starting playback: {title}")
        
        # Increment play_request_id to cancel any previous requests
        self.play_request_id += 1
        current_request_id = self.play_request_id

        def _play_worker():
            try:
                self.is_loading = True
                if self.logger:
                    self.logger.info("Play worker thread started")
                
                # Stop current playback if any
                if self.player and self.player.is_playing():
                    self.player.stop()
                
                # VLC can play directly from URL, no need to download to temp file first
                # However, for stability with some URLs, downloading might still be preferred.
                # For now, let's try direct URL playback. If issues arise, we can re-introduce download.
                
                media = self.vlc_instance.media_new(url)
                self.player.set_media(media)
                
                # Check if a new request has superseded this one
                if current_request_id != self.play_request_id:
                    if self.logger:
                        self.logger.info(f"Playback request {current_request_id} superseded by {self.play_request_id}")
                    if self.player:
                        self.player.stop() # Ensure player is stopped if superseded
                    return

                self.player.play()
                
                # Give VLC a moment to start playing and get media info
                # Wait up to 2 seconds for playback to actually start
                start_time = time.time()
                while not self.player.is_playing() and (time.time() - start_time) < 2.0:
                    time.sleep(0.1) 

                if self.logger:
                    self.logger.info(f"VLC player state after play: {self.player.get_state()}")
                    self.logger.info(f"VLC player is_playing: {self.player.is_playing()}")
                    self.logger.info(f"VLC player current_time: {self.player.get_time()}")
                    self.logger.info(f"VLC player duration: {self.player.get_length()}")

                self.is_playing = self.player.is_playing() # Get actual state from player
                self.is_paused = False
                self.is_loading = False
                
                # Set initial playback speed
                if self.is_playing: # Only set rate if actually playing
                    self.player.set_rate(self.playback_speed)

                if self.logger and self.is_playing:
                    self.logger.info("Playback started successfully")
                elif self.logger:
                    self.logger.warning("Playback did not start as expected.")
                
                # Start progress tracking
                if progress_callback and self.is_playing:
                    self._track_progress(progress_callback, completion_callback, current_request_id)
                elif not self.is_playing and error_callback:
                    error_callback("音訊播放失敗，請檢查 URL 或網路連線。")
                
            except Exception as e:
                self.is_loading = False
                error_msg = f"Error playing track: {str(e)}"
                if self.logger:
                    self.logger.error(error_msg)
                if error_callback:
                    error_callback(error_msg)
                    
                # Print traceback for debugging
                import traceback
                traceback.print_exc()
            finally:
                # Cleanup temp files if any were downloaded (not used in this version)
                self._cleanup_temp_dir()
        
        # Start playback in separate thread
        threading.Thread(target=_play_worker, daemon=True).start()
    
    def _download_audio(self, url: str) -> str:
        """
        Download audio file to a temporary location (kept for potential future use).
        
        Args:
            url: Audio file URL
            
        Returns:
            str: Path to downloaded audio file
            
        Raises:
            Exception: If download fails
        """
        import requests
        
        if self.logger:
            self.logger.info(f"Downloading audio from: {url[:50]}...")
        
        # Clean up previous temp directory
        self._cleanup_temp_dir()
        
        # Create new temp directory
        self.current_temp_dir = tempfile.mkdtemp()
        
        # Download the audio file
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Determine file extension
        content_type = response.headers.get('content-type', '')
        if 'mp3' in content_type or 'mpeg' in content_type:
            extension = '.mp3'
        elif 'wav' in content_type:
            extension = '.wav'
        elif 'ogg' in content_type:
            extension = '.ogg'
        else:
            # Try to get extension from URL
            extension = os.path.splitext(url)[1] or '.mp3'
        
        # Save downloaded file
        audio_file = os.path.join(self.current_temp_dir, f"audio{extension}")
        
        if self.logger:
            self.logger.info(f"Saving audio as: {audio_file}")
        
        with open(audio_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(audio_file)
        if self.logger:
            self.logger.info(f"Audio download completed: {file_size} bytes")
        
        return audio_file
    
    def _track_progress(self, progress_callback: Callable[[int, int], None],
                       completion_callback: Optional[Callable[[], None]],
                       request_id: int) -> None:
        """
        Track playback progress in a separate thread using VLC's state.
        
        Args:
            progress_callback: Function to call with progress updates
            completion_callback: Function to call when playback completes
            request_id: Request ID to check if operation is still valid
        """
        def _progress_worker():
            try:
                if self.logger:
                    self.logger.info("Progress tracking started with python-vlc")
                
                while self.player and self.player.is_playing() and request_id == self.play_request_id:
                    current_time_ms = self.player.get_time() # milliseconds
                    total_duration_ms = self.player.get_length() # milliseconds
                    
                    current_time_s = int(current_time_ms / 1000) if current_time_ms != -1 else 0
                    total_duration_s = int(total_duration_ms / 1000) if total_duration_ms != -1 else 0
                    
                    self.current_pos = current_time_s
                    self.duration = total_duration_s
                    
                    progress_callback(self.current_pos, self.duration)
                    time.sleep(0.5) # Update every 0.5 seconds
                    
                # Playback finished or stopped
                if self.player and not self.player.is_playing() and request_id == self.play_request_id:
                    if self.logger:
                        self.logger.info("Playback finished")
                    self.is_playing = False
                    self.is_paused = False
                    if completion_callback:
                        completion_callback()
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Progress tracking error: {e}")
                print(f"Progress tracking error: {e}")
        
        threading.Thread(target=_progress_worker, daemon=True).start()
    
    def toggle_play(self) -> bool:
        """
        Toggle between play and pause.
        
        Returns:
            bool: True if now playing, False if paused
        """
        if self.player:
            if self.player.is_playing():
                self.player.pause()
                self.is_paused = True
                self.is_playing = True # Still considered playing, just paused
                return False
            elif self.is_paused:
                self.player.play() # Resume
                self.is_paused = False
                self.is_playing = True
                return True
            else:
                # If not playing and not paused, it means it's stopped or not loaded.
                # This logic should ideally be handled by event_handlers or playlist_manager
                # For now, just return False if nothing is loaded/playing.
                return False
        return False
    
    def stop(self) -> None:
        """Stop audio playback and cleanup."""
        self.play_request_id += 1  # Cancel any pending operations
        
        if self.player:
            self.player.stop()
        
        self.is_playing = False
        self.is_paused = False
        self.current_pos = 0
        self.duration = 0 # Reset duration on stop
        self.is_loading = False
        
        self._cleanup_temp_dir() # Clean up temp files
    
    def set_volume(self, volume: float) -> None:
        """
        Set audio volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        if self.player:
            self.player.audio_set_volume(int(self.volume * 100)) # VLC volume is 0-100
    
    def get_volume(self) -> float:
        """Get current volume level."""
        if self.player:
            return self.player.audio_get_volume() / 100.0
        return self.volume
    
    def seek(self, position: int) -> None:
        """
        Seek to a specific position in seconds.
        
        Args:
            position: Position in seconds
        """
        if self.player and self.player.is_seekable():
            if self.logger:
                self.logger.info(f"Seeking to {position}s")
            self.player.set_time(position * 1000) # VLC uses milliseconds
            self.current_pos = position # Update current_pos immediately
        elif self.logger:
            self.logger.warning(f"Seek to {position}s failed: Player not seekable or not initialized.")
    
    def get_position(self) -> int:
        """Get current playback position in seconds."""
        if self.player and self.player.is_playing():
            return int(self.player.get_time() / 1000) if self.player.get_time() != -1 else 0
        return self.current_pos # Return last known position if not playing
    
    def get_duration(self) -> int:
        """Get track duration in seconds."""
        if self.player and self.player.get_media() and self.player.get_length() != -1:
            return int(self.player.get_length() / 1000)
        return self.duration # Return last known duration
    
    def set_duration(self, duration: int) -> None:
        """Set track duration (called from external source)."""
        # With VLC, duration is usually determined by the player itself.
        # This method might become less relevant, but keep for compatibility.
        self.duration = duration
    
    def is_busy(self) -> bool:
        """Check if player is currently loading or playing."""
        return self.is_loading or (self.player and self.player.is_playing())
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get current player state.
        
        Returns:
            Dict with player state information
        """
        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'is_loading': self.is_loading,
            'current_pos': self.get_position(), # Use getter for accurate position
            'duration': self.get_duration(),   # Use getter for accurate duration
            'volume': self.get_volume(), # Use getter for accurate volume
            'playback_speed': self.get_playback_speed()
        }
    
    def get_supported_speeds(self) -> list:
        """
        Get list of supported playback speeds.
        
        Returns:
            List of supported speed multipliers
        """
        return self.supported_speeds.copy()
    
    def set_playback_speed(self, speed: float) -> bool:
        """
        Set playback speed.
        
        Args:
            speed: Speed multiplier (0.5 to 2.0)
            
        Returns:
            True if speed was set successfully
        """
        try:
            if self.player and self.player.is_playing() and speed in self.supported_speeds:
                self.player.set_rate(speed)
                self.playback_speed = speed
                
                # Log speed change
                if self.logger:
                    self.logger.log_action(f"Playback speed changed to {speed}x")
                
                return True
            else:
                if self.error_handler:
                    self.error_handler.handle_error(
                        AudioError(f"Unsupported playback speed or player not ready: {speed}")
                    )
                return False
                
        except Exception as e:
            if self.error_handler:
                self.error_handler.handle_error(
                    AudioError(f"Error setting playback speed: {str(e)}")
                )
            return False
    
    def get_playback_speed(self) -> float:
        """
        Get current playback speed.
        
        Returns:
            Current speed multiplier
        """
        if self.player:
            return self.player.get_rate()
        return self.playback_speed
    
    def cycle_playback_speed(self) -> float:
        """
        Cycle to next playback speed.
        
        Returns:
            New playback speed
        """
        try:
            current_index = self.supported_speeds.index(self.playback_speed)
            next_index = (current_index + 1) % len(self.supported_speeds)
            new_speed = self.supported_speeds[next_index]
            
            self.set_playback_speed(new_speed)
            return new_speed
            
        except (ValueError, IndexError):
            # If current speed is not in supported list, reset to normal
            self.set_playback_speed(1.0)
            return 1.0
    
    def _cleanup_temp_dir(self) -> None:
        """Clean up the current temporary directory."""
        if self.current_temp_dir and os.path.exists(self.current_temp_dir):
            try:
                shutil.rmtree(self.current_temp_dir)
                self.current_temp_dir = None
                if self.logger:
                    self.logger.info(f"Cleaned up temp directory: {self.current_temp_dir}")
            except OSError as e:
                if self.logger:
                    self.logger.error(f"Error cleaning up temp directory {self.current_temp_dir}: {e}")
                print(f"Error cleaning up temp directory {self.current_temp_dir}: {e}")
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """
        Format time in seconds to MM:SS format.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            str: Formatted time string
        """
        if seconds < 0:
            return "00:00"
        
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop()
        self._cleanup_temp_dir()
