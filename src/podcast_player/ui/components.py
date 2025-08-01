"""
UI Components for Podcast Player

Contains the main UI components and widget creation logic.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional, Dict, Any


class PodcastPlayerUI:
    """Main UI components for the podcast player."""
    
    def __init__(self, root: tk.Tk):
        """
        Initialize UI components.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.widgets = {}
        self.callbacks = {}
        
        # Style configuration  
        self.setup_styles()
        
        # Create main layout
        self.create_main_layout()
    
    def setup_styles(self) -> None:
        """Configure UI styles."""
        style = ttk.Style()
        
        # Configure button styles
        style.configure("Play.TButton", font=("Arial", 12, "bold"))
        style.configure("Control.TButton", font=("Arial", 10))
        
        # Configure label styles
        style.configure("Title.TLabel", font=("Arial", 14, "bold"))
        style.configure("Info.TLabel", font=("Arial", 10))
    
    def create_main_layout(self) -> None:
        """Create the main UI layout."""
        # Create main menu
        self.create_menu_bar()
        
        # Create main frames
        self.create_frames()
        
        # Create controls
        self.create_controls()
        
        # Create RSS input section
        self.create_rss_section()
        
        # Create episode list
        self.create_episode_list()
        
        # Create playlist section
        self.create_playlist_section()
        
        # Create status bar
        self.create_status_bar()
    
    def create_menu_bar(self) -> None:
        """Create the main menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="檔案", menu=file_menu)
        file_menu.add_command(label="匯入電台列表")
        file_menu.add_command(label="匯出電台列表")
        file_menu.add_separator()
        file_menu.add_command(label="匯入播放清單")
        file_menu.add_command(label="匯出播放清單")
        file_menu.add_separator()
        file_menu.add_command(label="結束", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編輯", menu=edit_menu)
        edit_menu.add_command(label="清除播放紀錄")
        edit_menu.add_command(label="清除所有電台")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="說明", menu=help_menu)
        help_menu.add_command(label="關於", command=self._show_about)
        
        self.widgets['file_menu'] = file_menu
        self.widgets['edit_menu'] = edit_menu
        
        self.widgets['menubar'] = menubar
    
    def create_frames(self) -> None:
        """Create main frames for layout."""
        # Top frame for controls and RSS input
        self.widgets['top_frame'] = tk.Frame(self.root, bg='#f0f0f0')
        self.widgets['top_frame'].pack(fill=tk.X, padx=5, pady=5)
        
        # Middle frame for episode list and playlist
        self.widgets['middle_frame'] = tk.Frame(self.root)
        self.widgets['middle_frame'].pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bottom frame for status
        self.widgets['bottom_frame'] = tk.Frame(self.root, height=30, bg='#e0e0e0')
        self.widgets['bottom_frame'].pack(fill=tk.X, side=tk.BOTTOM)
    
    def create_controls(self) -> None:
        """Create playback control buttons."""
        controls_frame = tk.Frame(self.widgets['top_frame'], bg='#f0f0f0')
        controls_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Playback controls
        self.widgets['prev_button'] = ttk.Button(
            controls_frame, 
            text="◀◀", 
            style="Control.TButton"
        )
        self.widgets['prev_button'].pack(side=tk.LEFT, padx=2)
        
        self.widgets['play_button'] = ttk.Button(
            controls_frame, 
            text="播放", 
            style="Play.TButton"
        )
        self.widgets['play_button'].pack(side=tk.LEFT, padx=2)
        
        self.widgets['stop_button'] = ttk.Button(
            controls_frame, 
            text="停止", 
            style="Control.TButton"
        )
        self.widgets['stop_button'].pack(side=tk.LEFT, padx=2)
        
        self.widgets['next_button'] = ttk.Button(
            controls_frame, 
            text="▶▶", 
            style="Control.TButton"
        )
        self.widgets['next_button'].pack(side=tk.LEFT, padx=2)
        
        # Volume control
        volume_frame = tk.Frame(controls_frame, bg='#f0f0f0')
        volume_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(volume_frame, text="音量:", bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.widgets['volume_var'] = tk.DoubleVar(value=0.7)
        self.widgets['volume_scale'] = tk.Scale(
            volume_frame,
            from_=0, to=1, resolution=0.1,
            orient=tk.HORIZONTAL,
            variable=self.widgets['volume_var'],
            bg='#f0f0f0'
        )
        self.widgets['volume_scale'].pack(side=tk.LEFT)
        
        # Playback speed control
        speed_frame = tk.Frame(controls_frame, bg='#f0f0f0')
        speed_frame.pack(side=tk.RIGHT, padx=10)
        
        tk.Label(speed_frame, text="速度:", bg='#f0f0f0', font=("Arial", 9)).pack(side=tk.LEFT)
        
        self.widgets['speed_var'] = tk.StringVar(value="1.0x")
        self.widgets['speed_button'] = ttk.Button(
            speed_frame,
            textvariable=self.widgets['speed_var'],
            width=6
        )
        self.widgets['speed_button'].pack(side=tk.LEFT, padx=2)
        
        # Progress bar
        progress_frame = tk.Frame(self.widgets['top_frame'], bg='#f0f0f0')
        progress_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.widgets['progress_var'] = tk.DoubleVar()
        self.widgets['progress_scale'] = ttk.Scale( # Changed from Progressbar to Scale
            progress_frame,
            variable=self.widgets['progress_var'],
            from_=0, to=100, # Initial range, will be updated with actual duration
            orient=tk.HORIZONTAL,
            command=lambda val: self._get_callback('seek_position_drag')(val) # Bind to a temporary callback for drag
        )
        self.widgets['progress_scale'].pack(fill=tk.X, padx=5)
        self.widgets['progress_bar'] = self.widgets['progress_scale'] # Keep alias for compatibility
        
        # Enhanced time display
        time_frame = tk.Frame(self.widgets['top_frame'], bg='#f0f0f0')
        time_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        # Current/Total time
        self.widgets['time_label'] = tk.Label(
            time_frame, 
            text="00:00 / 00:00", 
            bg='#f0f0f0',
            font=("Arial", 9, "bold")
        )
        self.widgets['time_label'].pack(side=tk.LEFT)
        
        # Remaining time
        self.widgets['remaining_time_label'] = tk.Label(
            time_frame, 
            text="", 
            bg='#f0f0f0',
            font=("Arial", 8),
            fg='#666666'
        )
        self.widgets['remaining_time_label'].pack(side=tk.LEFT, padx=(10, 0))
        
        # Progress percentage
        self.widgets['progress_percent_label'] = tk.Label(
            time_frame, 
            text="0%", 
            bg='#f0f0f0',
            font=("Arial", 8),
            fg='#666666'
        )
        self.widgets['progress_percent_label'].pack(side=tk.RIGHT)
        
        # Playback rate indicator
        self.widgets['rate_indicator_label'] = tk.Label(
            time_frame, 
            text="1.0x", 
            bg='#f0f0f0',
            font=("Arial", 8),
            fg='#333333'
        )
        self.widgets['rate_indicator_label'].pack(side=tk.RIGHT, padx=(0, 10))
    
    def create_rss_section(self) -> None:
        """Create RSS input and station management section."""
        rss_frame = tk.LabelFrame(self.widgets['top_frame'], text="RSS 來源", bg='#f0f0f0')
        rss_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # RSS URL input
        input_frame = tk.Frame(rss_frame, bg='#f0f0f0')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text="RSS URL:", bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.widgets['rss_entry'] = tk.Entry(input_frame, width=50, state='normal')
        self.widgets['rss_entry'].pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        
        self.widgets['fetch_button'] = ttk.Button(
            input_frame, 
            text="取得"
        )
        self.widgets['fetch_button'].pack(side=tk.RIGHT, padx=2)
        
        # Station management
        station_frame = tk.Frame(rss_frame, bg='#f0f0f0')
        station_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(station_frame, text="我的電台:", bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.widgets['station_var'] = tk.StringVar()
        self.widgets['station_combobox'] = ttk.Combobox(
            station_frame,
            textvariable=self.widgets['station_var'],
            state="readonly",
            width=30
        )
        self.widgets['station_combobox'].pack(side=tk.LEFT, padx=5)
        
        self.widgets['save_station_button'] = ttk.Button(
            station_frame, 
            text="儲存電台"
        )
        self.widgets['save_station_button'].pack(side=tk.LEFT, padx=2)
        
        self.widgets['delete_station_button'] = ttk.Button(
            station_frame, 
            text="刪除電台"
        )
        self.widgets['delete_station_button'].pack(side=tk.LEFT, padx=2)
    
    def create_episode_list(self) -> None:
        """Create episode list display."""
        # Left panel for episodes
        left_panel = tk.Frame(self.widgets['middle_frame'])
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Header with search functionality
        header_frame = tk.Frame(left_panel)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        tk.Label(header_frame, text="節目列表", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        
        # Enhanced search functionality
        search_frame = tk.Frame(header_frame)
        search_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        tk.Label(search_frame, text="搜尋:", font=("Arial", 9)).pack(side=tk.LEFT)
        
        # Search input with history
        search_input_frame = tk.Frame(search_frame)
        search_input_frame.pack(side=tk.LEFT, padx=(5, 2))
        
        self.widgets['search_var'] = tk.StringVar()
        self.widgets['search_entry'] = tk.Entry(
            search_input_frame, 
            textvariable=self.widgets['search_var'],
            width=20,
            font=("Arial", 9)
        )
        self.widgets['search_entry'].pack(side=tk.TOP)
        
        # Search history dropdown (initially hidden)
        self.widgets['search_history_var'] = tk.StringVar()
        self.widgets['search_history_combo'] = ttk.Combobox(
            search_input_frame,
            textvariable=self.widgets['search_history_var'],
            font=("Arial", 8),
            height=5,
            width=18,
            state='readonly'
        )
        
        # Search options
        search_options_frame = tk.Frame(search_frame)
        search_options_frame.pack(side=tk.LEFT, padx=2)
        
        # Clear search button
        self.widgets['clear_search_button'] = ttk.Button(
            search_options_frame,
            text="清除",
            width=5
        )
        self.widgets['clear_search_button'].pack(side=tk.TOP)
        
        # Search mode toggle
        self.widgets['search_mode_var'] = tk.StringVar(value="模糊")
        self.widgets['search_mode_button'] = ttk.Button(
            search_options_frame,
            textvariable=self.widgets['search_mode_var'],
            width=5
        )
        self.widgets['search_mode_button'].pack(side=tk.TOP, pady=(2, 0))
        
        # Search status
        self.widgets['search_status_label'] = tk.Label(
            search_frame,
            text="",
            font=("Arial", 8),
            fg="gray"
        )
        self.widgets['search_status_label'].pack(side=tk.RIGHT, padx=(5, 0))
        
        # Episode tree view
        tree_frame = tk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('title', 'published', 'duration')
        self.widgets['episode_tree'] = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        # Configure columns
        self.widgets['episode_tree'].heading('title', text='標題')
        self.widgets['episode_tree'].heading('published', text='發布日期')
        self.widgets['episode_tree'].heading('duration', text='時長')
        
        self.widgets['episode_tree'].column('title', width=300)
        self.widgets['episode_tree'].column('published', width=150)
        self.widgets['episode_tree'].column('duration', width=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.widgets['episode_tree'].yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.widgets['episode_tree'].xview)
        
        self.widgets['episode_tree'].configure(yscrollcommand=v_scrollbar.set)
        self.widgets['episode_tree'].configure(xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        self.widgets['episode_tree'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
    
    def create_playlist_section(self) -> None:
        """Create playlist display section."""
        # Right panel for playlist
        right_panel = tk.Frame(self.widgets['middle_frame'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        tk.Label(right_panel, text="播放清單", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # Playlist listbox
        playlist_frame = tk.Frame(right_panel)
        playlist_frame.pack(fill=tk.BOTH, expand=True)
        
        self.widgets['playlist_listbox'] = tk.Listbox(playlist_frame)
        
        # Scrollbar for playlist
        playlist_scrollbar = ttk.Scrollbar(playlist_frame, orient=tk.VERTICAL, command=self.widgets['playlist_listbox'].yview)
        self.widgets['playlist_listbox'].configure(yscrollcommand=playlist_scrollbar.set)
        
        # Pack playlist components
        self.widgets['playlist_listbox'].pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
    
    def create_status_bar(self) -> None:
        """Create status bar."""
        self.widgets['status_label'] = tk.Label(
            self.widgets['bottom_frame'], 
            text="就緒", 
            anchor=tk.W,
            bg='#e0e0e0'
        )
        self.widgets['status_label'].pack(fill=tk.X, padx=5, pady=2)
    
    def set_callback(self, event_name: str, callback: Callable) -> None:
        """
        Set callback function for UI events.
        
        Args:
            event_name: Event name
            callback: Callback function
        """
        self.callbacks[event_name] = callback
    
    def _get_callback(self, event_name: str) -> Callable:
        """Get callback for event, returns no-op if not set."""
        return self.callbacks.get(event_name, lambda *args, **kwargs: None)
    
    def setup_callbacks(self, event_handlers) -> None:
        """
        Set up all callbacks after event handlers are created.
        
        Args:
            event_handlers: EventHandlers instance with all the callback methods
        """
        # Map event names to event handler methods
        callback_mapping = {
            'toggle_play': event_handlers.handle_toggle_play,
            'stop': event_handlers.handle_stop,
            'previous_track': event_handlers.handle_previous_track,
            'next_track': event_handlers.handle_next_track,
            'volume_changed': event_handlers.handle_volume_changed,
            'fetch_podcast': event_handlers.handle_fetch_podcast,
            'station_selected': event_handlers.handle_station_selected,
            'search_episodes': event_handlers.handle_search_episodes,
            'clear_search': event_handlers.handle_clear_search,
            'cycle_speed': event_handlers.handle_cycle_speed,
            'save_station': event_handlers.handle_save_station,
            'delete_station': event_handlers.handle_delete_station,
            'episode_double_click': event_handlers.handle_episode_double_click,
            'episode_select': event_handlers.handle_episode_select,
            'playlist_double_click': event_handlers.handle_playlist_double_click,
            'import_stations': event_handlers.handle_import_stations,
            'export_stations': event_handlers.handle_export_stations,
            'import_playlist': event_handlers.handle_import_playlist,
            'export_playlist': event_handlers.handle_export_playlist,
            'clear_history': event_handlers.handle_clear_history,
            'clear_stations': event_handlers.handle_clear_stations
        }
        
        # Set all callbacks
        for event_name, callback_method in callback_mapping.items():
            self.set_callback(event_name, callback_method)

        # --- Bind Callbacks to Widgets ---
        # Menu
        self.widgets['file_menu'].entryconfig("匯入電台列表", command=self._get_callback('import_stations'))
        self.widgets['file_menu'].entryconfig("匯出電台列表", command=self._get_callback('export_stations'))
        self.widgets['file_menu'].entryconfig("匯入播放清單", command=self._get_callback('import_playlist'))
        self.widgets['file_menu'].entryconfig("匯出播放清單", command=self._get_callback('export_playlist'))
        self.widgets['edit_menu'].entryconfig("清除播放紀錄", command=self._get_callback('clear_history'))
        self.widgets['edit_menu'].entryconfig("清除所有電台", command=self._get_callback('clear_stations'))

        # Controls
        self.widgets['prev_button'].config(command=self._get_callback('previous_track'))
        self.widgets['play_button'].config(command=self._get_callback('toggle_play'))
        self.widgets['stop_button'].config(command=self._get_callback('stop'))
        self.widgets['next_button'].config(command=self._get_callback('next_track'))
        self.widgets['volume_scale'].config(command=self._get_callback('volume_changed'))
        self.widgets['speed_button'].config(command=self._get_callback('cycle_speed'))

        # RSS Section
        self.widgets['fetch_button'].config(command=self._get_callback('fetch_podcast'))
        self.widgets['station_combobox'].bind('<<ComboboxSelected>>', self._get_callback('station_selected'))
        self.widgets['save_station_button'].config(command=self._get_callback('save_station'))
        self.widgets['delete_station_button'].config(command=self._get_callback('delete_station'))

        # Episode List and Enhanced Search
        self.widgets['search_var'].trace('w', self._get_callback('search_episodes'))
        self.widgets['clear_search_button'].config(command=self._get_callback('clear_search'))
        self.widgets['search_mode_button'].config(command=self._toggle_search_mode)
        self.widgets['search_history_combo'].bind('<<ComboboxSelected>>', self._on_history_selected)
        self.widgets['search_entry'].bind('<Return>', lambda e: self._handle_search_enter(e))
        self.widgets['search_entry'].bind('<Escape>', lambda e: self._handle_search_escape(e))
        self.widgets['search_entry'].bind('<Control-a>', lambda e: self._handle_search_select_all(e))
        self.widgets['episode_tree'].bind('<Double-1>', self._get_callback('episode_double_click'))
        self.widgets['episode_tree'].bind('<<TreeviewSelect>>', self._get_callback('episode_select'))

        # Playlist
        self.widgets['playlist_listbox'].bind('<Double-1>', self._get_callback('playlist_double_click'))
        
        print(f"UI callbacks set up and bound: {len(callback_mapping)} events mapped")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        messagebox.showinfo(
            "關於", 
            "Podcast 播放器\\n\\n一個簡單的 RSS 播客播放器\\n支援 RSS 訂閱和音訊播放功能"
        )
    
    def update_status(self, message: str) -> None:
        """Update status bar message."""
        if 'status_label' in self.widgets:
            self.widgets['status_label'].config(text=message)
    
    def set_controls_state(self, enabled: bool) -> None:
        """Enable or disable playback controls."""
        state = tk.NORMAL if enabled else tk.DISABLED
        
        controls = ['play_button', 'stop_button', 'prev_button', 'next_button']
        for control in controls:
            if control in self.widgets:
                self.widgets[control].config(state=state)
    
    def update_play_button(self, is_playing: bool, is_paused: bool) -> None:
        """Update play button text based on state."""
        if 'play_button' not in self.widgets:
            return
        
        if is_playing and not is_paused:
            self.widgets['play_button'].config(text="暫停")
        else:
            self.widgets['play_button'].config(text="播放")
    
    def update_progress(self, current: int, duration: int, playback_rate: float = 1.0) -> None:
        """Update progress scale and enhanced time display."""
        if 'progress_var' in self.widgets and 'time_label' in self.widgets and 'progress_scale' in self.widgets:
            # Update progress scale range and value
            if duration > 0:
                self.widgets['progress_scale'].config(to=duration)
                self.widgets['progress_var'].set(current)
                progress_percent = (current / duration) * 100
            else:
                self.widgets['progress_scale'].config(to=0)
                self.widgets['progress_var'].set(0)
                progress_percent = 0
            
            # Update main time display
            current_time = self._format_time_enhanced(current)
            total_time = self._format_time_enhanced(duration)
            self.widgets['time_label'].config(text=f"{current_time} / {total_time}")
            
            # Update remaining time
            if duration > 0 and 'remaining_time_label' in self.widgets:
                remaining_seconds = duration - current
                remaining_time = self._format_time_enhanced(remaining_seconds)
                self.widgets['remaining_time_label'].config(text=f"剩餘 {remaining_time}")
            elif 'remaining_time_label' in self.widgets:
                self.widgets['remaining_time_label'].config(text="")
            
            # Update progress percentage
            if 'progress_percent_label' in self.widgets:
                self.widgets['progress_percent_label'].config(text=f"{progress_percent:.1f}%")
            
            # Update playback rate indicator
            if 'rate_indicator_label' in self.widgets:
                self.widgets['rate_indicator_label'].config(text=f"{playback_rate:.1f}x")
    
    def update_station_combobox(self, stations: list) -> None:
        """Update station combobox with station list."""
        if 'station_combobox' in self.widgets:
            self.widgets['station_combobox']['values'] = stations
    
    def populate_episode_tree(self, episodes: list) -> None:
        """Populate episode tree with episode data."""
        if 'episode_tree' not in self.widgets:
            return
        
        # Clear existing items
        for item in self.widgets['episode_tree'].get_children():
            self.widgets['episode_tree'].delete(item)
        
        # Add episodes
        for episode in episodes:
            self.widgets['episode_tree'].insert('', tk.END, values=(
                episode.title[:50] + "..." if len(episode.title) > 50 else episode.title,
                episode.published,
                episode.duration or "Unknown"
            ))
    
    def populate_playlist(self, tracks: list, current_index: int = -1) -> None:
        """Populate playlist listbox with tracks."""
        if 'playlist_listbox' not in self.widgets:
            return
        
        # Clear existing items
        self.widgets['playlist_listbox'].delete(0, tk.END)
        
        # Add tracks
        for i, track in enumerate(tracks):
            display_text = f"{i+1:2d}. {track.title}"
            self.widgets['playlist_listbox'].insert(tk.END, display_text)
            
            # Highlight current track
            if i == current_index:
                self.widgets['playlist_listbox'].selection_set(i)
                self.widgets['playlist_listbox'].activate(i)
    
    def get_widget(self, name: str) -> Optional[tk.Widget]:
        """Get widget by name."""
        return self.widgets.get(name)
    
    def _format_time(self, seconds: int) -> str:
        """Format time in MM:SS format."""
        if seconds < 0:
            return "00:00"
        
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def _format_time_enhanced(self, seconds: int) -> str:
        """Format time with hours if needed (HH:MM:SS or MM:SS)."""
        if seconds < 0:
            return "00:00"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _toggle_search_mode(self) -> None:
        """Toggle between fuzzy and exact search modes."""
        current_mode = self.widgets['search_mode_var'].get()
        new_mode = "精確" if current_mode == "模糊" else "模糊"
        self.widgets['search_mode_var'].set(new_mode)
        
        # Trigger search refresh if there's a current search
        search_term = self.widgets['search_var'].get().strip()
        if search_term:
            # Re-trigger search with new mode
            if 'search_episodes' in self.callbacks:
                self.callbacks['search_episodes']()
    
    def update_search_history(self, history_list) -> None:
        """
        Update search history dropdown.
        
        Args:
            history_list: List of search history items
        """
        combo = self.widgets['search_history_combo']
        combo['values'] = history_list
        
        # Show/hide history dropdown based on availability
        if history_list:
            combo.pack(side=tk.TOP, pady=(2, 0))
        else:
            combo.pack_forget()
    
    def get_search_mode(self) -> str:
        """Get current search mode."""
        return self.widgets['search_mode_var'].get()
    
    def update_search_status(self, status: str) -> None:
        """
        Update search status label.
        
        Args:
            status: Status message to display
        """
        self.widgets['search_status_label'].config(text=status)
    
    def _on_history_selected(self, event) -> None:
        """Handle search history selection."""
        selected_term = self.widgets['search_history_var'].get()
        if selected_term:
            self.widgets['search_var'].set(selected_term)
            # Hide history dropdown after selection
            self.widgets['search_history_combo'].pack_forget()
    
    def _handle_search_enter(self, event) -> None:
        """Handle Enter key in search entry."""
        try:
            if 'search_episodes' in self.callbacks:
                self.callbacks['search_episodes']()
            return 'break'  # Prevent further event propagation
        except Exception as e:
            print(f"Error handling search enter: {e}")
    
    def _handle_search_escape(self, event) -> None:
        """Handle Escape key in search entry."""
        try:
            if 'clear_search' in self.callbacks:
                self.callbacks['clear_search']()
            return 'break'  # Prevent further event propagation
        except Exception as e:
            print(f"Error handling search escape: {e}")
    
    def _handle_search_select_all(self, event) -> None:
        """Handle Ctrl+A in search entry."""
        try:
            self.widgets['search_entry'].select_range(0, tk.END)
            return 'break'  # Prevent further event propagation
        except Exception as e:
            print(f"Error selecting all in search: {e}")
    
    def _show_about(self) -> None:
        """Show about dialog."""
        from tkinter import messagebox
        messagebox.showinfo(
            "關於 Podcast 播放器", 
            "Podcast 播放器 v1.0\\n\\n"
            "一個使用 Python 開發的播客播放器，支援 RSS 訂閱和播放清單管理。"
        )
