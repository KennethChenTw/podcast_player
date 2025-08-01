"""
Main Window for Podcast Player Application

This module provides the main application window and coordinates
all UI components and layout.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any

from .components import PodcastPlayerUI
from .event_handlers import EventHandlers
from .theme_manager import ThemeManager


class MainWindow:
    """
    Main application window that coordinates all UI components.
    
    This class manages the main window layout, menu bar, status bar,
    and coordinates between different UI components.
    """
    
    def __init__(self, root: tk.Tk, app_components: Dict[str, Any]):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
            app_components: Dictionary of application components
        """
        self.root = root
        self.app_components = app_components
        
        # Set up window properties
        self.setup_window()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager(app_components.get('config_manager'))
        
        # Create UI components first
        self.ui = PodcastPlayerUI(self.root)
        
        # Set up event handlers and pass them to UI
        self.event_handlers = EventHandlers(
            app_components.get('audio_player'),
            app_components.get('rss_processor'),
            app_components.get('station_manager'),
            app_components.get('playlist_manager'),
            app_components.get('config_manager'),
            self.ui
        )
        
        # Now set up callbacks after event handlers are created
        self.ui.setup_callbacks(self.event_handlers)
        
        # Set up menu and status bar
        self.setup_menu_bar()
        self.setup_status_bar()
        
        # Configure layout
        self.setup_layout()
        
        # Apply initial theme
        self.theme_manager.apply_theme_to_application(self.root, {})
        
        # Set up keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_window(self) -> None:
        """Set up basic window properties."""
        self.root.title("Podcast 播放器")
        self.root.minsize(800, 600)
        
        # Load and apply saved window state
        config_manager = self.app_components.get('config_manager')
        if config_manager:
            window_state = config_manager.get_window_state()
            
            # Apply window size and position
            if window_state['maximized']:
                self.root.state('zoomed')
            else:
                # Set size
                width = window_state['width']
                height = window_state['height']
                
                # Set position if available
                if window_state['x'] is not None and window_state['y'] is not None:
                    geometry = f"{width}x{height}+{window_state['x']}+{window_state['y']}"
                else:
                    # Center on screen if no position saved
                    screen_width = self.root.winfo_screenwidth()
                    screen_height = self.root.winfo_screenheight()
                    x = (screen_width - width) // 2
                    y = (screen_height - height) // 2
                    geometry = f"{width}x{height}+{x}+{y}"
                
                self.root.geometry(geometry)
        
        # Bind window state change events
        self.root.bind('<Configure>', self.on_window_configure)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set window icon if available
        try:
            # self.root.iconbitmap("icon.ico")  # Uncomment when icon is available
            pass
        except tk.TclError:
            pass  # Icon file not found, continue without icon
    
    def setup_menu_bar(self) -> None:
        """Create and configure the menu bar."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="匯入電台", command=self.import_stations)
        file_menu.add_command(label="匯出電台", command=self.export_stations)
        file_menu.add_separator()
        file_menu.add_command(label="匯入播放清單", command=self.import_playlist)
        file_menu.add_command(label="匯出播放清單", command=self.export_playlist)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="編輯", menu=edit_menu)
        edit_menu.add_command(label="偏好設定", command=self.show_preferences)
        edit_menu.add_command(label="清除歷史", command=self.clear_history)
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="檢視", menu=view_menu)
        view_menu.add_command(label="重新整理", command=self.refresh_view)
        view_menu.add_command(label="全螢幕", command=self.toggle_fullscreen)
        view_menu.add_separator()
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="主題", menu=theme_menu)
        
        self.theme_var = tk.StringVar(value=self.theme_manager.get_current_theme())
        for theme_id, theme_name in self.theme_manager.get_available_themes().items():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.theme_var,
                value=theme_id,
                command=lambda t=theme_id: self.change_theme(t)
            )
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="快捷鍵", command=self.show_shortcuts)
        help_menu.add_command(label="關於", command=self.show_about)
    
    def setup_status_bar(self) -> None:
        """Create and configure the status bar."""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        self.status_label = ttk.Label(
            self.status_frame,
            text="就緒",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode='indeterminate'
        )
        
        # Connection status indicator
        self.connection_status = ttk.Label(
            self.status_frame,
            text="離線",
            relief=tk.SUNKEN,
            width=10
        )
        self.connection_status.pack(side=tk.RIGHT)
    
    def setup_layout(self) -> None:
        """Configure the main window layout."""
        # Main content area
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # The UI components are already packed by PodcastPlayerUI
        # This method can be extended for additional layout configuration
    
    def setup_keyboard_shortcuts(self) -> None:
        """Set up keyboard shortcuts for the application."""
        # Focus on the root window to capture all key events
        self.root.focus_set()
        
        # Specific key bindings (with focus check)
        self.root.bind('<space>', lambda e: self.handle_shortcut(e, self.toggle_play))
        self.root.bind('<Return>', lambda e: self.handle_shortcut(e, self.toggle_play))
        self.root.bind('<Escape>', lambda e: self.handle_shortcut(e, self.stop_playback))
        
        # Volume control
        self.root.bind('<Up>', lambda e: self.handle_shortcut(e, lambda: self.adjust_volume(0.1)))
        self.root.bind('<Down>', lambda e: self.handle_shortcut(e, lambda: self.adjust_volume(-0.1)))
        
        # Track navigation
        self.root.bind('<Left>', lambda e: self.handle_shortcut(e, self.previous_track))
        self.root.bind('<Right>', lambda e: self.handle_shortcut(e, self.next_track))
        
        # Speed control
        self.root.bind('<plus>', lambda e: self.handle_shortcut(e, self.cycle_speed))
        self.root.bind('<minus>', lambda e: self.handle_shortcut(e, self.cycle_speed))
        
        # Search focus (always work)
        self.root.bind('<Control-f>', lambda e: self.focus_search())
        
        # Refresh
        self.root.bind('<F5>', lambda e: self.refresh_view())
        
        # Full screen
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # Theme toggle
        self.root.bind('<Control-t>', lambda e: self.toggle_theme())
    
    def update_status(self, message: str, show_progress: bool = False) -> None:
        """
        Update the status bar message.
        
        Args:
            message: Status message to display
            show_progress: Whether to show progress indicator
        """
        self.status_label.config(text=message)
        
        if show_progress:
            self.progress_bar.pack(side=tk.RIGHT, padx=(5, 10))
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    def update_connection_status(self, connected: bool) -> None:
        """
        Update the connection status indicator.
        
        Args:
            connected: Whether the application is connected
        """
        if connected:
            self.connection_status.config(text="線上", foreground="green")
        else:
            self.connection_status.config(text="離線", foreground="red")
    
    def import_stations(self) -> None:
        """Handle station import."""
        if hasattr(self.event_handlers, 'handle_import_stations'):
            self.event_handlers.handle_import_stations()

    def export_stations(self) -> None:
        """Handle station export."""
        if hasattr(self.event_handlers, 'handle_export_stations'):
            self.event_handlers.handle_export_stations()

    def import_playlist(self) -> None:
        """Handle playlist import."""
        # Delegate to event handlers
        if hasattr(self.event_handlers, 'handle_import_playlist'):
            self.event_handlers.handle_import_playlist()
    
    def export_playlist(self) -> None:
        """Handle playlist export."""
        # Delegate to event handlers
        if hasattr(self.event_handlers, 'handle_export_playlist'):
            self.event_handlers.handle_export_playlist()
    
    def show_preferences(self) -> None:
        """Show preferences dialog."""
        pref_window = tk.Toplevel(self.root)
        pref_window.title("偏好設定")
        pref_window.transient(self.root)
        pref_window.grab_set()
        
        config_manager = self.app_components.get('config_manager')
        
        main_frame = ttk.Frame(pref_window, padding="10")
        main_frame.pack(expand=True, fill="both")

        # --- Episode Loading Settings ---
        load_frame = ttk.LabelFrame(main_frame, text="單集載入設定", padding="10")
        load_frame.pack(fill="x", expand=True, pady=5)

        # Ensure config_manager is not None before calling its methods
        load_mode_val = config_manager.get_setting('episode_load_mode', 'all') if config_manager else 'all'
        latest_count_val = str(config_manager.get_setting('latest_episode_count', 10)) if config_manager else '10'

        load_mode = tk.StringVar(value=load_mode_val)
        latest_count = tk.StringVar(value=latest_count_val)

        def update_entry_state():
            # Ensure count_entry is a valid Entry widget
            if isinstance(count_entry, tk.Entry):
                if load_mode.get() == 'latest':
                    count_entry.config(state='normal')
                else:
                    count_entry.config(state='disabled')

        ttk.Radiobutton(load_frame, text="載入所有單集", variable=load_mode, value='all', command=update_entry_state).pack(anchor='w')
        
        latest_frame = ttk.Frame(load_frame)
        latest_frame.pack(fill='x', expand=True)
        
        ttk.Radiobutton(latest_frame, text="只載入最新的", variable=load_mode, value='latest', command=update_entry_state).pack(side='left')
        
        count_entry = ttk.Entry(latest_frame, textvariable=latest_count, width=5)
        count_entry.pack(side='left', padx=5)
        
        ttk.Label(latest_frame, text="集").pack(side='left')

        update_entry_state()

        # --- Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10, side="bottom")

        def save_settings():
            try:
                count = int(latest_count.get())
                if count <= 0:
                    raise ValueError("數量必須是正整數")
                
                # Ensure config_manager is not None before calling its methods
                if config_manager:
                    config_manager.set_setting('episode_load_mode', load_mode.get())
                    config_manager.set_setting('latest_episode_count', count)
                
                self.update_status("偏好設定已儲存")
                pref_window.destroy()
            except ValueError as e:
                from tkinter import messagebox
                messagebox.showerror("輸入錯誤", str(e), parent=pref_window)

        ttk.Button(button_frame, text="儲存", command=save_settings).pack(side="right", padx=5)
        ttk.Button(button_frame, text="取消", command=pref_window.destroy).pack(side="right")
    
    def clear_history(self) -> None:
        """Clear playback history."""
        # Delegate to playlist manager
        playlist_manager = self.app_components.get('playlist_manager')
        if playlist_manager and hasattr(playlist_manager, 'clear_history'):
            playlist_manager.clear_history()
            self.update_status("歷史記錄已清除")
    
    def refresh_view(self) -> None:
        """Refresh the current view."""
        # Delegate to event handlers
        if hasattr(self.event_handlers, 'handle_refresh'):
            self.event_handlers.handle_refresh()
        else:
            self.update_status("重新整理功能無法使用")
    
    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
    
    def change_theme(self, theme_id: str) -> None:
        """
        Change application theme.
        
        Args:
            theme_id: Theme ID to switch to
        """
        try:
            if self.theme_manager.set_theme(theme_id):
                # Apply theme to entire application
                self.theme_manager.apply_theme_to_application(self.root, {})
                
                # Update theme variable
                self.theme_var.set(theme_id)
                
                # Update status
                theme_name = self.theme_manager.get_available_themes().get(theme_id, theme_id)
                self.update_status(f"已切換至 {theme_name}")
            else:
                self.update_status("主題切換失敗")
                
        except Exception as e:
            print(f"Error changing theme: {e}")
            self.update_status("主題切換時發生錯誤")
    
    def handle_shortcut(self, event, callback) -> None:
        """
        Handle keyboard shortcuts with focus checking.
        
        Args:
            event: Key press event
            callback: Function to call if shortcut should be executed
        """
        # Check if focus is on a text input widget
        focused_widget = self.root.focus_get()
        
        # Skip shortcut if typing in Entry, Text, or Combobox
        if focused_widget and isinstance(focused_widget, (tk.Entry, tk.Text, ttk.Combobox)):
            return
        
        # Execute the callback
        try:
            callback()
        except Exception as e:
            print(f"Error executing shortcut: {e}")
    
    def handle_key_press(self, event) -> None:
        """
        Handle general key press events.
        
        Args:
            event: Key press event
        """
        # Only handle if focus is on the main window, not on text inputs
        focused_widget = self.root.focus_get()
        if focused_widget and isinstance(focused_widget, (tk.Entry, tk.Text, ttk.Combobox)):
            return
        
        # Log key press for debugging
        print(f"Key pressed: {event.keysym}")
    
    def toggle_play(self) -> None:
        """Toggle play/pause via keyboard shortcut."""
        try:
            if hasattr(self.event_handlers, 'handle_toggle_play'):
                self.event_handlers.handle_toggle_play()
        except Exception as e:
            print(f"Error toggling play: {e}")
    
    def stop_playback(self) -> None:
        """Stop playback via keyboard shortcut."""
        try:
            if hasattr(self.event_handlers, 'handle_stop'):
                self.event_handlers.handle_stop()
        except Exception as e:
            print(f"Error stopping playback: {e}")
    
    def adjust_volume(self, delta: float) -> None:
        """
        Adjust volume via keyboard shortcut.
        
        Args:
            delta: Volume change amount
        """
        try:
            # Get current volume
            volume_var = self.ui.get_widget('volume_var')
            if volume_var:
                current_volume = volume_var.get()
                new_volume = max(0.0, min(1.0, current_volume + delta))
                volume_var.set(new_volume)
                
                # Trigger volume change
                if hasattr(self.event_handlers, 'handle_volume_changed'):
                    self.event_handlers.handle_volume_changed(str(new_volume)) # Convert to str
                
                self.update_status(f"音量: {int(new_volume * 100)}%")
        except Exception as e:
            print(f"Error adjusting volume: {e}")
    
    def previous_track(self) -> None:
        """Go to previous track via keyboard shortcut."""
        try:
            if hasattr(self.event_handlers, 'handle_previous_track'):
                self.event_handlers.handle_previous_track()
        except Exception as e:
            print(f"Error going to previous track: {e}")
    
    def next_track(self) -> None:
        """Go to next track via keyboard shortcut."""
        try:
            if hasattr(self.event_handlers, 'handle_next_track'):
                self.event_handlers.handle_next_track()
        except Exception as e:
            print(f"Error going to next track: {e}")
    
    def cycle_speed(self) -> None:
        """Cycle playback speed via keyboard shortcut."""
        try:
            if hasattr(self.event_handlers, 'handle_cycle_speed'):
                self.event_handlers.handle_cycle_speed()
        except Exception as e:
            print(f"Error cycling speed: {e}")
    
    def focus_search(self) -> None:
        """Focus on search entry via keyboard shortcut."""
        try:
            search_entry = self.ui.get_widget('search_entry')
            if search_entry:
                # Ensure search_entry is a valid Entry widget
                if isinstance(search_entry, tk.Entry):
                    search_entry.focus_set()
                    search_entry.select_range(0, tk.END)
                self.update_status("搜尋模式")
        except Exception as e:
            print(f"Error focusing search: {e}")
    
    def toggle_theme(self) -> None:
        """Toggle between light and dark theme."""
        try:
            new_theme = self.theme_manager.toggle_theme()
            self.theme_manager.apply_theme_to_application(self.root, {})
            self.theme_var.set(new_theme)
            
            theme_name = self.theme_manager.get_available_themes().get(new_theme, new_theme)
            self.update_status(f"已切換至 {theme_name}")
            
        except Exception as e:
            print(f"Error toggling theme: {e}")
            self.update_status("主題切換時發生錯誤")
    
    def show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        from tkinter import messagebox
        shortcuts_text = """
