"""
RSS Feed Processor for Podcast Player

Handles RSS feed fetching, parsing, and episode extraction with
support for both synchronous and asynchronous operations.
"""

import threading
import traceback
import time
from typing import Optional, Callable, List
from urllib.parse import urlparse

# Import required dependencies
import feedparser
import requests

from ..data.models import Episode, PodcastData
from ..utils.network_utils import NetworkUtils


class RSSProcessor:
    """Processes RSS feeds and extracts podcast episode data."""
    
    def __init__(self, config_manager, timeout: int = 30, max_retries: int = 3):
        """
        Initialize RSS processor.
        
        Args:
            config_manager: ConfigManager instance
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.config_manager = config_manager
        self.timeout = timeout
        self.max_retries = max_retries
        self._current_thread: Optional[threading.Thread] = None
        self._cancel_requested = False
        
        self._session = NetworkUtils.create_session(max_retries)
    
    @property
    def is_busy(self) -> bool:
        """Check if processor is currently fetching data."""
        return self._current_thread is not None and self._current_thread.is_alive()
    
    def cancel_current_operation(self) -> None:
        """Cancel any ongoing RSS fetch operation."""
        self._cancel_requested = True
    
    def validate_rss_url(self, url: str) -> bool:
        """
        Validate if URL looks like a valid RSS feed URL.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL appears valid, False otherwise
        """
        return NetworkUtils.is_valid_url(url)
    
    def _fetch_with_retry(self, url: str) -> requests.Response:
        """
        Fetch URL with exponential backoff retry mechanism.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTTP response object
            
        Raises:
            requests.RequestException: If all retry attempts fail
        """
        for attempt in range(self.max_retries + 1):
            if self._cancel_requested:
                raise requests.RequestException("Operation cancelled")
            
            try:
                response = self._session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if attempt == self.max_retries:
                    # Last attempt failed, re-raise the exception
                    raise e
                
                # Calculate exponential backoff delay
                delay = min(2 ** attempt, 60)  # Max 60 seconds delay
                
                print(f"RSS fetch attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
        
        # This should never be reached, but just in case
        raise requests.RequestException("Max retries exceeded")
    
    def fetch_podcast_thread(self, url: str, 
                           success_callback: Optional[Callable[[PodcastData], None]] = None,
                           error_callback: Optional[Callable[[str], None]] = None,
                           complete_callback: Optional[Callable[[], None]] = None) -> None:
        """
        Fetch podcast data in a separate thread (non-blocking).
        
        Args:
            url: RSS feed URL
            success_callback: Called with PodcastData on success
            error_callback: Called with error message on failure
            complete_callback: Called when operation completes (success or failure)
        """
        def _fetch_worker():
            try:
                self._cancel_requested = False
                podcast_data = self.fetch_podcast(url)
                
                if not self._cancel_requested and success_callback:
                    success_callback(podcast_data)
                    
            except Exception as e:
                if not self._cancel_requested and error_callback:
                    error_message = f"RSS fetch error: {str(e)}"
                    error_callback(error_message)
            finally:
                if complete_callback:
                    complete_callback()
                self._current_thread = None
        
        # Cancel any existing operation
        self.cancel_current_operation()
        
        # Start new thread
        self._current_thread = threading.Thread(target=_fetch_worker, daemon=True)
        self._current_thread.start()
    
    def fetch_podcast(self, url: str) -> PodcastData:
        """
        Fetch and parse RSS feed synchronously.
        
        Args:
            url: RSS feed URL
            
        Returns:
            PodcastData: Parsed podcast data
            
        Raises:
            ValueError: If URL is invalid
            requests.RequestException: If network request fails
            Exception: If RSS parsing fails
        """
        if not self.validate_rss_url(url):
            raise ValueError(f"Invalid RSS URL: {url}")
        
        try:
            # Check for cancellation
            if self._cancel_requested:
                raise Exception("Operation cancelled")
            
            # Fetch RSS content with retry mechanism
            response = self._fetch_with_retry(url)
            
            if self._cancel_requested:
                raise Exception("Operation cancelled")
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo and feed.bozo_exception:
                print(f"RSS parsing warning: {feed.bozo_exception}")
            
            # Extract podcast metadata
            podcast_title = getattr(feed.feed, 'title', 'Unknown Podcast')
            podcast_description = getattr(feed.feed, 'description', '')
            
            # Extract episodes
            episodes = []
            for entry in feed.entries:
                if self._cancel_requested:
                    raise Exception("Operation cancelled")
                
                episode = self._parse_episode(entry)
                if episode:
                    episodes.append(episode)
            
            if not episodes:
                raise Exception("No valid episodes found in RSS feed")

            # Apply episode loading preferences
            load_mode = self.config_manager.get_setting('episode_load_mode', 'all')
            if load_mode == 'latest':
                count = self.config_manager.get_setting('latest_episode_count', 10)
                episodes = episodes[:count]
            
            return PodcastData(
                title=podcast_title,
                feed_url=url,
                description=podcast_description,
                episodes=episodes
            )
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Network error fetching RSS feed: {str(e)}")
        except Exception as e:
            if "Operation cancelled" in str(e):
                raise e
            raise Exception(f"Error parsing RSS feed: {str(e)}")
    
    def _parse_episode(self, entry) -> Optional[Episode]:
        """
        Parse a single RSS entry into an Episode object.
        
        Args:
            entry: RSS feed entry from feedparser
            
        Returns:
            Episode or None if parsing fails
        """
        try:
            # Extract basic info
            title = getattr(entry, 'title', 'Unknown Episode')
            published = getattr(entry, 'published', '')
            summary = getattr(entry, 'summary', getattr(entry, 'description', ''))
            
            # Find audio URL
            audio_url = self._extract_audio_url(entry)
            if not audio_url:
                return None
            
            # Extract duration if available
            duration = self._extract_duration(entry)
            
            return Episode(
                title=title.strip(),
                published=published.strip(),
                summary=summary.strip(),
                audio_url=audio_url,
                duration=duration
            )
            
        except Exception as e:
            print(f"Error parsing episode: {e}")
            return None
    
    def _extract_audio_url(self, entry) -> Optional[str]:
        """Extract audio URL from RSS entry."""
        # Check enclosures first (most common)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if hasattr(enclosure, 'type') and enclosure.type and \
                   'audio' in enclosure.type.lower():
                    return getattr(enclosure, 'href', getattr(enclosure, 'url', None))
        
        # Check links
        if hasattr(entry, 'links'):
            for link in entry.links:
                if hasattr(link, 'type') and link.type and \
                   'audio' in link.type.lower():
                    return getattr(link, 'href', None)
        
        # Check media content (iTunes/media RSS)
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if hasattr(media, 'type') and media.type and \
                   'audio' in media.type.lower():
                    return getattr(media, 'url', None)
        
        return None
    
    def _extract_duration(self, entry) -> Optional[str]:
        """Extract episode duration from RSS entry."""
        # Check iTunes duration
        if hasattr(entry, 'itunes_duration'):
            return entry.itunes_duration
        
        # Check media duration
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if hasattr(media, 'duration'):
                    return media.duration
        
        return None
