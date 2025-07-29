# RSSProcessor Integration Guide

This guide shows how to integrate the new `RSSProcessor` class into the existing `podcast_player.py` file.

## Overview

The `RSSProcessor` class has been extracted from the original RSS processing code in `podcast_player.py` and modularized for better maintainability and reusability.

## Key Features

- **Clean API**: Simple methods for both synchronous and asynchronous RSS fetching
- **Error Handling**: Comprehensive error handling for network and parsing issues
- **Threading Support**: Non-blocking operations with callback support
- **Data Models**: Uses the existing `Episode` and `PodcastData` models
- **URL Validation**: Built-in RSS URL validation

## Integration Steps

### 1. Import the RSSProcessor

Add this import to the top of `podcast_player.py`:

```python
from src.podcast_player.core.rss_processor import RSSProcessor
```

### 2. Initialize in PodcastPlayer.__init__()

Add this line in the `__init__` method:

```python
# Initialize RSS processor
self.rss_processor = RSSProcessor()
```

### 3. Replace the existing fetch_podcast_thread method

Replace the current `fetch_podcast_thread` method with:

```python
def fetch_podcast_thread(self):
    if self.rss_processor.is_busy:
        return
        
    rss_url = self.rss_url_entry.get().strip()
    if not rss_url:
        messagebox.showwarning("警告", "請輸入 RSS Feed URL")
        return
    
    # Update UI to show loading state
    self.fetch_button.config(state=tk.DISABLED)
    self.podcast_title_label.config(text=f"正在讀取: {rss_url}...")
    self.save_station_button.config(state=tk.DISABLED)
    self.delete_station_button.config(state=tk.DISABLED)
    
    # Define callbacks
    def on_success(podcast_data):
        # Convert PodcastData to the expected format
        self.podcast_data = {
            'title': podcast_data.title,
            'feed_url': podcast_data.feed_url,
            'episodes': [episode.to_dict() for episode in podcast_data.episodes]
        }
        self.root.after(0, self.update_podcast_gui)
    
    def on_error(error_message):
        self.root.after(0, lambda: self.podcast_title_label.config(text="讀取失敗"))
        self.root.after(0, lambda: messagebox.showerror("錯誤", error_message))
    
    def on_complete():
        try:
            if self.root.winfo_exists():
                self.root.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))
                self.root.after(0, self.update_station_buttons_state)
        except RuntimeError:
            print("背景執行緒嘗試更新已關閉的視窗，已安全忽略。")
    
    # Start the fetch operation
    self.rss_processor.fetch_podcast_thread(
        rss_url=rss_url,
        on_success=on_success,
        on_error=on_error,
        on_complete=on_complete
    )
```

### 4. Remove the old fetch_podcast method

The old `fetch_podcast` method can be removed as its functionality is now handled by the `RSSProcessor`.

### 5. Update loading state checks

Replace checks for `self.is_loading` with `self.rss_processor.is_busy` where appropriate.

## Benefits of the New Design

### 1. **Separation of Concerns**
- RSS processing logic is separated from UI logic
- Easier to test and maintain
- Can be reused in other parts of the application

### 2. **Better Error Handling**
- Centralized error handling in the RSS processor
- More detailed error messages
- Proper network error handling

### 3. **Cleaner Code**
- Removes ~30 lines of RSS processing code from the main class
- More readable and maintainable
- Better type hints and documentation

### 4. **Enhanced Functionality**
- URL validation before fetching
- Better audio URL extraction logic
- Support for more RSS formats

## Usage Examples

### Synchronous Usage
```python
processor = RSSProcessor()
try:
    podcast_data = processor.fetch_podcast("https://example.com/feed.xml")
    print(f"Found {podcast_data.get_episode_count()} episodes")
except Exception as e:
    print(f"Error: {e}")
```

### Asynchronous Usage with Callbacks
```python
processor = RSSProcessor()

def on_success(podcast_data):
    print(f"Loaded: {podcast_data.title}")

def on_error(error):
    print(f"Failed: {error}")

processor.fetch_podcast_thread(
    rss_url="https://example.com/feed.xml",
    on_success=on_success,
    on_error=on_error
)
```

### URL Validation
```python
processor = RSSProcessor()
if processor.is_valid_rss_url(url):
    # Proceed with fetch
    pass
```

## Testing

Run the example script to test the RSSProcessor:

```bash
python example_rss_usage.py
```

This will demonstrate both synchronous and asynchronous usage patterns.

## Notes

- The `RSSProcessor` maintains the same functionality as the original code
- All error handling and network timeouts are preserved
- The class is thread-safe for the intended usage patterns
- The original data format is maintained for backward compatibility