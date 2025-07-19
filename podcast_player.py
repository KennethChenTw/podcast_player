import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pygame
import feedparser
import threading
import time
import json
import os
import sys
import tempfile
import shutil
import subprocess
import traceback
from urllib.parse import urlparse
import requests

# 頂層導入VLC (為未來擴充保留)
try:
    import vlc
except (ImportError, OSError):
    vlc = None

class PodcastPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Podcast 播放器")

        # --- 檔案路徑設定 ---
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.stations_file = os.path.join(self.script_dir, "my_stations.json")
        self.history_file = os.path.join(self.script_dir, "podcast_history.json")
        self.settings_file = os.path.join(self.script_dir, "window_settings.json")

        # --- 播放器核心設定 ---
        self.is_playing = False
        self.is_paused = False
        self.current_pos = 0
        self.duration = 0
        self.volume = 0.7
        self.current_temp_dir = None
        self.is_loading = False 
        self.play_request_id = 0 

        # --- 資料模型 ---
        self.playlist = []
        self.current_index = 0
        self.podcast_data = {}
        self.my_stations = {}
        self.settings = {} 

        # --- 初始化 ---
        self.init_player()
        self.load_window_settings() 
        
        initial_geometry = self.settings.get('geometry', "1000x750")
        self.root.geometry(initial_geometry)
        
        self.create_widgets()
        self.load_stations()
        self.load_history()

        self.apply_restored_state()

        self.progress_thread = threading.Thread(target=self.update_progress, daemon=True)
        self.progress_thread.start()

    def load_window_settings(self):
        """讀取設定檔到 self.settings 字典"""
        if not os.path.exists(self.settings_file): return
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"無法讀取視窗設定，將使用預設值: {e}")
            self.settings = {}

    def save_window_settings(self):
        """儲存視窗大小、音量及最後狀態"""
        try:
            settings = {
                'geometry': self.root.geometry(),
                'volume': self.volume,
                'last_station_url': self.rss_url_entry.get()
            }
            if self.playlist:
                settings['last_playlist_index'] = self.current_index
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"儲存視窗設定失敗: {e}")

    def apply_restored_state(self):
        """在UI元件建立後，應用載入的設定"""
        saved_volume = self.settings.get('volume', self.volume) 
        self.volume_var.set(saved_volume * 100)
        self.set_volume(self.volume_var.get())

        last_url = self.settings.get('last_station_url')
        if last_url:
            self.rss_url_entry.delete(0, tk.END)
            self.rss_url_entry.insert(0, last_url)
            self.fetch_podcast_thread() 

        last_index = self.settings.get('last_playlist_index', -1)
        if self.playlist and 0 <= last_index < len(self.playlist):
            self.current_index = last_index
            track = self.playlist[self.current_index]

            self.playlist_listbox.selection_clear(0, tk.END)
            self.playlist_listbox.selection_set(self.current_index)
            self.playlist_listbox.see(self.current_index)
            self.current_title_label.config(text=track.get('title', '無標題'))
            
            self.duration = track.get('duration', 0)
            self.duration_label.config(text=self.format_time(self.duration))

    def init_player(self):
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.init()
            if not pygame.mixer.get_init(): raise Exception("Pygame mixer 初始化失敗")
            print("Pygame mixer 初始化成功")
        except Exception as e:
            messagebox.showerror("錯誤", f"Pygame 初始化失敗: {e}")
    
    def export_playlist(self):
        if self.is_loading:
            return
            
        if not self.playlist:
            messagebox.showinfo("提示", "播放清單為空，沒有內容可匯出。")
            return
        
        filepath = filedialog.asksaveasfilename(
            title="匯出播放清單",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("所有檔案", "*.*")],
            initialdir=self.script_dir,
            initialfile="my_playlist.json"
        )
        
        if not filepath:
            return
        
        try:
            export_data = {
                "version": "1.0",
                "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "playlist_count": len(self.playlist),
                "playlist": self.playlist
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("成功", f"播放清單已匯出至:\n{filepath}\n共 {len(self.playlist)} 個項目")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出播放清單失敗:\n{e}")

    def import_playlist(self):
        if self.is_loading:
            return
        
        if self.playlist:
            if not messagebox.askyesno("警告", 
                                       f"目前播放清單有 {len(self.playlist)} 個項目。\n"
                                       "匯入將會覆蓋目前的播放清單，確定繼續嗎？"):
                return
        
        filepath = filedialog.askopenfilename(
            title="匯入播放清單",
            filetypes=[("JSON files", "*.json"), ("所有檔案", "*.*")],
            initialdir=self.script_dir
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if isinstance(imported_data, dict) and 'playlist' in imported_data:
                playlist_data = imported_data['playlist']
                version = imported_data.get('version', '未知')
                export_time = imported_data.get('export_time', '未知')
            elif isinstance(imported_data, list):
                playlist_data = imported_data
                version = '舊版'
                export_time = '未知'
            else:
                raise TypeError("無法識別的檔案格式。檔案必須包含有效的播放清單資料。")
            
            if not isinstance(playlist_data, list):
                raise TypeError("播放清單資料格式錯誤，必須是陣列格式。")
            
            valid_items = []
            for i, item in enumerate(playlist_data):
                if not isinstance(item, dict):
                    print(f"跳過第 {i+1} 個無效項目：不是字典格式")
                    continue
                
                if 'title' not in item or 'url' not in item:
                    print(f"跳過第 {i+1} 個無效項目：缺少必要欄位 (title, url)")
                    continue
                
                valid_item = {
                    'title': item.get('title', '無標題'),
                    'url': item.get('url', ''),
                    'duration': item.get('duration', 0)
                }
                
                valid_items.append(valid_item)
            
            if not valid_items:
                raise ValueError("檔案中沒有找到有效的播放項目。")
            
            if self.is_playing:
                self.stop()
            
            self.playlist = valid_items
            self.current_index = 0
            
            self.playlist_listbox.delete(0, tk.END)
            for track in self.playlist:
                self.playlist_listbox.insert(tk.END, track.get('title', '無標題'))
            
            self.save_history()
            
            messagebox.showinfo("匯入成功", 
                               f"已成功匯入 {len(valid_items)} 個播放項目\n\n"
                               f"檔案版本: {version}\n"
                               f"匯出時間: {export_time}")
            
        except FileNotFoundError:
            messagebox.showerror("錯誤", "找不到指定的檔案。")
        except json.JSONDecodeError as e:
            messagebox.showerror("錯誤", f"JSON 檔案格式錯誤:\n{e}")
        except (TypeError, ValueError) as e:
            messagebox.showerror("錯誤", f"檔案格式不正確:\n{e}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入播放清單失敗:\n{e}")

    def create_widgets(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        stations_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="電台管理", menu=stations_menu)
        stations_menu.add_command(label="匯入電台列表...", command=self.import_stations)
        stations_menu.add_command(label="匯出電台列表...", command=self.export_stations)
        stations_menu.add_separator()
        stations_menu.add_command(label="清除所有電台", command=self.clear_all_stations)
        
        history_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="播放歷史", menu=history_menu)
        history_menu.add_command(label="匯入播放清單...", command=self.import_playlist)
        history_menu.add_command(label="匯出播放清單...", command=self.export_playlist)
        history_menu.add_separator()
        history_menu.add_command(label="清除播放歷史", command=self.clear_history)

        main_paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_frame = ttk.Frame(main_paned_window, padding=5)
        main_paned_window.add(left_frame, weight=2)

        stations_frame = ttk.LabelFrame(left_frame, text="我的電台", padding=5)
        stations_frame.pack(fill=tk.X, pady=(0, 10))
        self.station_combobox = ttk.Combobox(stations_frame, state="readonly")
        self.station_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.station_combobox.bind("<<ComboboxSelected>>", self.on_station_select)

        rss_frame = ttk.LabelFrame(left_frame, text="Podcast RSS Feed URL", padding=5)
        rss_frame.pack(fill=tk.X, pady=(0, 10))
        self.rss_url_entry = ttk.Entry(rss_frame)
        self.rss_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.fetch_button = ttk.Button(rss_frame, text="讀取", command=self.fetch_podcast_thread)
        self.fetch_button.pack(side=tk.LEFT)
        
        station_actions_frame = ttk.Frame(left_frame)
        station_actions_frame.pack(fill=tk.X, pady=5)
        
        self.save_station_button = ttk.Button(station_actions_frame, text="儲存目前電台到我的最愛", command=self.save_current_station, state=tk.DISABLED)
        self.save_station_button.pack(fill=tk.X, pady=(0, 5))
        
        self.delete_station_button = ttk.Button(station_actions_frame, text="從我的最愛刪除目前電台", command=self.delete_current_station, state=tk.DISABLED)
        self.delete_station_button.pack(fill=tk.X)

        self.podcast_title_label = ttk.Label(left_frame, text="尚未讀取節目", font=("Arial", 14, "bold"), wraplength=400)
        self.podcast_title_label.pack(fill=tk.X, pady=5)
        full_title_frame = ttk.LabelFrame(left_frame, text="單集完整標題", padding=5)
        full_title_frame.pack(fill=tk.X, pady=(0, 5))
        self.full_title_display_label = ttk.Label(full_title_frame, text="點擊下方列表中的單集以在此查看完整標題", wraplength=300, anchor=tk.W, justify=tk.LEFT, foreground="blue")
        self.full_title_display_label.pack(fill=tk.X, expand=True, pady=5, padx=5)
        
        playlist_frame = ttk.LabelFrame(left_frame, text="播放清單 (歷史紀錄)", padding="5")
        playlist_frame.pack(fill=tk.BOTH, expand=True)
        self.playlist_listbox = tk.Listbox(playlist_frame, height=8)
        self.playlist_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        playlist_scrollbar = ttk.Scrollbar(playlist_frame, orient=tk.VERTICAL, command=self.playlist_listbox.yview)
        self.playlist_listbox.configure(yscrollcommand=playlist_scrollbar.set)
        playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlist_listbox.bind('<Double-1>', self.play_from_playlist_double_click)

        right_frame = ttk.Frame(main_paned_window, padding=5)
        main_paned_window.add(right_frame, weight=3)
        
        episodes_frame = ttk.LabelFrame(right_frame, text="單集列表", padding=5)
        episodes_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        cols = ("#1", "#2")
        self.episodes_tree = ttk.Treeview(episodes_frame, columns=cols, show='headings', selectmode='browse')
        self.episodes_tree.heading("#1", text="發布日期"); self.episodes_tree.column("#1", width=100, anchor=tk.W)
        self.episodes_tree.heading("#2", text="單集標題"); self.episodes_tree.column("#2", width=300, anchor=tk.W)
        tree_scrollbar = ttk.Scrollbar(episodes_frame, orient=tk.VERTICAL, command=self.episodes_tree.yview)
        self.episodes_tree.configure(yscrollcommand=tree_scrollbar.set)
        self.episodes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.episodes_tree.bind('<Double-1>', self.on_episode_double_click)
        self.episodes_tree.bind('<<TreeviewSelect>>', self.on_episode_select)
        
        controls_frame = ttk.Frame(right_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        self.current_title_label = ttk.Label(controls_frame, text="無", font=("Arial", 10, "bold"), wraplength=350)
        self.current_title_label.pack(fill=tk.X)
        progress_frame = ttk.Frame(controls_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        self.time_label = ttk.Label(progress_frame, text="00:00"); self.time_label.pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar()
        self.progress_scale = ttk.Scale(progress_frame, from_=0, to=100, variable=self.progress_var, orient=tk.HORIZONTAL, command=self.seek)
        self.progress_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.duration_label = ttk.Label(progress_frame, text="00:00"); self.duration_label.pack(side=tk.RIGHT)
        
        buttons_frame = ttk.Frame(controls_frame); buttons_frame.pack()
        self.previous_button = ttk.Button(buttons_frame, text="上一首", command=self.previous_track)
        self.previous_button.pack(side=tk.LEFT)
        self.play_button = ttk.Button(buttons_frame, text="播放", command=self.toggle_play)
        self.play_button.pack(side=tk.LEFT)
        self.next_button = ttk.Button(buttons_frame, text="下一首", command=self.next_track)
        self.next_button.pack(side=tk.LEFT)
        self.stop_button = ttk.Button(buttons_frame, text="停止", command=self.stop)
        self.stop_button.pack(side=tk.LEFT)

        volume_frame = ttk.Frame(controls_frame); volume_frame.pack(fill=tk.X, pady=5)
        ttk.Label(volume_frame, text="音量:").pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=self.volume * 100)
        self.volume_scale = ttk.Scale(volume_frame, from_=0, to=100, variable=self.volume_var, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.volume_label = ttk.Label(volume_frame, text=f"{int(self.volume*100)}%"); self.volume_label.pack(side=tk.LEFT)

    def set_controls_state(self, is_enabled):
        state = tk.NORMAL if is_enabled else tk.DISABLED
        self.play_button.config(state=state)
        self.previous_button.config(state=state)
        self.next_button.config(state=state)
        self.stop_button.config(state=state)

    def load_stations(self):
        if not os.path.exists(self.stations_file): return
        try:
            with open(self.stations_file, 'r', encoding='utf-8') as f:
                self.my_stations = json.load(f)
            self.update_station_combobox()
            print(f"已載入 {len(self.my_stations)} 個電台。")
        except Exception as e:
            print(f"載入電台列表失敗: {e}")

    def save_stations(self):
        try:
            with open(self.stations_file, 'w', encoding='utf-8') as f:
                json.dump(self.my_stations, f, ensure_ascii=False, indent=4)
            print("電台列表已儲存。")
        except Exception as e:
            print(f"儲存電台列表失敗: {e}")

    def export_stations(self):
        if self.is_loading: return
        if not self.my_stations:
            messagebox.showinfo("提示", "沒有電台可匯出。")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            initialdir=self.script_dir
        )
        if not filepath: return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.my_stations, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("成功", f"電台列表已匯出至:\n{filepath}")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯出失敗: {e}")

    def import_stations(self):
        if self.is_loading: return
        if self.my_stations and not messagebox.askyesno("警告", "匯入將會覆蓋目前的電台列表，確定嗎？"):
            return
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            initialdir=self.script_dir
        )
        if not filepath: return
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_stations = json.load(f)
            if not isinstance(imported_stations, dict):
                raise TypeError("檔案格式需為 JSON 物件 (字典)。")
            self.my_stations = imported_stations
            self.update_station_combobox()
            self.save_stations()
            messagebox.showinfo("成功", f"已成功匯入 {len(self.my_stations)} 個電台。")
        except Exception as e:
            messagebox.showerror("錯誤", f"匯入失敗: {e}")

    def update_station_combobox(self):
        self.station_combobox['values'] = list(self.my_stations.keys())
        self.station_combobox.set('')

    def save_current_station(self):
        if self.is_loading: return
        if not self.podcast_data or 'title' not in self.podcast_data:
            messagebox.showwarning("提示", "沒有可儲存的電台資訊。")
            return
        
        station_name = self.podcast_data['title']
        station_url = self.podcast_data['feed_url']
        
        if messagebox.askyesno("確認", f"要將 '{station_name}' 加入到我的電台嗎？"):
            self.my_stations[station_name] = station_url
            self.save_stations()
            self.update_station_combobox()
            values = list(self.my_stations.keys())
            if station_name in values:
                self.station_combobox.set(station_name)
            self.update_station_buttons_state()
            messagebox.showinfo("成功", f"'{station_name}' 已儲存！")

    def delete_current_station(self):
        if self.is_loading: return
        if not self.podcast_data or 'title' not in self.podcast_data:
            return

        station_name = self.podcast_data['title']
        if station_name not in self.my_stations:
            messagebox.showwarning("提示", f"電台 '{station_name}' 不在您的最愛列表中。")
            return

        if messagebox.askyesno("確認刪除", f"確定要從我的最愛刪除 '{station_name}' 嗎？\n此操作無法復原。"):
            del self.my_stations[station_name]
            self.save_stations()
            self.update_station_combobox()
            self.update_station_buttons_state()
            messagebox.showinfo("完成", f"'{station_name}' 已從您的最愛刪除。")

    def update_station_buttons_state(self):
        if not self.podcast_data or 'title' not in self.podcast_data:
            self.save_station_button.config(state=tk.DISABLED)
            self.delete_station_button.config(state=tk.DISABLED)
            return

        station_name = self.podcast_data['title']
        if station_name in self.my_stations:
            self.save_station_button.config(state=tk.DISABLED)
            self.delete_station_button.config(state=tk.NORMAL)
        else:
            self.save_station_button.config(state=tk.NORMAL)
            self.delete_station_button.config(state=tk.DISABLED)

    def on_station_select(self, event):
        if self.is_loading: return
        selected_station = self.station_combobox.get()
        if selected_station in self.my_stations:
            rss_url = self.my_stations[selected_station]
            self.rss_url_entry.delete(0, tk.END)
            self.rss_url_entry.insert(0, rss_url)
            self.fetch_podcast_thread()

    def fetch_podcast_thread(self):
        if self.is_loading: return
        rss_url = self.rss_url_entry.get().strip()
        if not rss_url: messagebox.showwarning("警告", "請輸入 RSS Feed URL"); return
        self.fetch_button.config(state=tk.DISABLED)
        self.podcast_title_label.config(text=f"正在讀取: {rss_url}...")
        self.save_station_button.config(state=tk.DISABLED)
        self.delete_station_button.config(state=tk.DISABLED)
        threading.Thread(target=self.fetch_podcast, args=(rss_url,), daemon=True).start()

    def fetch_podcast(self, rss_url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(rss_url, headers=headers, timeout=20)
            response.raise_for_status()
            parsed_feed = feedparser.parse(response.content)
            if parsed_feed.bozo: raise Exception(f"RSS 解析錯誤: {parsed_feed.bozo_exception}")
            
            self.podcast_data = {
                'title': parsed_feed.feed.get('title', '無標題'), 'feed_url': rss_url, 'episodes': [] }
            for entry in parsed_feed.entries:
                audio_url = next((enclosure.href for enclosure in entry.get('enclosures', []) if 'audio' in enclosure.get('type', '')), None)
                if audio_url:
                    self.podcast_data['episodes'].append({
                        'title': entry.get('title', '無標題單集'), 'published': entry.get('published', ''),
                        'summary': entry.get('summary', '無摘要'), 'audio_url': audio_url,
                        'duration': entry.get('itunes_duration', '0')
                    })
            self.root.after(0, self.update_podcast_gui)
        except Exception as e:
            error_message = f"讀取失敗: {e}"
            self.root.after(0, lambda: self.podcast_title_label.config(text="讀取失敗"))
            self.root.after(0, lambda err=error_message: messagebox.showerror("錯誤", err))
        finally:
            try:
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.fetch_button.config(state=tk.NORMAL))
                    self.root.after(0, self.update_station_buttons_state)
            except RuntimeError:
                print("背景執行緒嘗試更新已關閉的視窗，已安全忽略。")

    def update_podcast_gui(self):
        for i in self.episodes_tree.get_children(): self.episodes_tree.delete(i)
        self.podcast_title_label.config(text=self.podcast_data['title'])
        self.full_title_display_label.config(text="點擊下方列表中的單集以在此查看完整標題")
        for i, episode in enumerate(self.podcast_data['episodes']):
            try:
                date_str = episode['published']
                for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
                    try:
                        parsed_time = time.strptime(date_str, fmt)
                        date_str = time.strftime("%Y-%m-%d", parsed_time)
                        break
                    except ValueError: continue
                else: date_str = episode['published'].split(' ')[0]
            except (ValueError, TypeError): date_str = episode['published'].split(' ')[0]
            self.episodes_tree.insert('', tk.END, iid=i, values=(date_str, episode['title']))

    def on_episode_double_click(self, event):
        selected_items = self.episodes_tree.selection()
        if not selected_items: return
        item_id = int(selected_items[0])
        episode_data = self.podcast_data['episodes'][item_id]
        
        duration_str = str(episode_data['duration'])
        duration_sec = 0
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 3: duration_sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2: duration_sec = int(parts[0]) * 60 + int(parts[1])
        elif duration_str.isdigit(): duration_sec = int(duration_str)

        track_info = {'title': episode_data['title'], 'url': episode_data['audio_url'], 'duration': duration_sec}
        self.playlist = [t for t in self.playlist if t['url'] != track_info['url']]
        self.playlist.insert(0, track_info)
        
        self.playlist_listbox.delete(0, tk.END)
        for t in self.playlist: self.playlist_listbox.insert(tk.END, t['title'])
        
        self.current_index = 0
        self.play_current_track()

    def on_episode_select(self, event):
        if self.is_loading: return
        selected_items = self.episodes_tree.selection()
        if not selected_items: return
        item_id = int(selected_items[0])
        if self.podcast_data and len(self.podcast_data['episodes']) > item_id:
            episode_data = self.podcast_data['episodes'][item_id]
            full_title = episode_data.get('title', '無標題')
            self.full_title_display_label.config(text=full_title)

    def play_current_track(self):
        if not self.playlist: return

        # <--- 修正點：如果前一個單集正在加載中，顯示取消訊息，給予使用者即時反饋
        if self.is_loading:
            self.current_title_label.config(text="下載未完成：因使用者有其他按鍵取消")
            self.root.update_idletasks() # 強制UI立即刷新以顯示此訊息
        
        self.is_loading = True
        self.set_controls_state(False)
        self.stop()
        
        self.play_request_id += 1
        current_request_id = self.play_request_id
        
        track = self.playlist[self.current_index]
        self.current_title_label.config(text=f"載入中: {track['title']}")
        threading.Thread(target=self.play_track, args=(track, current_request_id), daemon=True).start()

    def play_track(self, track, request_id):
        private_temp_dir = tempfile.mkdtemp()
        old_temp_dir_to_clean = None
        
        try:
            response = requests.get(track['url'], stream=True); response.raise_for_status()
            temp_mp3 = os.path.join(private_temp_dir, "audio.mp3")
            with open(temp_mp3, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if request_id != self.play_request_id:
                        print(f"下載被請求 {self.play_request_id} 中斷 (原為 {request_id})")
                        raise InterruptedError("Playback cancelled by new request")
                    f.write(chunk)
            
            if request_id != self.play_request_id:
                raise InterruptedError("Playback cancelled by new request")

            if not self.check_ffmpeg(): raise Exception("未在系統中找到 FFmpeg，無法轉檔。")

            temp_wav = os.path.join(private_temp_dir, "audio.wav")
            cmd = ['ffmpeg', '-i', temp_mp3, '-y', temp_wav]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            if result.returncode != 0: raise Exception(f"FFmpeg 轉檔失敗:\n{result.stderr}")
            if not os.path.exists(temp_wav) or os.path.getsize(temp_wav) == 0:
                raise Exception("FFmpeg 執行完畢，但未產生有效的音訊檔。")

            if request_id != self.play_request_id:
                raise InterruptedError("Playback cancelled by new request")

            old_temp_dir_to_clean = self.current_temp_dir
            self.current_temp_dir = private_temp_dir

            pygame.mixer.music.load(temp_wav)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play()
            
            self.is_playing = True; self.is_paused = False; self.current_pos = 0
            self.duration = track.get('duration', 0)
            self.root.after(0, self.update_play_ui, track)
            self.save_history()
            
            if old_temp_dir_to_clean and os.path.exists(old_temp_dir_to_clean):
                shutil.rmtree(old_temp_dir_to_clean, ignore_errors=True)

        except InterruptedError as e:
            print(f"請求 {request_id} 已成功取消: {e}")
            shutil.rmtree(private_temp_dir, ignore_errors=True)
            if request_id == self.play_request_id:
                 self.root.after(0, self.stop)
        except Exception:
            error_info = traceback.format_exc()
            self.root.after(0, lambda: messagebox.showerror("錯誤", f"播放失敗:\n{error_info}"))
            shutil.rmtree(private_temp_dir, ignore_errors=True)
        finally:
            if request_id == self.play_request_id:
                self.is_loading = False
                self.root.after(0, self.set_controls_state, True)

    def update_play_ui(self, track):
        self.current_title_label.config(text=track['title'])
        self.play_button.config(text="暫停")
        self.playlist_listbox.selection_clear(0, tk.END)
        self.playlist_listbox.selection_set(self.current_index)
        self.playlist_listbox.see(self.current_index)
    
    def play_from_playlist_double_click(self, event):
        selection = self.playlist_listbox.curselection()
        if selection:
            self.current_index = selection[0]
            self.play_current_track()

    def toggle_play(self):
        if self.is_loading:
            return
            
        if not pygame.mixer.get_init(): return
        
        if not self.is_playing:
            if self.playlist: self.play_current_track()
        else:
            if self.is_paused:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.play_button.config(text="暫停")
            else:
                pygame.mixer.music.pause()
                self.is_paused = True
                self.play_button.config(text="播放")

    def stop(self):
        if not pygame.mixer.get_init(): return
        self.play_request_id += 1
        pygame.mixer.music.stop()
        self.is_playing = False; self.is_paused = False; self.current_pos = 0
        self.play_button.config(text="播放"); self.current_title_label.config(text="無")
        self.progress_var.set(0); self.time_label.config(text="00:00")
        if self.is_loading:
            self.is_loading = False
            self.set_controls_state(True)

    def next_track(self):
        if self.is_loading: return
        if self.playlist and self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.play_current_track()

    def previous_track(self):
        if self.is_loading: return
        if self.playlist and self.current_index > 0:
            self.current_index -= 1
            self.play_current_track()

    def set_volume(self, value):
        self.volume = float(value) / 100
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)
        self.volume_label.config(text=f"{int(float(value))}%")
    
    def seek(self, value):
        if self.is_playing and self.duration > 0:
            seek_pos = (float(value) / 100) * self.duration
            pygame.mixer.music.set_pos(seek_pos)
            self.current_pos = seek_pos

    def update_progress(self):
        while True:
            try:
                if self.root.winfo_exists():
                    if self.is_playing and not self.is_paused:
                        if pygame.mixer.music.get_busy():
                            self.current_pos = pygame.mixer.music.get_pos() / 1000
                            if self.duration > 0:
                                self.progress_var.set((self.current_pos / self.duration) * 100)
                            else:
                                self.progress_var.set(0)
                        elif self.current_pos > 0:
                            time.sleep(0.5) 
                            if not pygame.mixer.music.get_busy():
                                self.root.after(0, self.next_track)
                                self.current_pos = 0
                        
                        self.time_label.config(text=self.format_time(self.current_pos))
                        self.duration_label.config(text=self.format_time(self.duration))
                time.sleep(1)
            except Exception as e:
                if isinstance(e, tk.TclError):
                    break

    def format_time(self, seconds):
        if not isinstance(seconds, (int, float)) or seconds < 0: return "00:00"
        return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"

    def check_ffmpeg(self):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, creationflags=creationflags)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError): return False

    def save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlist, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"儲存播放歷史失敗: {e}")

    def load_history(self):
        if not os.path.exists(self.history_file): return
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.playlist = json.load(f)
            self.playlist_listbox.delete(0, tk.END)
            for track in self.playlist:
                self.playlist_listbox.insert(tk.END, track.get('title', '無標題'))
        except Exception as e:
            print(f"載入播放歷史失敗: {e}")
            self.playlist = []

    def clear_history(self):
        if self.is_loading: return
        if not messagebox.askyesno("確認", "確定要清除所有播放歷史嗎？"): return
        self.stop()
        self.playlist = []
        self.playlist_listbox.delete(0, tk.END)
        if os.path.exists(self.history_file):
            try:
                os.remove(self.history_file)
                messagebox.showinfo("完成", "播放歷史已被清除。")
            except OSError as e:
                messagebox.showerror("錯誤", f"無法清除歷史紀錄檔案:\n{e}")

    def clear_all_stations(self):
        if self.is_loading: return
        if not messagebox.askyesno("確認", "確定要清除所有已儲存的電台嗎？"): return
        self.my_stations = {}
        self.save_stations()
        self.update_station_combobox()
        self.update_station_buttons_state()
        messagebox.showinfo("完成", "所有電台已被清除。")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = PodcastPlayer(root)
        
        def on_closing():
            app.save_window_settings()
            if app.current_temp_dir and os.path.exists(app.current_temp_dir):
                shutil.rmtree(app.current_temp_dir, ignore_errors=True)
            root.destroy()
            
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    except Exception as e:
        traceback.print_exc()
        input("按 Enter 鍵退出...")
