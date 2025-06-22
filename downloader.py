import logging
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Callable, Dict, Tuple

from .utils import is_valid_url

class VideoDownloader:
    """Handles the actual download logic."""
    def __init__(self, logger: Optional[logging.Logger] = None, postprocess_script: Optional[str] = None, proxy: Optional[str] = None, user_agent: Optional[str] = None, bandwidth: Optional[str] = None, plugin_dir: Optional[str] = None, ffmpeg_path: Optional[str] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.postprocess_script = postprocess_script
        self.proxy = proxy
        self.user_agent = user_agent
        self.bandwidth = bandwidth
        self.plugin_dir = plugin_dir
        self.ffmpeg_path = ffmpeg_path
        self.CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        
        try:
            self.ytdlp_cmd = self.find_ytdlp()
        except FileNotFoundError:
            if not self.install_ytdlp():
                raise FileNotFoundError("Failed to install yt-dlp. Please install it manually using: pip install yt-dlp")

    def find_ytdlp(self) -> List[str]:
        """Find yt-dlp command or install it if not found."""
        candidates = [
            ["yt-dlp"],
            [sys.executable, "-m", "yt_dlp"],
            ["python", "-m", "yt_dlp"],
            ["py", "-m", "yt_dlp"]
        ]
        for cmd in candidates:
            try:
                subprocess.run(cmd + ["--version"], capture_output=True, check=True, creationflags=self.CREATE_NO_WINDOW)
                return cmd
            except Exception:
                continue
        
        try:
            self.logger.info("yt-dlp not found. Attempting to install...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--user", "yt-dlp"], 
                         capture_output=True, check=True, creationflags=self.CREATE_NO_WINDOW)
            self.logger.info("yt-dlp installed successfully!")
            
            for cmd in candidates:
                try:
                    subprocess.run(cmd + ["--version"], capture_output=True, check=True, creationflags=self.CREATE_NO_WINDOW)
                    return cmd
                except Exception:
                    continue
        except Exception as e:
            self.logger.error(f"Failed to install yt-dlp: {e}")
            
        raise FileNotFoundError("yt-dlp not found and automatic installation failed. Please install it manually.")

    def install_ytdlp(self) -> bool:
        """Install yt-dlp using pip."""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "yt-dlp"], 
                                 capture_output=True, text=True, creationflags=self.CREATE_NO_WINDOW)
            
            if result.returncode != 0:
                result = subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], 
                                     capture_output=True, text=True, creationflags=self.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                self.logger.info("✓ yt-dlp installed successfully")
                self.ytdlp_cmd = [sys.executable, "-m", "yt_dlp"]
                try:
                    subprocess.run(self.ytdlp_cmd + ["--version"], 
                                 capture_output=True, check=True, creationflags=self.CREATE_NO_WINDOW)
                    self.logger.info("✓ yt-dlp verified and ready to use")
                    return True
                except Exception as e:
                    self.logger.error(f"⚠ yt-dlp installed but verification failed: {e}")
            else:
                self.logger.error(f"⚠ Failed to install yt-dlp: {result.stderr}")
        except Exception as e:
            self.logger.error(f"⚠ Error during yt-dlp installation: {e}")
        return False

    def set_postprocess_script(self, script_path: Optional[str]):
        self.postprocess_script = script_path

    def run_postprocess(self, filepath: str):
        if self.postprocess_script and os.path.exists(self.postprocess_script):
            try:
                result = subprocess.run([sys.executable, self.postprocess_script, filepath], 
                                     capture_output=True, text=True, creationflags=self.CREATE_NO_WINDOW)
                self.logger.info(f"Post-process output: {result.stdout.strip()}")
                if result.returncode != 0:
                   self.logger.error(f"Post-process error: {result.stderr.strip()}")
            except Exception as e:
                self.logger.error(f"Post-process error: {e}")

    def set_proxy(self, proxy: Optional[str]):
        self.proxy = proxy

    def set_user_agent(self, ua: Optional[str]):
        self.user_agent = ua

    def set_bandwidth(self, bw: Optional[str]):
        self.bandwidth = bw

    def set_plugin_dir(self, path: Optional[str]):
        self.plugin_dir = path

    def run_plugin_dir(self, filepath: str):
        if self.plugin_dir and os.path.isdir(self.plugin_dir):
            for fname in os.listdir(self.plugin_dir):
                if fname.endswith('.py'):
                    try:
                        subprocess.run([sys.executable, os.path.join(self.plugin_dir, fname), filepath], 
                                    capture_output=True, text=True, creationflags=self.CREATE_NO_WINDOW)
                    except Exception as e:
                        self.logger.error(f"Plugin error: {e}")

    def check_for_updates(self) -> bool:
        import requests
        try:
            resp = requests.get('https://pypi.org/pypi/yt-dlp/json', timeout=5)
            latest = resp.json()['info']['version']
            result = subprocess.run(self.ytdlp_cmd + ['--version'], capture_output=True, text=True, 
                                 creationflags=self.CREATE_NO_WINDOW)
            current = result.stdout.strip().splitlines()[0]
            return latest != current
        except Exception:
            return False

    def download(self, url: str, output_dir: str, quality: str = "best", audio_only: bool = False, playlist: bool = False, cookie_file: Optional[str] = None, progress_callback: Optional[Callable[[str], None]] = None, proxy: Optional[str] = None, file_template: Optional[str] = None, user_agent: Optional[str] = None, bandwidth: Optional[str] = None, plugin_dir: Optional[str] = None, download_archive: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        last_file = None
        try:
            os.makedirs(output_dir, exist_ok=True)
            output_template = file_template or "%(uploader)s - %(id)s.%(ext)s"
            output_path = os.path.abspath(os.path.join(output_dir, output_template))
            
            cmd = self.ytdlp_cmd + [url, "-o", output_path, "--ignore-errors", "--retries", "3", "--newline"]
            
            if self.ffmpeg_path:
                cmd.extend(["--ffmpeg-location", self.ffmpeg_path])

            if proxy or self.proxy:
                cmd.extend(["--proxy", proxy or self.proxy])
            if user_agent or self.user_agent:
                cmd.extend(["--user-agent", user_agent or self.user_agent])
            if bandwidth or self.bandwidth:
                cmd.extend(["--limit-rate", f"{bandwidth or self.bandwidth}K"])
            if not playlist:
                cmd.append("--no-playlist")

            ffmpeg_available = self.ffmpeg_path is not None
            if audio_only:
                cmd.extend(["--extract-audio", "--audio-format", "mp3", "--audio-quality", "192K"])
            else:
                if ffmpeg_available:
                    if quality == "worst":
                        cmd.extend(["-f", "worst"])
                    elif quality != "best":
                        height = quality.replace('p', '')
                        cmd.extend(["-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"])
                    else:
                        cmd.extend(["-f", "best"])
                else:
                    if quality == "worst":
                        cmd.extend(["-f", "worst[acodec!=none][vcodec!=none]/worst"])
                    elif quality != "best":
                        height = quality.replace('p', '')
                        cmd.extend(["-f", f"best[height<={height}][acodec!=none][vcodec!=none]/best[height<={height}]"])
                    else:
                        cmd.extend(["-f", "best[acodec!=none][vcodec!=none]/best"])
            
            if cookie_file and os.path.exists(cookie_file):
                cmd.extend(["--cookies", cookie_file])
            if download_archive and os.path.exists(download_archive):
                cmd.extend(["--download-archive", download_archive])
                
            if progress_callback:
                progress_callback(f"yt-dlp command: {' '.join(cmd)}")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, creationflags=self.CREATE_NO_WINDOW, bufsize=1)
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                line = line.strip()
                if line:
                    if progress_callback and not progress_callback(line):
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                        return False, last_file
                            
                    if '[download] Destination:' in line:
                        last_file = line.split('Destination: ', 1)[1]
                    elif '[Merger] Merging formats into "' in line:
                        last_file = line.split('[Merger] Merging formats into "', 1)[1].rstrip('"')
                    elif '[ExtractAudio] Destination:' in line:
                        last_file = line.split('[ExtractAudio] Destination: ', 1)[1]
                    elif 'has already been downloaded' in line:
                        last_file = line.split('[download] ', 1)[1].split(' has already')[0]
                        
            success = (process.returncode == 0)
            if success and last_file and os.path.exists(last_file):
                if self.postprocess_script:
                    self.run_postprocess(last_file)
                if self.plugin_dir:
                    self.run_plugin_dir(last_file)
                    
            return success, last_file
        
        except Exception as e:
            if progress_callback:
                progress_callback(f"Unexpected error: {str(e)}")
            return False, last_file

    def batch_download(self, urls: List[str], output_dir: str, quality: str, audio_only: bool, playlist: bool, cookie_file: Optional[str], parallel: int, progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, bool]:
        results = {}
        with ThreadPoolExecutor(max_workers=min(parallel, 8)) as executor:
            future_to_url = {executor.submit(self.download, url, output_dir, quality, audio_only, playlist, cookie_file, lambda msg, u=url: progress_callback(f"[{u}] {msg}") if progress_callback else None): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    success, _ = future.result()
                    results[url] = success
                except Exception as e:
                    if progress_callback:
                        progress_callback(f"Failed to process {url}: {str(e)}")
                    results[url] = False
        return results

    def detect_formats(self, url: str) -> List[str]:
        if not url or not is_valid_url(url):
            return []
        try:
            cmd = self.ytdlp_cmd + [url, "--list-formats", "--no-download"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, creationflags=self.CREATE_NO_WINDOW)
            formats = []
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.strip() and not line.startswith('[') and '|' in line:
                        parts = line.split()
                        if len(parts) > 0 and parts[0] not in ['format', 'code', 'ID']:
                            formats.append(parts[0])
            return formats[:20]
        except Exception:
            return []

    def validate_cookie_file(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
                if not content:
                    return False
                lines = content.split('\n')
                return any(not line.startswith('#') and len(line.split('\t')) >= 6 for line in lines)
        except Exception:
            return False

    def check_dependencies(self) -> Dict[str, str]:
        status = {"yt-dlp": "Not found", "ffmpeg": "Not found"}
        try:
            subprocess.run(self.ytdlp_cmd + ["--version"], capture_output=True, check=True, creationflags=self.CREATE_NO_WINDOW)
            status["yt-dlp"] = "Installed"
        except Exception:
            pass
        
        if self.ffmpeg_path:
            try:
                subprocess.run([self.ffmpeg_path, "-version"], capture_output=True, check=True, creationflags=self.CREATE_NO_WINDOW)
                status["ffmpeg"] = "Installed"
            except Exception:
                status["ffmpeg"] = "Found but seems broken"
                
        return status 