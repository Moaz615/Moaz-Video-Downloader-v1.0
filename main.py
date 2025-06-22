import argparse
import logging
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

# --- Path Hack ---
# This allows the script to be run directly, without needing to be installed as a package.
# It adjusts the Python path to include the parent directory, making the `moaz_downloader` package visible.
try:
    # If running as a script, add the parent directory to the path
    # to allow relative imports.
    if __name__ == "__main__" and __package__ is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        # Now we can import from our package
        from moaz_downloader.gui import DownloaderGUI
        from moaz_downloader.settings import Settings
        from moaz_downloader.downloader import VideoDownloader
        import moaz_downloader.cli as cli
    # If frozen by PyInstaller, the path is handled differently.
    elif getattr(sys, 'frozen', False):
        # This is the standard structure for a PyInstaller bundle with our package
        from moaz_downloader.gui import DownloaderGUI
        from moaz_downloader.settings import Settings
        from moaz_downloader.downloader import VideoDownloader
        import moaz_downloader.cli as cli
    # Otherwise, assume it's being run as a module
    else:
        from .gui import DownloaderGUI
        from .settings import Settings
        from .downloader import VideoDownloader
        from . import cli
except ImportError as e:
    # Provide a helpful message if imports fail
    print(f"Error: Failed to import necessary modules. {e}")
    print("Please ensure you are running from the correct directory or have the package installed.")
    sys.exit(1)

def find_asset(filename):
    """Finds an asset file, handling PyInstaller's temporary directory."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # In a PyInstaller bundle
        return os.path.join(sys._MEIPASS, filename)
    # In a normal environment, assume it's in a 'assets' subdirectory
    # relative to this script's location.
    return os.path.join(os.path.dirname(__file__), 'assets', filename)

def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Moaz Video Downloader")
    parser.add_argument("--cli", action="store_true", help="Run in command-line interface mode.")
    # Capture all other arguments to pass to the CLI if needed
    args, unknown = parser.parse_known_args()

    # Instantiate core components
    settings = Settings()
    
    # Locate FFmpeg
    # You might want to make this configurable in settings.py
    ffmpeg_path = find_asset('ffmpeg.exe')
    if not os.path.exists(ffmpeg_path):
        ffmpeg_path = None # Will trigger a warning in the GUI/downloader
        
    downloader = VideoDownloader(
        logger=logging.getLogger(__name__),
        ffmpeg_path=ffmpeg_path,
        # ... other downloader settings from 'settings' instance
    )

    if args.cli:
        # Re-parse arguments for the CLI module
        # This is a bit of a workaround to allow both GUI and CLI flags.
        sys.argv = [sys.argv[0]] + unknown
        cli.main()
    else:
        # Launch the GUI
        icon_path = find_asset('icon.ico')
        if not os.path.exists(icon_path):
            icon_path = None
        
        # Setup basic logging for the GUI
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        try:
            app = DownloaderGUI(settings=settings, downloader=downloader, icon_path=icon_path, ffmpeg_path=ffmpeg_path)
            app.run()
        except Exception as e:
            logging.error(f"Failed to launch GUI: {e}", exc_info=True)
            # Fallback to a simple Tkinter error message if the GUI fails catastrophically
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Fatal Error", f"A critical error occurred: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main() 