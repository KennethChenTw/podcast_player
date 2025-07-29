"""
Error handling system for Podcast Player

Provides centralized error handling, user-friendly error messages,
and error recovery mechanisms.
"""

import traceback
import sys
from typing import Optional, Callable, Dict, Any, Type
from enum import Enum

# Handle tkinter import for headless environments
try:
    import tkinter.messagebox as messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    messagebox = None
    TKINTER_AVAILABLE = False


class ErrorSeverity(Enum):
    """Error severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PodcastError(Exception):
    """Base exception class for podcast player errors."""
    
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.ERROR, 
                 user_message: Optional[str] = None, recovery_action: Optional[str] = None):
        super().__init__(message)
        self.severity = severity
        self.user_message = user_message or message
        self.recovery_action = recovery_action


class NetworkError(PodcastError):
    """Network-related errors."""
    
    def __init__(self, message: str, url: Optional[str] = None):
        user_msg = f"網路連線問題：{message}"
        if url:
            user_msg += f"\nURL: {url}"
        super().__init__(message, ErrorSeverity.WARNING, user_msg, "請檢查網路連線並重試")


class AudioError(PodcastError):
    """Audio playback related errors."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        user_msg = f"音頻播放問題：{message}"
        if file_path:
            user_msg += f"\n檔案: {file_path}"
        super().__init__(message, ErrorSeverity.ERROR, user_msg, "請檢查音頻檔案格式或重新下載")


class ConfigError(PodcastError):
    """Configuration related errors."""
    
    def __init__(self, message: str, config_file: Optional[str] = None):
        user_msg = f"設定檔問題：{message}"
        if config_file:
            user_msg += f"\n檔案: {config_file}"
        super().__init__(message, ErrorSeverity.WARNING, user_msg, "將使用預設設定")


class RSSError(PodcastError):
    """RSS feed related errors."""
    
    def __init__(self, message: str, feed_url: Optional[str] = None):
        user_msg = f"RSS 訂閱源問題：{message}"
        if feed_url:
            user_msg += f"\nURL: {feed_url}"
        super().__init__(message, ErrorSeverity.WARNING, user_msg, "請檢查 RSS URL 或稍後重試")


class ErrorHandler:
    """Centralized error handler for the podcast player."""
    
    def __init__(self, logger=None, show_gui_errors: bool = True):
        """
        Initialize error handler.
        
        Args:
            logger: Logger instance for error logging
            show_gui_errors: Whether to show GUI error dialogs
        """
        self.logger = logger
        self.show_gui_errors = show_gui_errors
        self.error_counts: Dict[str, int] = {}
        self.recovery_handlers: Dict[Type[Exception], Callable] = {}
        
    def register_recovery_handler(self, error_type: Type[Exception], handler: Callable):
        """
        Register a recovery handler for specific error types.
        
        Args:
            error_type: Exception type to handle
            handler: Recovery function to call
        """
        self.recovery_handlers[error_type] = handler
    
    def handle_error(self, error: Exception, context: str = "", 
                    show_to_user: bool = True, attempt_recovery: bool = True) -> bool:
        """
        Handle an error with logging, user notification, and recovery.
        
        Args:
            error: The exception that occurred
            context: Context where the error occurred
            show_to_user: Whether to show error to user
            attempt_recovery: Whether to attempt automatic recovery
            
        Returns:
            bool: True if error was handled successfully, False otherwise
        """
        error_key = f"{type(error).__name__}:{str(error)}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # Log the error
        if self.logger:
            self.logger.error(f"Error in {context}: {error}", exc_info=True)
        else:
            print(f"Error in {context}: {error}")
            traceback.print_exc()
        
        # Show error to user if requested
        if show_to_user and self.show_gui_errors:
            self._show_error_to_user(error, context)
        
        # Attempt recovery if possible
        recovery_success = False
        if attempt_recovery:
            recovery_success = self._attempt_recovery(error, context)
        
        return recovery_success
    
    def _show_error_to_user(self, error: Exception, context: str):
        """Show error message to user via GUI dialog."""
        if not TKINTER_AVAILABLE or messagebox is None:
            # Fallback to console output if GUI is not available
            if isinstance(error, PodcastError):
                print(f"ERROR ({context}): {error.user_message}")
                if error.recovery_action:
                    print(f"建議：{error.recovery_action}")
            else:
                print(f"未預期的錯誤 ({context}): {str(error)}")
            return
        
        if isinstance(error, PodcastError):
            title = f"錯誤 - {context}" if context else "錯誤"
            message = error.user_message
            if error.recovery_action:
                message += f"\n\n建議：{error.recovery_action}"
            
            if error.severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(title, message)
            elif error.severity == ErrorSeverity.ERROR:
                messagebox.showerror(title, message)
            elif error.severity == ErrorSeverity.WARNING:
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
        else:
            # Generic error
            title = f"未預期的錯誤 - {context}" if context else "未預期的錯誤"
            message = f"發生了未預期的錯誤：\n{str(error)}\n\n請檢查日誌檔案或聯繫開發者。"
            messagebox.showerror(title, message)
    
    def _attempt_recovery(self, error: Exception, context: str) -> bool:
        """Attempt to recover from an error."""
        error_type = type(error)
        
        # Check for registered recovery handler
        if error_type in self.recovery_handlers:
            try:
                self.recovery_handlers[error_type](error, context)
                if self.logger:
                    self.logger.info(f"Successfully recovered from {error_type.__name__} in {context}")
                return True
            except Exception as recovery_error:
                if self.logger:
                    self.logger.error(f"Recovery failed for {error_type.__name__}: {recovery_error}")
                return False
        
        # Built-in recovery strategies
        if isinstance(error, NetworkError):
            return self._recover_network_error(error, context)
        elif isinstance(error, ConfigError):
            return self._recover_config_error(error, context)
        
        return False
    
    def _recover_network_error(self, error: NetworkError, context: str) -> bool:
        """Attempt to recover from network errors."""
        # For now, just log that recovery should be attempted
        if self.logger:
            self.logger.info(f"Network error recovery needed for: {context}")
        return False
    
    def _recover_config_error(self, error: ConfigError, context: str) -> bool:
        """Attempt to recover from configuration errors."""
        # For now, just log that default config should be used
        if self.logger:
            self.logger.info(f"Using default configuration due to error in {context}")
        return False
    
    def get_error_statistics(self) -> Dict[str, int]:
        """Get error occurrence statistics."""
        return self.error_counts.copy()
    
    def clear_error_statistics(self):
        """Clear error statistics."""
        self.error_counts.clear()


def safe_execute(func: Callable, error_handler: ErrorHandler, 
                context: str = "", *args, **kwargs) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        error_handler: Error handler instance
        context: Context description for error reporting
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, context or func.__name__)
        return None


# Global error handler instance (optional, for convenience)
_global_error_handler: Optional[ErrorHandler] = None


def get_global_error_handler() -> ErrorHandler:
    """Get or create global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_global_error_handler(handler: ErrorHandler):
    """Set global error handler instance."""
    global _global_error_handler
    _global_error_handler = handler