import datetime
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import webbrowser
from pathlib import Path

try:
    from ttkthemes import ThemedTk
    HAS_THEMES = True
except ImportError:
    HAS_THEMES = False

try:
    from plyer import notification
    HAS_NOTIFICATIONS = True
except ImportError:
    HAS_NOTIFICATIONS = False

from .settings import Settings
from .downloader import VideoDownloader
from .i18n import get_translator
from .utils import ToolTip, is_valid_url

APP_NAME = "Moaz Video Downloader"
APP_VERSION = "1.0"

class DownloaderGUI:
    """Tkinter-based GUI for the downloader, with post-processing plugin support."""
    def __init__(self, settings: Settings, downloader: VideoDownloader, icon_path: str, ffmpeg_path: str):
        self.settings = settings
        self.downloader = downloader
        self.icon_path = icon_path
        self.ffmpeg_path = ffmpeg_path
        self.language = self.settings.data.get('language', 'en')
        self.t = get_translator(self.language)

        if HAS_THEMES:
            self.root = ThemedTk(theme="arc")
        else:
            self.root = tk.Tk()
            
        self.root.title(f"{self.t('title')} v{APP_VERSION}")
        self.root.geometry('800x600')
        self.root.minsize(700, 500)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self._init_vars()

        self.setup_ui()
        self.language_var.set(self.language_code_to_short.get(self.language, 'En'))
        self.apply_theme()
        self.check_dependencies()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        try:
            if self.icon_path and os.path.exists(self.icon_path):
                self.root.iconbitmap(self.icon_path)
        except tk.TclError:
            print("Note: .ico files are only supported on Windows.")

        if self.ffmpeg_path is None:
            # Schedule the messagebox to appear after the main window is fully drawn
            self.root.after(100, lambda: messagebox.showerror(self.t('error'), self.t('ffmpeg_missing')))

    def _init_vars(self):
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=self.settings.data.get("output_dir", str(Path.home() / "Downloads")))
        self.single_quality_var = tk.StringVar(value="best")
        self.batch_quality_var = tk.StringVar(value="best")
        self.audio_only_var = tk.BooleanVar()
        self.playlist_var = tk.BooleanVar(value=self.settings.data.get("playlist", False))
        self.progress_text = tk.StringVar(value=self.t("ready"))
        self.progress_percent = tk.StringVar(value="0%")
        self.parallel_var = tk.IntVar(value=self.settings.data.get('parallel', 2))
        self.theme_var = tk.StringVar(value=self.settings.data.get('theme', 'light'))
        self.format_var = tk.StringVar(value=self.settings.data.get('format', 'mp4'))
        self.custom_format_var = tk.StringVar(value=self.settings.data.get('custom_format', ''))
        self.cookie_file_var = tk.StringVar(value=self.settings.data.get('cookie_file', ''))
        self.proxy_var = tk.StringVar(value=self.settings.data.get('proxy', ''))
        self.enable_notifications_var = tk.BooleanVar(value=self.settings.data.get('enable_notifications', True))
        self.log_level_var = tk.StringVar(value=self.settings.data.get('log_level', 'INFO'))
        self.file_template_var = tk.StringVar(value=self.settings.data.get('file_template', '%(uploader)s - %(id)s.%(ext)s'))
        self.user_agent_var = tk.StringVar(value=self.settings.data.get('user_agent', ''))
        self.bandwidth_var = tk.StringVar(value=self.settings.data.get('bandwidth', ''))
        self.plugin_dir_var = tk.StringVar(value=self.settings.data.get('plugin_dir', ''))
        self.skip_downloaded_var = tk.BooleanVar(value=self.settings.data.get('skip_downloaded', True))
        
        self.log_lines = []
        self.recent_urls = self.settings.data.get('recent_urls', [])
        self.recent_batch_files = self.settings.data.get('recent_batch_files', [])
        self.download_threads = []
        self.cancel_requested = False
        
        self.language_var = tk.StringVar(value=self.language)
        self.language_short_names = ['En', 'Es', 'Fr', 'De', 'It', 'Pt', 'Ru', 'Zh', 'Ja', 'Ar']
        self.language_short_to_code = dict(zip(self.language_short_names, ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'zh', 'ja', 'ar']))
        self.language_code_to_short = {v: k for k, v in self.language_short_to_code.items()}

        self._update_quality_maps()

    def _update_quality_maps(self):
        self.quality_value_map = {
            self.t('best'): 'best', self.t('worst'): 'worst', '1080p': '1080p', '720p': '720p',
            '480p': '480p', '360p': '360p', '240p': '240p',
        }
        self.quality_display_map = {v: k for k, v in self.quality_value_map.items()}

    def setup_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        self.nb = ttk.Notebook(main_frame)
        self.nb.grid(row=0, column=0, sticky="nsew")

        self._setup_download_tab()
        self._setup_batch_tab()
        self._setup_settings_tab()
        self._setup_history_tab()
        self._setup_recent_tab()
        self._setup_menu()
        self._setup_statusbar()
        self._add_tooltips()

    def _setup_download_tab(self):
        self.download_group = ttk.LabelFrame(self.nb, text=self.t('download'), padding=0)
        self.nb.add(self.download_group, text=self.t('download'))
        
        self.download_bg_frame = tk.Frame(self.download_group, bd=0, highlightthickness=0)
        self.download_bg_frame.pack(fill=tk.BOTH, expand=True)
        self.download_bg_frame.pack_propagate(0)
        self.download_bg_frame.grid_columnconfigure(1, weight=1)

        self.url_label = ttk.Label(self.download_bg_frame, text=self.t('url_label'))
        self.url_label.grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.url_entry = ttk.Entry(self.download_bg_frame, textvariable=self.url_var, width=60)
        self.url_entry.grid(row=0, column=1, sticky=tk.EW, pady=5, padx=5)

        self.detect_formats_btn = ttk.Button(self.download_bg_frame, text=self.t('detect_formats'), command=self.detect_formats)
        self.detect_formats_btn.grid(row=0, column=2, padx=5)

        self.recent_combo = ttk.Combobox(self.download_bg_frame, values=self.recent_urls, postcommand=self.update_recent_urls)
        self.recent_combo.grid(row=0, column=3, sticky=tk.W, padx=5)
        self.recent_combo.bind('<<ComboboxSelected>>', self.select_recent_url)

        self.quality_label = ttk.Label(self.download_bg_frame, text=self.t('quality'))
        self.quality_label.grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.quality_combo = ttk.Combobox(self.download_bg_frame, textvariable=self.single_quality_var, values=list(self.quality_value_map.keys()), width=15, state="readonly")
        self.quality_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.output_dir_label = ttk.Label(self.download_bg_frame, text=self.t('output_dir_label'))
        self.output_dir_label.grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.output_dir_entry = ttk.Entry(self.download_bg_frame, textvariable=self.output_dir_var, width=40)
        self.output_dir_entry.grid(row=3, column=1, sticky=tk.EW, pady=5, padx=5)
        self.browse_dir_btn = ttk.Button(self.download_bg_frame, text=self.t('browse'), command=self.browse_dir)
        self.browse_dir_btn.grid(row=3, column=2, padx=5)

        self.audio_only_cb = ttk.Checkbutton(self.download_bg_frame, text=self.t('audio_only'), variable=self.audio_only_var, command=self.on_audio_only_toggle)
        self.audio_only_cb.grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
        self.playlist_cb = ttk.Checkbutton(self.download_bg_frame, text=self.t('playlist'), variable=self.playlist_var)
        self.playlist_cb.grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)

        self.button_frame = ttk.Frame(self.download_bg_frame)
        self.button_frame.grid(row=7, column=1, pady=10, columnspan=2)
        self.download_btn = ttk.Button(self.button_frame, text=self.t('download'), command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        self.cancel_btn = ttk.Button(self.button_frame, text=self.t('cancel'), command=self.cancel_download, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = ttk.Label(self.download_bg_frame, text=self.t('status'))
        self.status_label.grid(row=8, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Label(self.download_bg_frame, textvariable=self.progress_text, foreground="blue").grid(row=8, column=1, sticky=tk.W, pady=5, padx=5)
        
        self.progress_canvas = tk.Canvas(self.download_bg_frame, height=20, width=300, highlightthickness=0, bd=0)
        self.progress_canvas.grid(row=9, column=1, columnspan=3, sticky=tk.W, pady=5, padx=5)
        self.draw_progress_bar(0)
        
        self.output_text = scrolledtext.ScrolledText(self.download_bg_frame, height=8, width=80, wrap=tk.WORD)
        self.output_text.grid(row=11, column=0, columnspan=4, sticky=tk.EW, pady=5, padx=5)

    def _setup_batch_tab(self):
        batch_frame = ttk.Frame(self.nb, padding=10)
        self.nb.add(batch_frame, text=self.t('batch_download'))
        batch_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(batch_frame, text=self.t('batch_urls_label')).grid(row=0, column=0, sticky=tk.NW, pady=5)
        self.batch_text = scrolledtext.ScrolledText(batch_frame, height=10, width=80, wrap=tk.WORD)
        self.batch_text.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=5)
        batch_frame.grid_rowconfigure(1, weight=1)
        
        ttk.Button(batch_frame, text=self.t('load_from_file'), command=self.load_batch_file).grid(row=2, column=0, pady=5, sticky=tk.W)

        options_frame = ttk.Frame(batch_frame)
        options_frame.grid(row=3, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        ttk.Label(options_frame, text=self.t('quality')).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.batch_quality_combo = ttk.Combobox(options_frame, textvariable=self.batch_quality_var, values=list(self.quality_value_map.keys()), state="readonly", width=15)
        self.batch_quality_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(options_frame, text=f"{self.t('parallel_downloads')}:").grid(row=0, column=2, sticky=tk.W, padx=10)
        ttk.Scale(options_frame, from_=1, to=10, orient=tk.HORIZONTAL, variable=self.parallel_var, length=120).grid(row=0, column=3, sticky=tk.W)
        ttk.Label(options_frame, textvariable=self.parallel_var).grid(row=0, column=4, sticky=tk.W, padx=5)
        
        self.batch_download_btn = ttk.Button(batch_frame, text=self.t('batch_download'), command=self.start_batch_download)
        self.batch_download_btn.grid(row=4, column=0, columnspan=3, pady=10)

    def _setup_settings_tab(self):
        self.settings_frame = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.settings_frame, text=self.t('settings'))
        
        # Using a scrolled frame for better layout management
        canvas = tk.Canvas(self.settings_frame)
        scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        row = 0
        
        # Theme and Language
        ttk.Label(scrollable_frame, text=self.t('theme')).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        themes = ['light', 'dark', 'arc', 'black', 'equilux', 'scidpink', 'scidgreen', 'smog', 'alt', 'itft1', 'xpnative', 'clearlooks']
        self.theme_combo = ttk.Combobox(scrollable_frame, textvariable=self.theme_var, values=themes, state="readonly")
        self.theme_combo.grid(row=row, column=1, sticky=tk.EW, pady=2, padx=5)
        self.theme_combo.bind('<<ComboboxSelected>>', self.change_theme)
        row += 1
        
        ttk.Label(scrollable_frame, text=self.t('language')).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        self.lang_combo = ttk.Combobox(scrollable_frame, textvariable=self.language_var, values=self.language_short_names, state='readonly')
        self.lang_combo.grid(row=row, column=1, sticky=tk.EW, pady=2, padx=5)
        self.lang_combo.bind('<<ComboboxSelected>>', self.change_language)
        row += 1

        # File and Network Settings
        ttk.Label(scrollable_frame, text=self.t('file_template_label')).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Entry(scrollable_frame, textvariable=self.file_template_var).grid(row=row, column=1, sticky=tk.EW, pady=2, padx=5)
        row += 1

        ttk.Label(scrollable_frame, text=self.t('cookie_file')).grid(row=row, column=0, sticky=tk.W, pady=2, padx=5)
        ttk.Entry(scrollable_frame, textvariable=self.cookie_file_var).grid(row=row, column=1, sticky=tk.EW, pady=2, padx=5)
        ttk.Button(scrollable_frame, text=self.t('browse'), command=lambda: self.browse_file(self.cookie_file_var)).grid(row=row, column=2, padx=5)
        row += 1

        # Other settings would follow here...
        
        ttk.Button(scrollable_frame, text=self.t('save'), command=self.save_settings).grid(row=row, column=1, pady=10)

    def _setup_history_tab(self):
        history_frame = ttk.Frame(self.nb, padding=10)
        self.nb.add(history_frame, text=self.t('history'))
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)
        self.history_text = scrolledtext.ScrolledText(history_frame, height=20, width=100, wrap=tk.WORD, state=tk.DISABLED)
        self.history_text.grid(row=0, column=0, sticky="nsew")
        self.clear_history_btn = ttk.Button(history_frame, text=self.t('clear_history'), command=self.clear_history)
        self.clear_history_btn.grid(row=1, column=0, pady=5)
        self.update_history()

    def _setup_recent_tab(self):
        recent_frame = ttk.Frame(self.nb, padding=10)
        self.nb.add(recent_frame, text=self.t('recent_downloads'))
        recent_frame.grid_rowconfigure(0, weight=1)
        recent_frame.grid_columnconfigure(0, weight=1)
        self.recent_listbox = tk.Listbox(recent_frame, height=10, activestyle='dotbox')
        self.recent_listbox.grid(row=0, column=0, sticky="nsew")
        self.recent_listbox.bind('<Double-Button-1>', self.open_recent_download)
        self.remove_recent_btn = ttk.Button(recent_frame, text=self.t('remove_recent_downloads'), command=self.remove_recent_downloads)
        self.remove_recent_btn.grid(row=1, column=0, pady=5)
        self.update_recent_downloads()

    def _setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.t('file'), menu=file_menu)
        file_menu.add_command(label=self.t('exit'), command=self.on_closing)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.t('tools'), menu=tools_menu)
        tools_menu.add_command(label=self.t('check_for_updates'), command=self.check_for_updates)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.t('help'), menu=help_menu)
        help_menu.add_command(label=self.t('about'), command=self.show_about)
        help_menu.add_command(label=self.t('visit_github'), command=lambda: webbrowser.open("https://github.com/moazmohamed24/Moaz-Downloader/"))

    def _setup_statusbar(self):
        self.status_message = tk.StringVar(value=self.t("ready"))
        status_bar = ttk.Label(self.root, textvariable=self.status_message, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        status_bar.grid(row=1, column=0, sticky="ew")

    def _add_tooltips(self):
        ToolTip(self.download_btn, self.t('tooltip_download'))
        ToolTip(self.cancel_btn, self.t('tooltip_cancel'))
        ToolTip(self.output_text, self.t('tooltip_log'))
        ToolTip(self.progress_canvas, self.t('tooltip_progress'))
        ToolTip(self.recent_combo, self.t('tooltip_recent'))
        ToolTip(self.batch_text, self.t('tooltip_batch_urls'))
        ToolTip(self.batch_download_btn, self.t('tooltip_batch_download'))
        ToolTip(self.theme_combo, self.t('tooltip_theme'))
        ToolTip(self.lang_combo, self.t('tooltip_language'))

    def apply_theme(self):
        style = ttk.Style()
        theme = self.theme_var.get()
        if HAS_THEMES and theme not in ['light', 'dark']:
            try:
                self.root.set_theme(theme)
                return
            except Exception:
                pass # Fallback to light/dark
        
        bg_color = '#2e2e2e' if theme == 'dark' else '#f0f0f0'
        fg_color = 'white' if theme == 'dark' else 'black'
        entry_bg = '#444444' if theme == 'dark' else 'white'
        
        self.root.configure(bg=bg_color)
        style.configure('.', background=bg_color, foreground=fg_color)
        style.configure('TFrame', background=bg_color)
        style.configure('TLabel', background=bg_color, foreground=fg_color)
        style.configure('TButton', background='#555555' if theme == 'dark' else '#e1e1e1', foreground=fg_color)
        style.map('TButton', background=[('active', '#666666' if theme == 'dark' else '#d4d4d4')])
        style.configure('TEntry', fieldbackground=entry_bg, foreground=fg_color)
        style.configure('TCombobox', fieldbackground=entry_bg, foreground=fg_color)
        style.configure('TCheckbutton', background=bg_color, foreground=fg_color)
        # Add more specific styling as needed...

    def change_language(self, event=None):
        lang_short = self.language_var.get()
        self.language = self.language_short_to_code.get(lang_short, 'en')
        self.settings.data['language'] = self.language
        self.t = get_translator(self.language)
        self.refresh_ui()
    
    def change_theme(self, event=None):
        self.settings.data['theme'] = self.theme_var.get()
        self.apply_theme()

    def save_settings(self):
        # General
        self.settings.data['language'] = self.language
        self.settings.data['theme'] = self.theme_var.get()
        self.settings.data['enable_notifications'] = self.enable_notifications_var.get()
        self.settings.data['log_level'] = self.log_level_var.get()
        
        # Download
        self.settings.data['output_dir'] = self.output_dir_var.get()
        self.settings.data['file_template'] = self.file_template_var.get()
        self.settings.data['playlist'] = self.playlist_var.get()
        self.settings.data['skip_downloaded'] = self.skip_downloaded_var.get()

        # Network
        self.settings.data['proxy'] = self.proxy_var.get()
        self.settings.data['user_agent'] = self.user_agent_var.get()
        self.settings.data['cookie_file'] = self.cookie_file_var.get()
        self.settings.data['bandwidth'] = self.bandwidth_var.get()
        
        # Advanced
        self.settings.data['plugin_dir'] = self.plugin_dir_var.get()

        self.settings.save()
        messagebox.showinfo(self.t('success'), self.t('settings_saved'))

    def refresh_ui(self):
        self.root.title(f"{self.t('title')} v{APP_VERSION}")
        self._update_quality_maps()
        # Refresh all widgets with translated text
        # This is extensive and needs to cover all translatable text widgets
        self.nb.tab(0, text=self.t('download'))
        self.nb.tab(1, text=self.t('batch_download'))
        self.nb.tab(2, text=self.t('settings'))
        self.nb.tab(3, text=self.t('history'))
        self.nb.tab(4, text=self.t('recent_downloads'))
        # ... and so on for all widgets. This is a large task.

    def start_download(self):
        url = self.url_var.get().strip()
        if not url or not is_valid_url(url):
            messagebox.showerror(self.t('error'), self.t('invalid_url'))
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror(self.t('error'), self.t('output_dir_missing'))
            return
        
        self.cancel_requested = False
        self.download_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.log_message(f"Starting download for: {url}")

        def progress_callback(msg):
            if self.cancel_requested:
                return False
            self.root.after(0, self.parse_progress, msg)
            return True

        def download_thread_func():
            success, final_path = self.downloader.download(
                url=url,
                output_dir=output_dir,
                quality=self.quality_value_map.get(self.single_quality_var.get(), 'best'),
                audio_only=self.audio_only_var.get(),
                playlist=self.playlist_var.get(),
                cookie_file=self.cookie_file_var.get(),
                progress_callback=progress_callback
            )
            self.root.after(0, self.on_download_complete, success, url, final_path)

        thread = threading.Thread(target=download_thread_func, daemon=True)
        thread.start()

    def start_batch_download(self):
        urls = [line.strip() for line in self.batch_text.get(1.0, tk.END).strip().split('\n') if is_valid_url(line.strip())]
        if not urls:
            messagebox.showerror(self.t('error'), self.t('no_valid_urls'))
            return

        output_dir = self.output_dir_var.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror(self.t('error'), self.t('output_dir_missing'))
            return
        
        self.log_message(f"Starting batch download of {len(urls)} URLs...")
        # Simplified batch download logic for now
        for url in urls:
            # This should be parallelized properly
            self.url_var.set(url)
            self.start_download()
            
    def on_download_complete(self, success, url, final_path):
        if self.cancel_requested:
            status = 'Cancelled'
            self.log_message("Download cancelled.")
        elif success:
            status = 'Success'
            self.log_message(f"Download completed: {final_path}")
            if self.enable_notifications_var.get() and HAS_NOTIFICATIONS:
                notification.notify(title=self.t('title'), message=self.t('notification_success'), app_name=APP_NAME)
        else:
            status = 'Failed'
            self.log_message("Download failed.")
            if self.enable_notifications_var.get() and HAS_NOTIFICATIONS:
                notification.notify(title=self.t('title'), message=self.t('notification_fail'), app_name=APP_NAME)

        self.settings.add_history({'time': datetime.datetime.now().isoformat(), 'url': url, 'status': status, 'path': final_path})
        self.update_history()
        self.update_recent_downloads()

        self.download_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)

    # All other helper methods...
    def cancel_download(self): self.cancel_requested = True
    def browse_dir(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory: self.output_dir_var.set(directory)
    def browse_file(self, var):
        filename = filedialog.askopenfilename()
        if filename: var.set(filename)
    def load_batch_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.batch_text.delete(1.0, tk.END)
                self.batch_text.insert(tk.END, f.read())

    def detect_formats(self):
        url = self.url_var.get().strip()
        if not is_valid_url(url): return
        formats = self.downloader.detect_formats(url)
        messagebox.showinfo(self.t('detected_formats'), '\n'.join(formats) if formats else self.t('no_formats_detected'))

    def update_history(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        for entry in self.settings.data.get('download_history', []):
            self.history_text.insert(tk.END, f"{entry.get('time', '')} | {entry.get('status', '')} | {entry.get('url', '')}\n")
        self.history_text.config(state=tk.DISABLED)

    def clear_history(self):
        self.settings.data['download_history'] = []
        self.settings.save()
        self.update_history()
    
    def update_recent_downloads(self):
        self.recent_listbox.delete(0, tk.END)
        for entry in self.settings.data.get('download_history', [])[:15]:
            if entry.get('path') and os.path.exists(entry['path']):
                self.recent_listbox.insert(tk.END, entry['path'])

    def remove_recent_downloads(self):
        selected_indices = self.recent_listbox.curselection()
        # This needs more logic to remove from settings data
        for i in reversed(selected_indices):
            self.recent_listbox.delete(i)

    def open_recent_download(self, event):
        try:
            filepath = self.recent_listbox.get(self.recent_listbox.curselection())
            webbrowser.open(os.path.dirname(filepath))
        except Exception:
            pass
    
    def select_recent_url(self, event): self.url_var.set(self.recent_combo.get())
    def update_recent_urls(self): self.recent_combo['values'] = self.settings.data.get('recent_urls', [])

    def show_about(self):
        messagebox.showinfo(self.t('about'), f"{APP_NAME} v{APP_VERSION}\n{self.t('about_message')}")
    
    def check_dependencies(self):
        deps = self.downloader.check_dependencies()
        self.status_message.set(f"yt-dlp: {deps.get('yt-dlp', 'Unknown')}, ffmpeg: {deps.get('ffmpeg', 'Unknown')}")
        
    def check_for_updates(self):
        self.status_message.set(self.t('checking_for_updates'))
        self.root.update()
        if self.downloader.check_for_updates():
            messagebox.showinfo(self.t('update_available'), self.t('update_prompt'))
        else:
            messagebox.showinfo(self.t('no_updates'), self.t('up_to_date'))
        self.status_message.set(self.t('ready'))

    def on_audio_only_toggle(self):
        state = 'disabled' if self.audio_only_var.get() else 'readonly'
        self.quality_combo.config(state=state)

    def parse_progress(self, line):
        match = re.search(r'\[download\]\s+([\d\.]+)% of', line)
        if match:
            percent = float(match.group(1))
            self.update_progress_bar(percent)
        self.log_message(line)

    def update_progress_bar(self, percent):
        self.draw_progress_bar(percent)

    def draw_progress_bar(self, percent):
        self.progress_canvas.delete('all')
        width = self.progress_canvas.winfo_width() or 300
        height = self.progress_canvas.winfo_height() or 20
        fill_w = width * percent / 100
        self.progress_canvas.create_rectangle(0, 0, fill_w, height, fill="green", outline="")
        self.progress_canvas.create_text(width/2, height/2, text=f"{int(percent)}%", fill="white" if percent > 10 else "black")
    
    def log_message(self, msg):
        self.output_text.insert(tk.END, msg + '\n')
        self.output_text.see(tk.END)

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

    def run(self):
        self.root.mainloop() 