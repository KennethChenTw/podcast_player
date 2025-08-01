"""
Event Handlers for Podcast Player

Handles user interface events and coordinates between UI and core functionality.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Optional, List


class EventHandlers:
    """Handles UI events and coordinates with core functionality."""
    
    def __init__(self, audio_player, rss_processor, station_manager, 
                 playlist_manager, config_manager, ui_components):
        """
        Initialize event handlers.
        
        Args:
            audio_player: AudioPlayer instance
            rss_processor: RSSProcessor instance
            station_manager: StationManager instance
            playlist_manager: PlaylistManager instance
            config_manager: ConfigManager instance
            ui_components: PodcastPlayerUI instance
        """
        self.audio_player = audio_player
        self.rss_processor = rss_processor
        self.station_manager = station_manager
        self.playlist_manager = playlist_manager
        self.config_manager = config_manager
        self.ui = ui_components
        
        # Current podcast data
        self.current_podcast_data = None
        
        # Callbacks will be set up by the UI component after initialization
    
    
    def handle_toggle_play(self) -> None:
        """Handle play/pause button click."""
        try:
            current_track = self.playlist_manager.get_current_track()
            if not current_track:
                messagebox.showwarning("警告", "請先選擇要播放的曲目")
                return
            
            if self.audio_player.is_playing:
                # Toggle pause/resume
                is_playing = self.audio_player.toggle_play()
                self.ui.update_play_button(is_playing, not is_playing)
                
                if is_playing:
                    self.ui.update_status("繼續播放")
                else:
                    self.ui.update_status("已暫停")
            else:
                # Start playing
                self.ui.update_status("正在載入...")
                self.ui.set_controls_state(False)
                
                self.audio_player.play_track(
                    url=current_track.url,
                    title=current_track.title,
                    progress_callback=self.handle_progress_update,
                    completion_callback=self.handle_track_completion,
                    error_callback=self.handle_playback_error
                )
                
                self.ui.update_play_button(True, False)
                self.ui.set_controls_state(True)
                self.ui.update_status(f"播放: {current_track.title}")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"播放時發生錯誤: {str(e)}")
            self.ui.update_status("播放錯誤")
    
    def handle_stop(self) -> None:
        """Handle stop button click."""
        try:
            self.audio_player.stop()
            self.ui.update_play_button(False, False)
            self.ui.update_progress(0, 0)
            self.ui.update_status("已停止")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"停止播放時發生錯誤: {str(e)}")
    
    def handle_previous_track(self) -> None:
        """Handle previous track button click."""
        try:
            previous_track = self.playlist_manager.previous_track()
            if previous_track:
                self.ui.populate_playlist(
                    self.playlist_manager.get_playlist_copy(), 
                    self.playlist_manager.current_index
                )
                
                # Auto-play if currently playing
                if self.audio_player.is_playing:
                    self.handle_toggle_play()
                    
                self.ui.update_status(f"上一首: {previous_track.title}")
            else:
                messagebox.showinfo("資訊", "已經是第一首曲目")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"切換曲目時發生錯誤: {str(e)}")
    
    def handle_next_track(self) -> None:
        """Handle next track button click."""
        try:
            next_track = self.playlist_manager.next_track()
            if next_track:
                self.ui.populate_playlist(
                    self.playlist_manager.get_playlist_copy(),
                    self.playlist_manager.current_index
                )
                
                # Auto-play if currently playing
                if self.audio_player.is_playing:
                    self.handle_toggle_play()
                    
                self.ui.update_status(f"下一首: {next_track.title}")
            else:
                messagebox.showinfo("資訊", "已經是最後一首曲目")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"切換曲目時發生錯誤: {str(e)}")
    
    def handle_volume_changed(self, value: str) -> None:
        """Handle volume change."""
        try:
            volume = float(value)
            self.audio_player.set_volume(volume)
            
        except Exception as e:
            print(f"Error changing volume: {e}")
    
    def handle_fetch_podcast(self) -> None:
        """Handle RSS fetch button click."""
        print("=== RSS FETCH EVENT ===")
        try:
            rss_entry = self.ui.get_widget('rss_entry')
            if not rss_entry:
                print("No RSS entry widget found!")
                return
            
            url = rss_entry.get().strip()
            print(f"Fetching RSS URL: '{url}'")
            
            if not url:
                print("No URL provided")
                messagebox.showwarning("警告", "請輸入 RSS URL")
                return
            
            print("Validating RSS URL...")
            try:
                if not self.rss_processor.validate_rss_url(url):
                    print("RSS URL validation failed")
                    messagebox.showwarning("警告", "請輸入有效的 RSS URL")
                    return
            except AttributeError as e:
                print(f"RSS processor validation method missing: {e}")
                # Try basic URL validation
                if not url.startswith(('http://', 'https://')):
                    messagebox.showwarning("警告", "請輸入有效的 RSS URL（需以 http:// 或 https:// 開頭）")
                    return
            
            print("RSS URL validation passed")
            self.ui.update_status("正在取得 RSS 內容...")
            
            fetch_button = self.ui.get_widget('fetch_button')
            if fetch_button:
                fetch_button.config(state=tk.DISABLED)
            
            print("Starting RSS fetch thread...")
            try:
                self.rss_processor.fetch_podcast_thread(
                    url=url,
                    success_callback=self.handle_rss_success,
                    error_callback=self.handle_rss_error,
                    complete_callback=self.handle_rss_complete
                )
            except ImportError as e:
                error_msg = f"缺少必要依賴: {str(e)}\n\n請運行: pip install feedparser requests"
                print(f"Import error: {error_msg}")
                messagebox.showerror("依賴缺失", error_msg)
                self.handle_rss_complete()
            
        except Exception as e:
            print(f"Exception in handle_fetch_podcast: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("錯誤", f"取得 RSS 時發生錯誤: {str(e)}")
            self.handle_rss_complete()
        print("=== END RSS FETCH ===\n")
    
    def handle_rss_success(self, podcast_data) -> None:
        """Handle successful RSS fetch."""
        try:
            self.current_podcast_data = podcast_data
            
            # Update UI with episodes
            self.ui.populate_episode_tree(podcast_data.episodes)
            
            self.ui.update_status(f"已載入 {len(podcast_data.episodes)} 個節目")
            
        except Exception as e:
            print(f"RSS Success Handler Error: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("錯誤", f"處理 RSS 資料時發生錯誤: {str(e)}")
    
    def handle_rss_error(self, error_message: str) -> None:
        """Handle RSS fetch error."""
        print(f"RSS Error: {error_message}")
        messagebox.showerror("錯誤", f"無法取得 RSS 內容: {error_message}")
        self.ui.update_status("RSS 取得失敗")
    
    def handle_rss_complete(self) -> None:
        """Handle RSS fetch completion."""
        fetch_button = self.ui.get_widget('fetch_button')
        if fetch_button:
            fetch_button.config(state=tk.NORMAL)
    
    def handle_station_selected(self, event) -> None:
        """Handle station selection from combobox."""
        print("=== STATION SELECTION EVENT ===")
        try:
            station_var = self.ui.get_widget('station_var')
            rss_entry = self.ui.get_widget('rss_entry')
            
            print(f"Station var: {station_var}")
            print(f"RSS entry: {rss_entry}")
            
            if not station_var or not rss_entry:
                print("Missing widgets!")
                return
            
            station_name = station_var.get()
            print(f"Selected station name: '{station_name}'")
            
            if station_name:
                station_url = self.station_manager.get_station_url(station_name)
                print(f"Station URL: {station_url}")
                
                if station_url:
                    print("Updating RSS entry...")
                    rss_entry.delete(0, tk.END)
                    rss_entry.insert(0, station_url)
                    
                    # Verify the update
                    current_content = rss_entry.get()
                    print(f"RSS entry after update: '{current_content}'")
                    
                    # Update status
                    self.ui.update_status(f"已選擇電台: {station_name}")
                else:
                    print("No URL found for station!")
            else:
                print("No station name!")
                    
        except Exception as e:
            print(f"Error selecting station: {e}")
            import traceback
            traceback.print_exc()
        print("=== END STATION SELECTION ===\n")
    
    def handle_save_station(self) -> None:
        """Handle save station button click."""
        try:
            rss_entry = self.ui.get_widget('rss_entry')
            if not rss_entry:
                return
            
            url = rss_entry.get().strip()
            if not url:
                messagebox.showwarning("警告", "請先輸入 RSS URL")
                return
            
            station_name = simpledialog.askstring("儲存電台", "請輸入電台名稱:")
            if station_name:
                station_name = station_name.strip()
                if self.station_manager.add_station(station_name, url):
                    self.ui.update_station_combobox(self.station_manager.get_station_names())
                    messagebox.showinfo("成功", f"已儲存電台: {station_name}")
                else:
                    messagebox.showwarning("警告", "電台名稱已存在")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存電台時發生錯誤: {str(e)}")
    
    def handle_delete_station(self) -> None:
        """Handle delete station button click."""
        try:
            station_var = self.ui.get_widget('station_var')
            if not station_var:
                return
            
            station_name = station_var.get()
            if not station_name:
                messagebox.showwarning("警告", "請先選擇要刪除的電台")
                return
            
            if messagebox.askyesno("確認", f"確定要刪除電台 '{station_name}' 嗎?"):
                if self.station_manager.delete_station(station_name):
                    self.ui.update_station_combobox(self.station_manager.get_station_names())
                    station_var.set("")
                    messagebox.showinfo("成功", f"已刪除電台: {station_name}")
                else:
                    messagebox.showerror("錯誤", "刪除電台失敗")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"刪除電台時發生錯誤: {str(e)}")
    
    def handle_episode_double_click(self, event) -> None:
        """Handle episode list double click."""
        try:
            episode_tree = self.ui.get_widget('episode_tree')
            if not episode_tree or not self.current_podcast_data:
                return
            
            selection = episode_tree.selection()
            if selection:
                item = selection[0]
                index = episode_tree.index(item)
                
                if 0 <= index < len(self.current_podcast_data.episodes):
                    episode = self.current_podcast_data.episodes[index]
                    
                    # Add to playlist
                    new_index = self.playlist_manager.add_track(episode)
                    self.ui.populate_playlist(
                        self.playlist_manager.get_playlist_copy(),
                        self.playlist_manager.current_index
                    )

                    # If not playing, start playing the new track
                    if not self.audio_player.is_playing:
                        self.playlist_manager.set_current_index(new_index)
                        self.ui.populate_playlist(
                            self.playlist_manager.get_playlist_copy(),
                            self.playlist_manager.current_index
                        )
                        self.handle_toggle_play()
                    else:
                        self.ui.update_status(f"'{episode.title}' 已加入播放清單")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"播放節目時發生錯誤: {str(e)}")
    
    def handle_episode_select(self, event) -> None:
        """Handle episode selection."""
        # Could be used to show episode details
        pass
    
    def handle_playlist_double_click(self, event) -> None:
        """Handle playlist double click."""
        try:
            playlist_listbox = self.ui.get_widget('playlist_listbox')
            if not playlist_listbox:
                return
            
            selection = playlist_listbox.curselection()
            if selection:
                index = selection[0]
                if self.playlist_manager.set_current_index(index):
                    self.ui.populate_playlist(
                        self.playlist_manager.get_playlist_copy(),
                        self.playlist_manager.current_index
                    )
                    
                    self.handle_toggle_play()
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"播放曲目時發生錯誤: {str(e)}")
    
    def handle_progress_update(self, current_pos: int, duration: int) -> None:
        """Handle progress update from audio player."""
        try:
            # Get current playback rate from audio player
            playback_rate = getattr(self.audio_player, 'playback_speed', 1.0)
            
            # Update UI with enhanced progress information
            self.ui.update_progress(current_pos, duration, playback_rate)
            
        except Exception as e:
            print(f"Error updating progress: {e}")
    
    def handle_track_completion(self) -> None:
        """Handle track completion."""
        try:
            # Auto-play next track
            next_track = self.playlist_manager.next_track()
            if next_track:
                self.ui.populate_playlist(
                    self.playlist_manager.get_playlist_copy(),
                    self.playlist_manager.current_index
                )
                
                self.handle_toggle_play()
            else:
                self.ui.update_play_button(False, False)
                self.ui.update_status("播放完畢")
                
        except Exception as e:
            print(f"Error handling track completion: {e}")
    
    def handle_playback_error(self, error_message: str) -> None:
        """Handle playback error."""
        messagebox.showerror("播放錯誤", f"無法播放音訊: {error_message}")
        self.ui.update_play_button(False, False)
        self.ui.set_controls_state(True)
        self.ui.update_status("播放錯誤")
    
    def handle_import_stations(self) -> None:
        """Handle import stations menu item."""
        try:
            success, message = self.station_manager.import_stations(self.ui.root)
            if success:
                self.ui.update_station_combobox(self.station_manager.get_station_names())
                messagebox.showinfo("成功", message)
            elif "cancelled" not in message:
                messagebox.showerror("錯誤", message)
                
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入電台時發生錯誤: {str(e)}")
    
    def handle_export_stations(self) -> None:
        """Handle export stations menu item."""
        try:
            success, message = self.station_manager.export_stations(self.ui.root)
            if success:
                messagebox.showinfo("成功", message)
            elif "cancelled" not in message:
                messagebox.showerror("錯誤", message)
                
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出電台時發生錯誤: {str(e)}")
    
    def handle_import_playlist(self) -> None:
        """Handle import playlist menu item."""
        try:
            success, message = self.playlist_manager.import_playlist(self.ui.root)
            if success:
                self.ui.populate_playlist(
                    self.playlist_manager.get_playlist_copy(),
                    self.playlist_manager.current_index
                )
                messagebox.showinfo("成功", message)
            elif "cancelled" not in message:
                messagebox.showerror("錯誤", message)
                
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入播放清單時發生錯誤: {str(e)}")
    
    def handle_export_playlist(self) -> None:
        """Handle export playlist menu item."""
        try:
            success, message = self.playlist_manager.export_playlist(self.ui.root)
            if success:
                messagebox.showinfo("成功", message)
            elif "cancelled" not in message:
                messagebox.showerror("錯誤", message)
                
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出播放清單時發生錯誤: {str(e)}")

    def handle_seek_position(self, value: str) -> None:
        """Handle seeking to a new position from the progress scale."""
        try:
            position = int(float(value)) # Scale value is float, convert to int seconds
            self.audio_player.seek(position)
            self.ui.update_status(f"跳轉至: {self.audio_player.format_time(position)}")
        except Exception as e:
            print(f"Error seeking position: {e}")
            messagebox.showerror("錯誤", f"跳轉時發生錯誤: {str(e)}")

    def handle_refresh(self) -> None:
        """Handle the refresh action."""
        self.handle_fetch_podcast()
    
    def handle_clear_history(self) -> None:
        """Handle clear history menu item."""
        try:
            if messagebox.askyesno("確認", "確定要清除所有播放紀錄嗎?"):
                if self.playlist_manager.clear_history():
                    messagebox.showinfo("成功", "已清除播放紀錄")
                else:
                    messagebox.showerror("錯誤", "清除播放紀錄失敗")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"清除播放紀錄時發生錯誤: {str(e)}")
    
    def handle_clear_stations(self) -> None:
        """Handle clear all stations menu item."""
        try:
            if messagebox.askyesno("確認", "確定要清除所有電台嗎?"):
                if self.station_manager.clear_all_stations():
                    self.ui.update_station_combobox([])
                    messagebox.showinfo("成功", "已清除所有電台")
                else:
                    messagebox.showerror("錯誤", "清除電台失敗")
                    
        except Exception as e:
            messagebox.showerror("錯誤", f"清除電台時發生錯誤: {str(e)}")
    
    def handle_search_episodes(self, *args) -> None:
        """Handle episode search with enhanced fuzzy matching."""
        try:
            if not self.current_podcast_data:
                return
            
            search_term = self.ui.get_widget('search_var').get().strip()
            
            if not search_term:
                # Show all episodes if search is empty
                self.ui.populate_episode_tree(self.current_podcast_data.episodes)
                return
            
            # Add to search history
            self._add_to_search_history(search_term)
            
            # Update search history UI
            self.ui.update_search_history(self.get_search_history())
            
            # Check search mode and filter accordingly
            search_mode = self.ui.get_search_mode()
            if search_mode == "模糊":
                filtered_episodes = self._filter_episodes_fuzzy(self.current_podcast_data.episodes, search_term)
            else:
                filtered_episodes = self._filter_episodes_exact(self.current_podcast_data.episodes, search_term)
            
            # Update UI with filtered results
            self.ui.populate_episode_tree(filtered_episodes)
            
            # Update status with more detailed info
            if filtered_episodes:
                total_episodes = len(self.current_podcast_data.episodes)
                self.ui.update_status(f"搜尋 '{search_term}': 找到 {len(filtered_episodes)}/{total_episodes} 個相符的集數")
            else:
                self.ui.update_status(f"搜尋 '{search_term}': 沒有找到相符的集數")
                
        except Exception as e:
            print(f"Search error: {e}")
            self.ui.update_status("搜尋時發生錯誤")
    
    def _filter_episodes_fuzzy(self, episodes, search_term):
        """
        Filter episodes using fuzzy matching algorithm.
        
        Args:
            episodes: List of episodes to filter
            search_term: Search term to match against
            
        Returns:
            List of matched episodes, sorted by relevance
        """
        search_lower = search_term.lower()
        search_words = search_lower.split()
        
        matches = []
        
        for episode in episodes:
            title_lower = episode.title.lower()
            description_lower = episode.description.lower()
            
            # Scoring system for relevance
            score = 0
            
            # Exact phrase match (highest priority)
            if search_lower in title_lower:
                score += 100
            elif search_lower in description_lower:
                score += 50
            
            # Individual word matches
            for word in search_words:
                if word in title_lower:
                    score += 20
                elif word in description_lower:
                    score += 10
                
                # Fuzzy matching for similar words
                title_words = title_lower.split()
                desc_words = description_lower.split()
                
                for title_word in title_words:
                    if self._fuzzy_match(word, title_word):
                        score += 15
                        
                for desc_word in desc_words:
                    if self._fuzzy_match(word, desc_word):
                        score += 8
            
            # Include episode if it has any relevance
            if score > 0:
                matches.append((episode, score))
        
        # Sort by score (descending) and return episodes
        matches.sort(key=lambda x: x[1], reverse=True)
        return [match[0] for match in matches]
    
    def _fuzzy_match(self, word1, word2, threshold=0.7):
        """
        Simple fuzzy string matching using Levenshtein-like algorithm.
        
        Args:
            word1: First word to compare
            word2: Second word to compare
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if words are similar enough, False otherwise
        """
        if len(word1) < 3 or len(word2) < 3:
            return word1 == word2
        
        # Simple similarity calculation
        shorter = min(len(word1), len(word2))
        longer = max(len(word1), len(word2))
        
        if longer == 0:
            return True
        
        # Count matching characters in order
        matches = 0
        i = j = 0
        while i < len(word1) and j < len(word2):
            if word1[i] == word2[j]:
                matches += 1
                i += 1
                j += 1
            else:
                i += 1 if len(word1) > len(word2) else j + 1
                j += 1 if len(word2) > len(word1) else i + 1
        
        similarity = matches / longer
        return similarity >= threshold
    
    def _add_to_search_history(self, search_term):
        """Add search term to history."""
        if not hasattr(self, 'search_history'):
            self.search_history = []
        
        # Remove if already exists (move to front)
        if search_term in self.search_history:
            self.search_history.remove(search_term)
        
        # Add to front
        self.search_history.insert(0, search_term)
        
        # Limit history size
        if len(self.search_history) > 20:
            self.search_history = self.search_history[:20]
    
    def _filter_episodes_exact(self, episodes, search_term):
        """
        Filter episodes using exact matching.
        
        Args:
            episodes: List of episodes to filter
            search_term: Search term to match against
            
        Returns:
            List of matched episodes
        """
        search_lower = search_term.lower()
        matches = []
        
        for episode in episodes:
            title_lower = episode.title.lower()
            description_lower = episode.description.lower()
            
            if search_lower in title_lower or search_lower in description_lower:
                matches.append(episode)
        
        return matches
    
    def get_search_history(self):
        """Get search history for UI components."""
        return getattr(self, 'search_history', [])
    
    def handle_clear_search(self) -> None:
        """Handle clear search."""
        try:
            # Clear search entry
            search_var = self.ui.get_widget('search_var')
            if search_var:
                search_var.set("")
            
            # Show all episodes
            if self.current_podcast_data:
                self.ui.populate_episode_tree(self.current_podcast_data.episodes)
                self.ui.update_status(f"顯示所有 {len(self.current_podcast_data.episodes)} 個集數")
            
        except Exception as e:
            print(f"Clear search error: {e}")
            self.ui.update_status("清除搜尋時發生錯誤")
    
    def handle_cycle_speed(self) -> None:
        """Handle playback speed cycling."""
        try:
            new_speed = self.audio_player.cycle_playback_speed()
            
            # Update UI
            speed_var = self.ui.get_widget('speed_var')
            if speed_var:
                speed_var.set(f"{new_speed}x")
            
            # Update status
            self.ui.update_status(f"播放速度: {new_speed}x")
            
        except Exception as e:
            print(f"Speed cycle error: {e}")
            self.ui.update_status("播放速度切換時發生錯誤")
