#!/usr/bin/env python3
"""
Example usage of the RSSProcessor class.

This script demonstrates how to use the new RSSProcessor class for fetching
and parsing RSS feeds both synchronously and asynchronously.
"""

import sys
import os
import time

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from podcast_player.core.rss_processor import RSSProcessor
from podcast_player.data.models import PodcastData, Episode


def example_synchronous_fetch():
    """Example of synchronous RSS feed fetching."""
    print("=== Synchronous RSS Fetch Example ===")
    
    processor = RSSProcessor()
    
    # Example RSS feed URL (replace with a real one for testing)
    rss_url = "https://feeds.npr.org/510289/podcast.xml"  # NPR Up First
    
    try:
        print(f"Fetching RSS feed: {rss_url}")
        podcast_data = processor.fetch_podcast(rss_url)
        
        print(f"Podcast Title: {podcast_data.title}")
        print(f"Feed URL: {podcast_data.feed_url}")
        print(f"Description: {podcast_data.description[:100]}..." if podcast_data.description else "No description")
        print(f"Number of episodes: {podcast_data.get_episode_count()}")
        
        # Show first 3 episodes
        for i, episode in enumerate(podcast_data.episodes[:3]):
            print(f"\nEpisode {i+1}:")
            print(f"  Title: {episode.title}")
            print(f"  Published: {episode.published}")
            print(f"  Duration: {episode.duration}")
            print(f"  Audio URL: {episode.audio_url[:50]}...")
            
    except Exception as e:
        print(f"Error fetching RSS feed: {e}")


def example_asynchronous_fetch():
    """Example of asynchronous RSS feed fetching with callbacks."""
    print("\n=== Asynchronous RSS Fetch Example ===")
    
    processor = RSSProcessor()
    rss_url = "https://feeds.npr.org/510289/podcast.xml"  # NPR Up First
    
    # Define callback functions
    def on_start():
        print("Starting RSS feed fetch...")
    
    def on_success(podcast_data: PodcastData):
        print(f"Successfully fetched: {podcast_data.title}")
        print(f"Episodes found: {podcast_data.get_episode_count()}")
        
        # Get latest episode
        latest = podcast_data.get_latest_episode()
        if latest:
            print(f"Latest episode: {latest.title}")
    
    def on_error(error_message: str):
        print(f"Error occurred: {error_message}")
    
    def on_complete():
        print("RSS fetch operation completed")
    
    # Start asynchronous fetch
    processor.fetch_podcast_thread(
        rss_url=rss_url,
        on_start=on_start,
        on_success=on_success,
        on_error=on_error,
        on_complete=on_complete
    )
    
    # Wait for the operation to complete
    print("Waiting for async operation to complete...")
    while processor.is_busy:
        time.sleep(0.1)
    
    print("Async operation finished")


def example_url_validation():
    """Example of RSS URL validation."""
    print("\n=== RSS URL Validation Example ===")
    
    processor = RSSProcessor()
    
    test_urls = [
        "https://feeds.npr.org/510289/podcast.xml",  # Valid
        "http://example.com/rss.xml",  # Valid format
        "https://podcast.example.com/feed",  # Valid format  
        "not-a-url",  # Invalid
        "",  # Empty
        "ftp://example.com/feed.xml",  # Wrong protocol
        "https://example.com/page.html"  # No RSS indicators
    ]
    
    for url in test_urls:
        is_valid = processor.is_valid_rss_url(url)
        print(f"URL: {url or '(empty)':<40} Valid: {is_valid}")


def main():
    """Run all examples."""
    try:
        example_synchronous_fetch()
        example_asynchronous_fetch()
        example_url_validation()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()