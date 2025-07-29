#!/usr/bin/env python3
"""
Example integration script showing how to use the enhanced podcast player
with the new error handling, logging, and playback memory systems.
"""

import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from podcast_player.core import (
    ErrorHandler, PodcastLogger, PlaybackMemory, 
    ConfigManager, PerformanceMonitor
)

# Try to import AudioPlayer (may not be available if pygame is missing)
try:
    from podcast_player.core import AudioPlayer
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False


def main():
    """Main example integration."""
    print("🎵 Enhanced Podcast Player Example")
    print("="*50)
    
    # 1. Set up logging system
    print("\n1. Setting up logging system...")
    logger = PodcastLogger(
        name="ExampleApp",
        console_output=True,
        level=20  # INFO level
    )
    logger.log_system_info()
    
    # 2. Set up error handling
    print("\n2. Setting up error handling...")
    error_handler = ErrorHandler(logger=logger, show_gui_errors=False)
    
    # Register a custom recovery handler
    def audio_error_recovery(error, context):
        logger.info(f"Attempting recovery for audio error in {context}")
        # Could implement actual recovery logic here
        return False
    
    from podcast_player.core.error_handler import AudioError
    error_handler.register_recovery_handler(AudioError, audio_error_recovery)
    
    # 3. Set up playback memory
    print("\n3. Setting up playback memory...")
    playback_memory = PlaybackMemory(
        logger=logger,
        error_handler=error_handler
    )
    
    # 4. Set up audio player
    print("\n4. Setting up audio player...")
    if AUDIO_AVAILABLE:
        try:
            audio_player = AudioPlayer(
                logger=logger,
                error_handler=error_handler
            )
            
            # Check FFmpeg availability
            ffmpeg_available = audio_player.check_ffmpeg()
            if ffmpeg_available:
                logger.info("FFmpeg is available - full format support enabled")
            else:
                logger.warning("FFmpeg not available - limited format support")
                
        except Exception as e:
            logger.error(f"Failed to initialize audio player: {e}")
            return 1
    else:
        logger.warning("AudioPlayer not available (pygame missing) - using mock implementation")
        audio_player = None
    
    # 5. Demonstrate playback memory
    print("\n5. Demonstrating playback memory...")
    
    # Simulate some playback history
    episodes = [
        ("http://example.com/ep1.mp3", "Episode 1: Introduction", 450.0, 1800.0),
        ("http://example.com/ep2.mp3", "Episode 2: Getting Started", 1200.0, 2400.0),
        ("http://example.com/ep3.mp3", "Episode 3: Advanced Topics", 300.0, 1500.0),
    ]
    
    for url, title, position, duration in episodes:
        playback_memory.update_position(url, title, position, duration)
        logger.log_audio_event("position_saved", title, f"{position:.0f}s")
    
    # Mark one as completed
    playback_memory.mark_completed("http://example.com/ep2.mp3")
    
    # Show statistics
    stats = playback_memory.get_statistics()
    print(f"\n📊 Playback Statistics:")
    print(f"   Total episodes: {stats['total_episodes']}")
    print(f"   Completed: {stats['completed_episodes']}")
    print(f"   In progress: {stats['in_progress_episodes']}")
    print(f"   Total listening time: {stats['total_listening_hours']:.1f} hours")
    
    # Show recently played
    recent = playback_memory.get_recently_played(limit=3)
    print(f"\n🕒 Recently Played:")
    for i, episode in enumerate(recent, 1):
        print(f"   {i}. {episode.episode_title} ({episode.get_resume_time_formatted()})")
    
    # Show resume recommendations
    in_progress = playback_memory.get_in_progress()
    print(f"\n▶️  Resume Recommendations:")
    for episode in in_progress:
        print(f"   • {episode.episode_title} - Resume at {episode.get_resume_time_formatted()}")
    
    # 6. Demonstrate performance monitoring
    print("\n6. Demonstrating performance monitoring...")
    
    with PerformanceMonitor(logger, "file_processing"):
        # Simulate some work
        time.sleep(0.1)
    
    with PerformanceMonitor(logger, "network_request"):
        # Simulate network request
        time.sleep(0.05)
    
    # Log performance statistics
    logger.log_performance_stats()
    
    # 7. Demonstrate error handling
    print("\n7. Demonstrating error handling...")
    
    def simulate_audio_error():
        raise AudioError("Simulated codec error", "/fake/path/audio.mp3")
    
    # This will be handled gracefully
    try:
        simulate_audio_error()
    except Exception as e:
        error_handler.handle_error(
            e, 
            "example_simulation",
            show_to_user=False
        )
    
    # Show error statistics
    error_stats = error_handler.get_error_statistics()
    if error_stats:
        print(f"\n⚠️  Error Statistics:")
        for error_type, count in error_stats.items():
            print(f"   {error_type}: {count} occurrences")
    
    # 8. Export data for backup/analysis
    print("\n8. Exporting data...")
    
    # Export playback data
    playback_export = playback_memory.export_data()
    print(f"   Playback data exported to: {playback_export}")
    
    # Export logs
    log_export = logger.export_logs_to_json(hours_back=1)
    print(f"   Logs exported to: {log_export}")
    
    # 9. Cleanup
    print("\n9. Cleanup...")
    playback_memory.cleanup()
    logger.info("Example completed successfully")
    
    print("\n✅ Enhanced podcast player systems demonstrated successfully!")
    print("   Check the generated log files and exports for detailed information.")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)