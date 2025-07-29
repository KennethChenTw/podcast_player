"""
Playback Memory System for Podcast Player

Tracks and restores playback positions for episodes across sessions.
Provides intelligent resume functionality with configurable behavior.
"""

import json
import os
import time
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from .error_handler import ConfigError, ErrorHandler
from .logger import PodcastLogger


@dataclass
class PlaybackPosition:
    """Represents a saved playback position."""
    episode_url: str
    episode_title: str
    position_seconds: float
    duration_seconds: float
    last_played: str  # ISO format timestamp
    play_count: int = 1
    completion_percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaybackPosition':
        """Create instance from dictionary."""
        return cls(**data)
    
    def is_completed(self, completion_threshold: float = 0.95) -> bool:
        """Check if episode is considered completed."""
        return self.completion_percentage >= completion_threshold
    
    def should_resume(self, min_position: float = 30.0, max_age_days: int = 30) -> bool:
        """
        Determine if this position should offer resume.
        
        Args:
            min_position: Minimum seconds to consider resuming
            max_age_days: Maximum age in days to offer resume
            
        Returns:
            bool: True if should offer resume
        """
        # Don't resume if too little progress
        if self.position_seconds < min_position:
            return False
        
        # Don't resume if already completed
        if self.is_completed():
            return False
        
        # Don't resume if too old
        try:
            last_played = datetime.fromisoformat(self.last_played)
            age = datetime.now() - last_played
            if age.days > max_age_days:
                return False
        except ValueError:
            # Invalid timestamp, don't resume
            return False
        
        return True
    
    def get_resume_time_formatted(self) -> str:
        """Get formatted resume time for display."""
        minutes = int(self.position_seconds // 60)
        seconds = int(self.position_seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"


class PlaybackMemory:
    """Manages playback position memory across sessions."""
    
    def __init__(self, data_dir: Optional[str] = None, 
                 logger: Optional[PodcastLogger] = None,
                 error_handler: Optional[ErrorHandler] = None):
        """
        Initialize playback memory system.
        
        Args:
            data_dir: Directory for storing position data
            logger: Logger instance
            error_handler: Error handler instance
        """
        self.logger = logger
        self.error_handler = error_handler
        
        # Set up data directory
        if data_dir is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            data_dir = os.path.join(script_dir, "data")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.positions_file = self.data_dir / "playback_positions.json"
        self.positions: Dict[str, PlaybackPosition] = {}
        
        # Configuration
        self.auto_save_interval = 30.0  # seconds
        self.min_save_progress = 5.0   # minimum seconds to save
        self.completion_threshold = 0.95  # 95% to mark as completed
        self.max_positions = 1000  # maximum positions to store
        
        # Runtime state
        self.last_save_time = 0.0
        self.current_episode_url: Optional[str] = None
        self.position_update_callbacks = []
        
        # Load existing positions
        self.load_positions()
        
        if self.logger:
            self.logger.info(f"PlaybackMemory initialized with {len(self.positions)} saved positions")
    
    def load_positions(self) -> bool:
        """
        Load saved playback positions from file.
        
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not self.positions_file.exists():
                self.positions = {}
                return True
            
            with open(self.positions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.positions = {}
            for url, pos_data in data.items():
                try:
                    self.positions[url] = PlaybackPosition.from_dict(pos_data)
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Failed to load position for {url}: {e}")
                    continue
            
            if self.logger:
                self.logger.info(f"Loaded {len(self.positions)} playback positions")
            
            return True
            
        except Exception as e:
            error = ConfigError(f"Failed to load playback positions: {e}", str(self.positions_file))
            if self.error_handler:
                self.error_handler.handle_error(error, "PlaybackMemory.load_positions")
            elif self.logger:
                self.logger.error(f"Failed to load playback positions: {e}")
            
            # Start with empty positions on error
            self.positions = {}
            return False
    
    def save_positions(self, force: bool = False) -> bool:
        """
        Save playback positions to file.
        
        Args:
            force: Force save even if auto-save interval hasn't passed
            
        Returns:
            bool: True if saved successfully
        """
        current_time = time.time()
        
        # Check if we should save (rate limiting)
        if not force and (current_time - self.last_save_time) < self.auto_save_interval:
            return True
        
        try:
            # Convert positions to dict format
            data = {}
            for url, position in self.positions.items():
                data[url] = position.to_dict()
            
            # Write to temporary file first, then rename (atomic operation)
            temp_file = self.positions_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_file.replace(self.positions_file)
            
            self.last_save_time = current_time
            
            if self.logger:
                self.logger.debug(f"Saved {len(self.positions)} playback positions")
            
            return True
            
        except Exception as e:
            error = ConfigError(f"Failed to save playback positions: {e}", str(self.positions_file))
            if self.error_handler:
                self.error_handler.handle_error(error, "PlaybackMemory.save_positions")
            elif self.logger:
                self.logger.error(f"Failed to save playback positions: {e}")
            
            return False
    
    def update_position(self, episode_url: str, episode_title: str,
                       position_seconds: float, duration_seconds: float) -> None:
        """
        Update playback position for an episode.
        
        Args:
            episode_url: URL of the episode
            episode_title: Title of the episode
            position_seconds: Current position in seconds
            duration_seconds: Total duration in seconds
        """
        # Don't save very short progress
        if position_seconds < self.min_save_progress:
            return
        
        # Calculate completion percentage
        completion_percentage = position_seconds / duration_seconds if duration_seconds > 0 else 0.0
        
        # Update or create position
        if episode_url in self.positions:
            existing = self.positions[episode_url]
            existing.position_seconds = position_seconds
            existing.duration_seconds = duration_seconds
            existing.completion_percentage = completion_percentage
            existing.last_played = datetime.now().isoformat()
            # Don't increment play_count for position updates
        else:
            self.positions[episode_url] = PlaybackPosition(
                episode_url=episode_url,
                episode_title=episode_title,
                position_seconds=position_seconds,
                duration_seconds=duration_seconds,
                completion_percentage=completion_percentage,
                last_played=datetime.now().isoformat(),
                play_count=1
            )
        
        # Cleanup old positions if we have too many
        self._cleanup_old_positions()
        
        # Auto-save if enough time has passed
        self.save_positions()
        
        # Notify callbacks
        for callback in self.position_update_callbacks:
            try:
                callback(episode_url, position_seconds, duration_seconds)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Position update callback failed: {e}")
    
    def start_episode(self, episode_url: str, episode_title: str) -> None:
        """
        Mark the start of episode playback.
        
        Args:
            episode_url: URL of the episode
            episode_title: Title of the episode
        """
        self.current_episode_url = episode_url
        
        # Increment play count
        if episode_url in self.positions:
            self.positions[episode_url].play_count += 1
        
        if self.logger:
            self.logger.log_audio_event("start", episode_title)
    
    def get_resume_position(self, episode_url: str) -> Optional[PlaybackPosition]:
        """
        Get resume position for an episode if available.
        
        Args:
            episode_url: URL of the episode
            
        Returns:
            PlaybackPosition if should resume, None otherwise
        """
        if episode_url not in self.positions:
            return None
        
        position = self.positions[episode_url]
        if position.should_resume():
            return position
        
        return None
    
    def mark_completed(self, episode_url: str) -> None:
        """
        Mark an episode as completed.
        
        Args:
            episode_url: URL of the episode
        """
        if episode_url in self.positions:
            self.positions[episode_url].completion_percentage = 1.0
            self.positions[episode_url].last_played = datetime.now().isoformat()
            self.save_positions(force=True)
            
            if self.logger:
                title = self.positions[episode_url].episode_title
                self.logger.log_audio_event("completed", title)
    
    def remove_position(self, episode_url: str) -> bool:
        """
        Remove a saved position.
        
        Args:
            episode_url: URL of the episode
            
        Returns:
            bool: True if removed, False if not found
        """
        if episode_url in self.positions:
            del self.positions[episode_url]
            self.save_positions(force=True)
            return True
        return False
    
    def get_recently_played(self, limit: int = 10) -> list[PlaybackPosition]:
        """
        Get recently played episodes.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of recently played positions
        """
        positions = list(self.positions.values())
        
        # Sort by last played time (most recent first)
        try:
            positions.sort(key=lambda p: datetime.fromisoformat(p.last_played), reverse=True)
        except ValueError:
            # Fallback sorting if timestamps are invalid
            positions.sort(key=lambda p: p.last_played, reverse=True)
        
        return positions[:limit]
    
    def get_in_progress(self) -> list[PlaybackPosition]:
        """
        Get episodes that are in progress (not completed).
        
        Returns:
            List of in-progress positions
        """
        in_progress = []
        for position in self.positions.values():
            if not position.is_completed() and position.should_resume():
                in_progress.append(position)
        
        # Sort by last played time (most recent first)
        try:
            in_progress.sort(key=lambda p: datetime.fromisoformat(p.last_played), reverse=True)
        except ValueError:
            in_progress.sort(key=lambda p: p.last_played, reverse=True)
        
        return in_progress
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get playback statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_positions = len(self.positions)
        completed = sum(1 for p in self.positions.values() if p.is_completed())
        in_progress = sum(1 for p in self.positions.values() if not p.is_completed() and p.should_resume())
        
        total_listening_time = sum(p.position_seconds for p in self.positions.values())
        total_play_count = sum(p.play_count for p in self.positions.values())
        
        # Find most played
        most_played = max(self.positions.values(), key=lambda p: p.play_count, default=None)
        
        return {
            'total_episodes': total_positions,
            'completed_episodes': completed,
            'in_progress_episodes': in_progress,
            'total_listening_hours': total_listening_time / 3600,
            'total_play_count': total_play_count,
            'most_played_episode': most_played.episode_title if most_played else None,
            'most_played_count': most_played.play_count if most_played else 0
        }
    
    def add_position_update_callback(self, callback: callable) -> None:
        """
        Add callback for position updates.
        
        Args:
            callback: Function called with (episode_url, position, duration)
        """
        self.position_update_callbacks.append(callback)
    
    def remove_position_update_callback(self, callback: callable) -> None:
        """Remove position update callback."""
        if callback in self.position_update_callbacks:
            self.position_update_callbacks.remove(callback)
    
    def _cleanup_old_positions(self) -> None:
        """Clean up old positions if we exceed the maximum."""
        if len(self.positions) <= self.max_positions:
            return
        
        # Sort by last played time and keep only the most recent ones
        positions_list = list(self.positions.items())
        try:
            positions_list.sort(key=lambda x: datetime.fromisoformat(x[1].last_played), reverse=True)
        except ValueError:
            positions_list.sort(key=lambda x: x[1].last_played, reverse=True)
        
        # Keep only the most recent positions
        positions_to_keep = positions_list[:self.max_positions]
        self.positions = dict(positions_to_keep)
        
        if self.logger:
            removed_count = len(positions_list) - len(positions_to_keep)
            self.logger.info(f"Cleaned up {removed_count} old playback positions")
    
    def export_data(self, output_file: Optional[str] = None) -> str:
        """
        Export playback data to JSON file.
        
        Args:
            output_file: Output file path
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.data_dir / f"playback_export_{timestamp}.json"
        
        export_data = {
            'export_time': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'positions': {url: pos.to_dict() for url, pos in self.positions.items()}
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        if self.logger:
            self.logger.info(f"Playback data exported to: {output_file}")
        
        return str(output_file)
    
    def cleanup(self) -> None:
        """Cleanup and save final state."""
        self.save_positions(force=True)
        if self.logger:
            self.logger.info("PlaybackMemory cleanup completed")