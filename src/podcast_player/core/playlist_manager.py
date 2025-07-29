"""
Playlist Manager for Podcast Player

Handles playlist operations including track management, 
history tracking, import/export functionality.
"""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from tkinter import filedialog

from ..data.models import Track, Episode


class PlaylistManager:
    """Manages playlist operations and history tracking."""
    
    def __init__(self, history_file: str, playlist_file: str):
        """
        Initialize playlist manager.
        
        Args:
            history_file: Path to history JSON file
            playlist_file: Path to current playlist JSON file
        """
        self.history_file = history_file
        self.playlist_file = playlist_file
        self.playlist: List[Track] = []
        self.current_index = 0
        self.history: List[Dict[str, Any]] = []
        self.load_history()
        self.load_playlist()
    
    def add_track(self, track: Track | Episode) -> int:
        """
        Add a track or episode to the playlist.
        
        Args:
            track: Track or Episode to add
            
        Returns:
            int: The index of the newly added track.
        """
        if isinstance(track, Episode):
            duration = 0
            if track.duration:
                try:
                    # Try to parse duration if it's in HH:MM:SS or MM:SS format
                    parts = track.duration.split(':')
                    if len(parts) == 3:  # HH:MM:SS
                        duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:  # MM:SS
                        duration = int(parts[0]) * 60 + int(parts[1])
                    else:
                        duration = int(track.duration)
                except (ValueError, TypeError):
                    duration = 0
            
            new_track = Track(
                title=track.title,
                url=track.audio_url,
                duration=duration
            )
            self.playlist.append(new_track)
        else:
            self.playlist.append(track)
            
        return len(self.playlist) - 1
    
    def add_episode_as_track(self, episode: Episode) -> int:
        """
        Add an episode to the playlist as a track.
        
        Args:
            episode: Episode to add
            
        Returns:
            int: The index of the newly added track.
        """
        return self.add_track(episode)
    
    def remove_track(self, index: int) -> bool:
        """
        Remove a track from the playlist.
        
        Args:
            index: Index of track to remove
            
        Returns:
            bool: True if removed successfully, False if index invalid
        """
        if 0 <= index < len(self.playlist):
            self.playlist.pop(index)
            # Adjust current index if needed
            if index <= self.current_index:
                self.current_index = max(0, self.current_index - 1)
            return True
        return False
    
    def clear_playlist(self) -> None:
        """Clear all tracks from the playlist."""
        self.playlist.clear()
        self.current_index = 0
    
    def get_current_track(self) -> Optional[Track]:
        """
        Get the currently selected track.
        
        Returns:
            Track or None: Current track if valid index, None otherwise
        """
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None
    
    def get_track(self, index: int) -> Optional[Track]:
        """
        Get a track by index.
        
        Args:
            index: Track index
            
        Returns:
            Track or None: Track if valid index, None otherwise
        """
        if 0 <= index < len(self.playlist):
            return self.playlist[index]
        return None
    
    def set_current_index(self, index: int) -> bool:
        """
        Set the current track index.
        
        Args:
            index: New current index
            
        Returns:
            bool: True if index is valid, False otherwise
        """
        if 0 <= index < len(self.playlist):
            self.current_index = index
            return True
        return False
    
    def next_track(self) -> Optional[Track]:
        """
        Move to next track.
        
        Returns:
            Track or None: Next track if available, None otherwise
        """
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            return self.get_current_track()
        return None
    
    def previous_track(self) -> Optional[Track]:
        """
        Move to previous track.
        
        Returns:
            Track or None: Previous track if available, None otherwise
        """
        if self.current_index > 0:
            self.current_index -= 1
            return self.get_current_track()
        return None
    
    def get_playlist_size(self) -> int:
        """
        Get number of tracks in playlist.
        
        Returns:
            int: Number of tracks
        """
        return len(self.playlist)
    
    def get_playlist_copy(self) -> List[Track]:
        """
        Get a copy of the playlist.
        
        Returns:
            List[Track]: Copy of playlist
        """
        return self.playlist.copy()
    
    def populate_from_episodes(self, episodes: List[Episode]) -> None:
        """
        Populate playlist from episode list.
        
        Args:
            episodes: List of episodes to add
        """
        self.clear_playlist()
        for episode in episodes:
            self.add_episode_as_track(episode)

    def save_playlist(self) -> bool:
        """
        Save current playlist to a file.

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            playlist_data = {
                'tracks': [track.to_dict() for track in self.playlist],
                'current_index': self.current_index
            }
            
            directory = os.path.dirname(self.playlist_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

            with open(self.playlist_file, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError) as e:
            print(f"Error saving playlist: {e}")
            return False

    def load_playlist(self) -> bool:
        """
        Load playlist from a file.

        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.playlist_file):
                with open(self.playlist_file, 'r', encoding='utf-8') as f:
                    playlist_data = json.load(f)
                
                self.playlist = [Track.from_dict(track_data) for track_data in playlist_data.get('tracks', [])]
                self.current_index = playlist_data.get('current_index', 0)
                
                if self.current_index >= len(self.playlist):
                    self.current_index = 0
                return True
            return False
        except (json.JSONDecodeError, OSError, KeyError) as e:
            print(f"Error loading playlist: {e}")
            return False
    
    def save_history(self) -> bool:
        """
        Save current playlist to history.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            if not self.playlist:
                return True  # Nothing to save
            
            # Create history entry
            playlist_data = {
                'tracks': [track.to_dict() for track in self.playlist],
                'current_index': self.current_index,
                'timestamp': self._get_timestamp()
            }
            
            # Add to history (keep last 10 entries)
            self.history.append(playlist_data)
            if len(self.history) > 10:
                self.history = self.history[-10:]
            
            # Ensure directory exists
            directory = os.path.dirname(self.history_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Save to file
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            
            return True
        except (OSError, TypeError) as e:
            print(f"Error saving history: {e}")
            return False
    
    def load_history(self) -> bool:
        """
        Load history from file.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                return True
            else:
                self.history = []
                return False
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error loading history: {e}")
            self.history = []
            return False
    
    def restore_from_history(self, index: int = -1) -> bool:
        """
        Restore playlist from history entry.
        
        Args:
            index: History entry index (-1 for most recent)
            
        Returns:
            bool: True if restored successfully, False otherwise
        """
        try:
            if not self.history:
                return False
            
            if index < 0:
                index = len(self.history) + index
            
            if 0 <= index < len(self.history):
                entry = self.history[index]
                
                # Restore tracks
                self.playlist = [Track.from_dict(track_data) for track_data in entry['tracks']]
                self.current_index = entry.get('current_index', 0)
                
                # Ensure current index is valid
                if self.current_index >= len(self.playlist):
                    self.current_index = 0
                
                return True
            
            return False
        except (KeyError, TypeError, ValueError) as e:
            print(f"Error restoring from history: {e}")
            return False
    
    def clear_history(self) -> bool:
        """
        Clear all history entries.
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            self.history.clear()
            
            # Ensure directory exists
            directory = os.path.dirname(self.history_file)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            # Save empty history to file
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            
            return True
        except OSError as e:
            print(f"Error clearing history: {e}")
            return False
    
    def get_history_count(self) -> int:
        """
        Get number of history entries.
        
        Returns:
            int: Number of history entries
        """
        return len(self.history)
    
    def get_history_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of history entries.
        
        Returns:
            List[Dict]: List of history summaries
        """
        summaries = []
        for i, entry in enumerate(self.history):
            summary = {
                'index': i,
                'track_count': len(entry.get('tracks', [])),
                'timestamp': entry.get('timestamp', 'Unknown'),
                'current_track': entry.get('tracks', [{}])[entry.get('current_index', 0)].get('title', 'Unknown') if entry.get('tracks') else 'Empty'
            }
            summaries.append(summary)
        return summaries
    
    def export_playlist(self, parent_window=None) -> Tuple[bool, str]:
        """
        Export current playlist to JSON file.
        
        Args:
            parent_window: Tkinter parent window for dialog
            
        Returns:
            Tuple[bool, str]: (Success status, message)
        """
        try:
            if not self.playlist:
                return False, "No tracks to export"
            
            file_path = filedialog.asksaveasfilename(
                parent=parent_window,
                title="Export Playlist",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return False, "Export cancelled"
            
            playlist_data = {
                'tracks': [track.to_dict() for track in self.playlist],
                'current_index': self.current_index,
                'export_timestamp': self._get_timestamp()
            }
            
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(playlist_data, f, indent=2, ensure_ascii=False)
            
            return True, f"Exported {len(self.playlist)} tracks to {file_path}"
            
        except OSError as e:
            return False, f"Error writing file: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def import_playlist(self, parent_window=None) -> Tuple[bool, str]:
        """
        Import playlist from JSON file.
        
        Args:
            parent_window: Tkinter parent window for dialog
            
        Returns:
            Tuple[bool, str]: (Success status, message)  
        """
        try:
            file_path = filedialog.askopenfilename(
                parent=parent_window,
                title="Import Playlist",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return False, "Import cancelled"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                playlist_data = json.load(f)
            
            if not isinstance(playlist_data, dict):
                return False, "Invalid file format: expected JSON object"
            
            tracks_data = playlist_data.get('tracks', [])
            if not isinstance(tracks_data, list):
                return False, "Invalid playlist format: tracks must be a list"
            
            # Import tracks
            imported_tracks = []
            for track_data in tracks_data:
                try:
                    track = Track.from_dict(track_data)
                    imported_tracks.append(track)
                except (KeyError, TypeError):
                    continue  # Skip invalid tracks
            
            if not imported_tracks:
                return False, "No valid tracks found in file"
            
            # Append to current playlist
            self.playlist.extend(imported_tracks)
            
            # If playlist was empty, set current index to the start of imported tracks
            if len(self.playlist) == len(imported_tracks):
                self.current_index = 0
            
            return True, f"Imported {len(imported_tracks)} tracks"
            
        except json.JSONDecodeError:
            return False, "Invalid JSON file format"
        except OSError as e:
            return False, f"Error reading file: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_track_titles(self) -> List[str]:
        """
        Get list of track titles.
        
        Returns:
            List[str]: List of track titles
        """
        return [track.title for track in self.playlist]
    
    def find_track_by_title(self, title: str) -> Optional[int]:
        """
        Find track index by title.
        
        Args:
            title: Track title to search for
            
        Returns:
            int or None: Index if found, None otherwise
        """
        for i, track in enumerate(self.playlist):
            if track.title == title:
                return i
        return None
