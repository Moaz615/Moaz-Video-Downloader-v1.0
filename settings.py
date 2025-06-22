import json
from pathlib import Path
from typing import Optional, Any, Dict

class Settings:
    """Handles loading and saving user settings."""
    def __init__(self, path: Optional[Path] = None):
        self.path = path or Path.home() / ".video_downloader_settings.json"
        self.data: Dict[str, Any] = {
            "language": "en",
            "theme": "light",
            "output_dir": str(Path.home() / "Downloads"),
            "parallel": 2,
            "postprocess_script": "",
            "format": "mp4",
            "custom_format": "",
            "cookie_file": "",
            "recent_urls": [],
            "recent_batch_files": [],
            "playlist": False,
            "proxy": "",
            "enable_notifications": True,
            "log_level": "INFO",
            "file_template": "%(uploader)s - %(id)s.%(ext)s",
            "user_agent": "",
            "bandwidth": "",
            "plugin_dir": "",
            "download_history": [],
            "skip_downloaded": True,
        }
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self.data.update(json.load(f))
            except Exception as e:
                print(f"Failed to load settings: {e}")

    def save(self):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def add_recent_url(self, url: str):
        if url and url not in self.data['recent_urls']:
            self.data['recent_urls'] = ([url] + self.data['recent_urls'])[:10]
            self.save()

    def add_recent_batch_file(self, path: str):
        if path and path not in self.data['recent_batch_files']:
            self.data['recent_batch_files'] = ([path] + self.data['recent_batch_files'])[:5]
            self.save()

    def add_history(self, entry: dict):
        self.data['download_history'] = ([entry] + self.data['download_history'])[:100]
        self.save()

    def export_settings(self, export_path: str):
        with open(export_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def import_settings(self, import_path: str):
        with open(import_path, 'r', encoding='utf-8') as f:
            self.data.update(json.load(f))
        self.save() 