鍵盤快捷鍵：

播放控制：
• 空格鍵 / Enter - 播放/暫停
• Esc - 停止播放
• ← / → - 上一首/下一首
• ↑ / ↓ - 增加/減少音量
• + / - - 切換播放速度

導航：
• Ctrl+F - 聚焦搜尋框
• F5 - 重新整理
• F11 - 全螢幕切換

外觀：
• Ctrl+T - 切換深色/淺色主題

使用提示：
• 在文字輸入框中時，這些快捷鍵不會生效
• 點擊主視窗來確保焦點正確
        """
        
        messagebox.showinfo("快捷鍵說明", shortcuts_text)
    
    def show_about(self) -> None:
        """Show about dialog."""
        from tkinter import messagebox
        messagebox.showinfo(
            "關於 Podcast 播放器",
            "Podcast 播放器 v1.0.0\\n\\n"
            "一個現代化的播客播放器，支援 RSS 訂閱源。\\n\\n"
            "功能特色：\\n"
            "• RSS 訂閱源支援\\n"
            "• 播放位置記憶\\n"
            "• 播放清單管理\\n"
            "• 音效控制\\n\\n"
            "© 2024 Podcast Player Team"
        )
    
    def on_window_configure(self, event) -> None:
        """
        Handle window configuration changes (resize, move).
        
        Args:
            event: Configure event
        """
        # Only handle main window events, not child widgets
        if event.widget != self.root:
            return
        
        # Save window state periodically (throttle to avoid excessive saving)
        if not hasattr(self, '_last_save_time'):
            self._last_save_time = 0
        
        import time
        current_time = time.time()
        if current_time - self._last_save_time > 2.0:  # Save at most every 2 seconds
            self.save_window_state()
            self._last_save_time = current_time
    
    def save_window_state(self) -> None:
        """Save current window state to configuration."""
        config_manager = self.app_components.get('config_manager')
        if not config_manager:
            return
        
        try:
            # Get current geometry
            geometry = self.root.geometry()
            is_maximized = self.root.state() == 'zoomed'
            
            # Parse geometry
            window_width, window_height, window_x, window_y = None, None, None, None
            try:
                if '+' in geometry:
                    size_part, pos_part = geometry.split('+', 1)
                    window_width, window_height = map(int, size_part.split('x'))
                    
                    # Handle negative positions
                    pos_parts = pos_part.replace('-', '+-').split('+')
                    pos_parts = [p for p in pos_parts if p]  # Remove empty strings
                    
                    if len(pos_parts) >= 2:
                        window_x = int(pos_parts[0])
                        window_y = int(pos_parts[1])
                    elif len(pos_parts) == 1:
                        window_x = int(pos_parts[0])
                        window_y = 0
                else:
                    window_width, window_height = map(int, geometry.split('x'))
            except (ValueError, IndexError) as e:
                print(f"Error parsing geometry '{geometry}': {e}")
            
            # Update settings
            if window_width and window_height:
                config_manager.update_setting('window_width', window_width)
                config_manager.update_setting('window_height', window_height)
            if window_x is not None:
                config_manager.update_setting('window_x', window_x)
            if window_y is not None:
                config_manager.update_setting('window_y', window_y)
            config_manager.update_setting('window_maximized', is_maximized)
            config_manager.update_setting('geometry', geometry)
            
        except Exception as e:
            print(f"Error saving window state: {e}")
    
    def on_closing(self) -> None:
        """Handle window closing."""
        # Save final window state
        self.save_window_state()
        
        # Save any PanedWindow positions
        self.save_ui_layout_state()
        
        # Delegate to main application
        if 'on_closing' in self.app_components:
            self.app_components['on_closing']()
        else:
            self.root.destroy()
    
    def save_ui_layout_state(self) -> None:
        """Save UI layout state like PanedWindow positions and column widths."""
        config_manager = self.app_components.get('config_manager')
        if not config_manager:
            return
        
        try:
            # Save PanedWindow positions (if any exist in the UI)
            # This would need to be implemented based on actual UI components
            ui_widgets = self.ui.get_all_widgets() if hasattr(self.ui, 'get_all_widgets') else {}
            
            for widget_name, widget in ui_widgets.items():
                if isinstance(widget, tk.PanedWindow):
                    # Save sash positions
                    for i in range(widget.panes().__len__() - 1):
                        try:
                            position = widget.sash_coord(i)[0]  # Get x coordinate
                            config_manager.save_paned_window_position(f"{widget_name}_sash_{i}", position)
                        except tk.TclError:
                            pass  # Sash might not exist yet
                
                elif hasattr(widget, 'heading'):  # Treeview-like widget
                    try:
                        # Save column widths
                        columns = widget['columns'] if widget['columns'] else ['#0']
                        for col in columns:
                            width = widget.column(col, 'width')
                            if width:
                                config_manager.save_column_width(widget_name, col, width)
                    except (tk.TclError, KeyError):
                        pass
        
        except Exception as e:
            print(f"Error saving UI layout state: {e}")
    
    def get_ui_component(self) -> PodcastPlayerUI:
        """
        Get the UI component instance.
        
        Returns:
            PodcastPlayerUI instance
        """
        return self.ui
    
    def get_event_handlers(self) -> EventHandlers:
        """
        Get the event handlers instance.
        
        Returns:
            EventHandlers instance
        """
        return self.event_handlers
