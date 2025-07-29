"""
Core functionality modules for the podcast player
"""

from .config_manager import ConfigManager

# Import modules that might have optional dependencies conditionally
try:
    from .rss_processor import RSSProcessor
    _rss_available = True
except ImportError:
    _rss_available = False

# Import new modules
from .error_handler import ErrorHandler, PodcastError, NetworkError, AudioError, ConfigError, RSSError
from .logger import PodcastLogger, PerformanceMonitor
from .playback_memory import PlaybackMemory, PlaybackPosition

# Import modules that might need tkinter conditionally
try:
    from .station_manager import StationManager
    from .playlist_manager import PlaylistManager
    _station_available = True
except ImportError:
    _station_available = False

from .progress_tracker import ProgressTracker

# Import audio player with optional pygame dependency
try:
    from .audio_player import AudioPlayer
    _audio_available = True
except ImportError:
    _audio_available = False

__all__ = [
    "ConfigManager",
    "ErrorHandler", 
    "PodcastError", 
    "NetworkError", 
    "AudioError", 
    "ConfigError", 
    "RSSError",
    "PodcastLogger",
    "PerformanceMonitor", 
    "PlaybackMemory",
    "PlaybackPosition",
    "ProgressTracker"
]

if _audio_available:
    __all__.append("AudioPlayer")

if _rss_available:
    __all__.append("RSSProcessor")

if _station_available:
    __all__.extend(["StationManager", "PlaylistManager"])