"""
Data models for the podcast player application.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Episode:
    """Represents a podcast episode."""
    title: str
    published: str
    summary: str
    audio_url: str
    duration: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert episode to dictionary."""
        return {
            'title': self.title,
            'published': self.published,
            'summary': self.summary,
            'audio_url': self.audio_url,
            'duration': self.duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Episode':
        """Create episode from dictionary."""
        return cls(
            title=data.get('title', ''),
            published=data.get('published', ''),
            summary=data.get('summary', ''),
            audio_url=data.get('audio_url', ''),
            duration=data.get('duration')
        )


@dataclass
class Track:
    """Represents a playable track."""
    title: str
    url: str
    duration: int = 0  # Duration in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert track to dictionary."""
        return {
            'title': self.title,
            'url': self.url,
            'duration': self.duration
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Track':
        """Create track from dictionary."""
        return cls(
            title=data.get('title', ''),
            url=data.get('url', ''),
            duration=data.get('duration', 0)
        )


@dataclass
class PodcastData:
    """Represents podcast metadata and episodes."""
    title: str
    feed_url: str
    episodes: List[Episode]
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert podcast data to dictionary."""
        return {
            'title': self.title,
            'feed_url': self.feed_url,
            'description': self.description,
            'episodes': [episode.to_dict() for episode in self.episodes]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PodcastData':
        """Create podcast data from dictionary."""
        episodes = [Episode.from_dict(ep_data) for ep_data in data.get('episodes', [])]
        return cls(
            title=data.get('title', ''),
            feed_url=data.get('feed_url', ''),
            description=data.get('description'),
            episodes=episodes
        )
    
    def get_episode_count(self) -> int:
        """Get number of episodes."""
        return len(self.episodes)
    
    def get_latest_episode(self) -> Optional[Episode]:
        """Get the most recent episode."""
        return self.episodes[0] if self.episodes else None