"""
Logging system for Podcast Player

Provides structured logging with rotation, filtering, and performance monitoring.
"""

import logging
import logging.handlers
import os
import time
import threading
import sys
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from pathlib import Path
import json


class PodcastLogger:
    """Enhanced logger for the podcast player application."""
    
    def __init__(self, name: str = "PodcastPlayer", log_dir: Optional[str] = None,
                 level: int = logging.INFO, max_file_size: int = 10*1024*1024,
                 backup_count: int = 5, console_output: bool = True):
        """
        Initialize the logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files (defaults to logs/ in script directory)
            level: Logging level
            max_file_size: Maximum log file size in bytes
            backup_count: Number of backup files to keep
            console_output: Whether to output to console
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Set up log directory
        if log_dir is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            log_dir = os.path.join(script_dir, "logs")
        
        self.log_dir = Path(log_dir) if log_dir else Path(os.path.join(script_dir, "logs"))
        self.log_dir.mkdir(exist_ok=True)
        
        # Performance tracking
        self.performance_data: Dict[str, list] = {}
        self.start_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # Set up handlers
        self._setup_file_handler(max_file_size, backup_count)
        if console_output:
            self._setup_console_handler()
        
        # Set up error log
        self._setup_error_handler()
        
        self.logger.info(f"Logger initialized: {name}")
    
    def _setup_file_handler(self, max_file_size: int, backup_count: int):
        """Set up rotating file handler for general logs."""
        log_file = self.log_dir / f"{self.name.lower()}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_file_size, backupCount=backup_count,
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """Set up console handler for immediate feedback."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_error_handler(self):
        """Set up separate handler for errors only."""
        error_file = self.log_dir / f"{self.name.lower()}_errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file, maxBytes=5*1024*1024, backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s\n'
            'MESSAGE: %(message)s\n'
            '%(exc_info)s\n' + '-'*80 + '\n',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, exc_info=True, **kwargs):
        """Log error message with exception info."""
        self.logger.error(message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info=True, **kwargs):
        """Log critical message with exception info."""
        self.logger.critical(message, exc_info=exc_info, **kwargs)
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        with self._lock:
            self.start_times[operation] = time.time()
        self.debug(f"Started timing: {operation}")
    
    def end_timer(self, operation: str, log_result: bool = True) -> float:
        """
        End timing an operation and return duration.
        
        Args:
            operation: Operation name
            log_result: Whether to log the timing result
            
        Returns:
            Duration in seconds
        """
        end_time = time.time()
        
        with self._lock:
            start_time = self.start_times.pop(operation, end_time)
            duration = end_time - start_time
            
            # Store performance data
            if operation not in self.performance_data:
                self.performance_data[operation] = []
            self.performance_data[operation].append(duration)
        
        if log_result:
            self.info(f"Operation '{operation}' completed in {duration:.3f}s")
        
        return duration
    
    def log_performance_stats(self):
        """Log performance statistics for all tracked operations."""
        with self._lock:
            if not self.performance_data:
                self.info("No performance data available")
                return
            
            self.info("=== Performance Statistics ===")
            for operation, times in self.performance_data.items():
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    self.info(f"{operation}: avg={avg_time:.3f}s, min={min_time:.3f}s, "
                             f"max={max_time:.3f}s, count={len(times)}")
    
    def clear_performance_data(self):
        """Clear stored performance data."""
        with self._lock:
            self.performance_data.clear()
            self.start_times.clear()
        self.info("Performance data cleared")
    
    def log_system_info(self):
        """Log system information for debugging."""
        import platform
        
        self.info("=== System Information ===")
        self.info(f"Python version: {platform.python_version()}")
        self.info(f"Platform: {platform.platform()}")
        
        try:
            import psutil
            self.info(f"CPU count: {psutil.cpu_count()}")
            self.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        except ImportError:
            self.info("System stats unavailable (psutil not installed)")
        
        try:
            import pygame
            self.info(f"Pygame version: {pygame.version.ver}")
        except ImportError:
            self.info("Pygame not available")
        
        try:
            import feedparser
            self.info(f"Feedparser version: {feedparser.__version__}")
        except ImportError:
            self.info("Feedparser not available")
        
        try:
            import requests
            self.info(f"Requests version: {requests.__version__}")
        except ImportError:
            self.info("Requests not available")
    
    def log_network_request(self, method: str, url: str, status_code: Optional[int] = None,
                           duration: Optional[float] = None, error: Optional[str] = None):
        """Log network request details."""
        message = f"HTTP {method} {url}"
        if status_code:
            message += f" -> {status_code}"
        if duration:
            message += f" ({duration:.3f}s)"
        if error:
            message += f" ERROR: {error}"
            self.error(message)
        else:
            self.info(message)
    
    def log_audio_event(self, event: str, track_title: str = "", details: str = ""):
        """Log audio-related events."""
        message = f"Audio {event}"
        if track_title:
            message += f": {track_title}"
        if details:
            message += f" ({details})"
        self.info(message)
    
    def log_action(self, action: str, details: str = ""):
        """Log user actions or general application actions."""
        message = f"Action: {action}"
        if details:
            message += f" - {details}"
        self.info(message)
    
    def export_logs_to_json(self, output_file: Optional[str] = None,
                           hours_back: int = 24) -> str:
        """
        Export recent logs to JSON format.
        
        Args:
            output_file: Output file path (auto-generated if None)
            hours_back: Number of hours of logs to export
            
        Returns:
            Path to exported file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_path = self.log_dir / f"logs_export_{timestamp}.json"
        else:
            output_file_path = Path(output_file)
        
        # Read log files and extract recent entries
        log_entries = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        log_file_path = self.log_dir / f"{self.name.lower()}.log"
        if log_file_path.exists():
            try:
                with open(str(log_file_path), 'r', encoding='utf-8') as f: # Convert Path to str
                    for line in f:
                        try:
                            # Parse timestamp from log line
                            timestamp_str = line.split(' - ')[0]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            
                            if timestamp >= cutoff_time:
                                log_entries.append({
                                    'timestamp': timestamp_str,
                                    'message': line.strip()
                                })
                        except (ValueError, IndexError):
                            # Skip malformed lines
                            continue
            except Exception as e:
                self.error(f"Failed to read log file: {e}")
        
        # Export to JSON
        export_data = {
            'export_time': datetime.now().isoformat(),
            'hours_back': hours_back,
            'total_entries': len(log_entries),
            'logs': log_entries,
            'performance_data': self.performance_data
        }
        
        try:
            with open(str(output_file_path), 'w', encoding='utf-8') as f: # Convert Path to str
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.info(f"Logs exported to: {output_file_path}")
            return str(output_file_path)
        except Exception as e:
            self.error(f"Failed to export logs: {e}")
            raise


class PerformanceMonitor:
    """Context manager for performance monitoring."""
    
    def __init__(self, logger: PodcastLogger, operation: str):
        self.logger = logger
        self.operation = operation
    
    def __enter__(self):
        self.logger.start_timer(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.end_timer(self.operation)


# Global logger instance
_global_logger: Optional[PodcastLogger] = None


def get_logger(name: str = "PodcastPlayer") -> PodcastLogger:
    """Get or create logger instance."""
    global _global_logger
    if _global_logger is None or _global_logger.name != name:
        _global_logger = PodcastLogger(name)
    return _global_logger


def setup_logging(log_dir: Optional[str] = None, level: int = logging.INFO,
                 console_output: bool = True) -> PodcastLogger:
    """Set up application logging."""
    logger = PodcastLogger(
        name="PodcastPlayer",
        log_dir=log_dir,
        level=level,
        console_output=console_output
    )
    
    # Log system info on startup
    logger.log_system_info()
    
    global _global_logger
    _global_logger = logger
    return logger
