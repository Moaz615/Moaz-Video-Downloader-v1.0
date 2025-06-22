import argparse
import logging
import sys
from pathlib import Path

from .settings import Settings
from .downloader import VideoDownloader

def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Moaz Video Downloader - Command Line Interface")
    parser.add_argument("url", nargs='?', help="The URL of the video to download.")
    parser.add_argument("-o", "--output", help="Output directory for downloaded files.")
    parser.add_argument("-q", "--quality", default="best", help="Video quality (e.g., best, 1080p, 720p).")
    parser.add_argument("-a", "--audio", action="store_true", help="Download audio only (MP3).")
    parser.add_argument("-p", "--playlist", action="store_true", help="Download the entire playlist.")
    parser.add_argument("--batch-file", help="Path to a file containing URLs to download.")
    parser.add_argument("--parallel", type=int, default=2, help="Number of parallel downloads for batch processing.")
    parser.add_argument("--config", help="Path to a custom settings JSON file.")
    parser.add_argument("--verbose", "-v", action="count", default=0, help="Increase verbosity level.")
    
    args = parser.parse_args()

    # Setup logging
    log_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    log_level = log_levels[min(args.verbose, len(log_levels) - 1)]
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    settings = Settings(path=Path(args.config) if args.config else None)
    
    # Override settings with CLI arguments if provided
    output_dir = args.output or settings.data.get("output_dir")

    downloader = VideoDownloader(
        logger=logging.getLogger(__name__),
        proxy=settings.data.get('proxy'),
        user_agent=settings.data.get('user_agent'),
        bandwidth=settings.data.get('bandwidth'),
        ffmpeg_path=settings.data.get('ffmpeg_path') # Assuming you add this to settings
    )
    
    def cli_progress(message):
        print(message)

    if args.batch_file:
        try:
            with open(args.batch_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            logging.info(f"Starting batch download from {args.batch_file}...")
            results = downloader.batch_download(
                urls=urls,
                output_dir=output_dir,
                quality=args.quality,
                audio_only=args.audio,
                playlist=args.playlist,
                cookie_file=settings.data.get('cookie_file'),
                parallel=args.parallel,
                progress_callback=cli_progress
            )
            
            for url, success in results.items():
                status = "succeeded" if success else "failed"
                print(f"Download for {url}: {status}")

        except FileNotFoundError:
            logging.error(f"Batch file not found: {args.batch_file}")
            sys.exit(1)
            
    elif args.url:
        logging.info(f"Downloading {args.url} to {output_dir}...")
        success, final_path = downloader.download(
            url=args.url,
            output_dir=output_dir,
            quality=args.quality,
            audio_only=args.audio,
            playlist=args.playlist,
            cookie_file=settings.data.get('cookie_file'),
            progress_callback=cli_progress
        )
        if success:
            print(f"Download successful! File saved to: {final_path}")
        else:
            print("Download failed.")
            sys.exit(1)
    else:
        print("No URL or batch file provided. Use --help for more information.")
        parser.print_help()

if __name__ == "__main__":
    main() 