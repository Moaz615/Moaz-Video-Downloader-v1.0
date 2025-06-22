# Moaz Video Downloader v1.0

A powerful, universal video downloader with a modern GUI interface. Download videos and playlists from hundreds of websites with support for multiple languages and themes.

![Moaz Downloader](moaz.ico)

## ✨ Features

- **Universal Download Support**: Download from hundreds of video platforms
- **Batch Processing**: Download multiple videos simultaneously with parallel processing
- **Format Flexibility**: Support for video and audio-only (MP3) downloads
- **Multi-Language Interface**: Available in 10+ languages (including English, Arabic, French, Spanish, German, Italian, Portuguese, Russian, Japanese, and Chinese)
- **Modern UI**: Clean interface with light/dark and more theme support
- **Drag & Drop**: Easy URL input with drag-and-drop functionality
- **Smart Features**: Download history, recent URLs, and persistent settings
- **Built-in Tools**: Integrated ffmpeg for video processing and yt-dlp auto-updates
- **Cross-Platform**: Windows, macOS, and Linux support

## 🚀 Installation

### Windows Users

1. **Download**: Get the latest Windows installer from the [Releases](https://github.com/Moaz615/Moaz-Video-Downloader-V.1.0/releases) page
2. **Extract**: Unzip the `Windows.zip` file to access the setup files
3. **Install**: Run `MoazVideoDownloaderSetup.exe` and follow the installation wizard
4. **Launch**: Start the application from the Start Menu or desktop shortcut

### macOS Users

1. **Download**: Get the latest macOS package from the [Releases](https://github.com/Moaz615/Moaz-Video-Downloader-V.1.0/releases) page
2. **Extract**: Unzip the `macOS.zip` file
3. **Install**: Open the `.dmg` file and drag the app to Applications folder
4. **Launch**: Open from Applications or Spotlight search

### Linux Users

1. **Download**: Get the latest Linux package from the [Releases](https://github.com/Moaz615/Moaz-Video-Downloader-V.1.0/releases) page
2. **Extract**: Unzip the `Linux.zip` file
3. **Install**: Run the AppImage file or use the provided installation script
4. **Launch**: Start from your applications menu

## 📖 How to Use

### Basic Usage
1. **Single Video**: Paste a video URL and click "Download"
2. **Batch Download**: Paste multiple URLs (one per line) and click "Batch Download"
3. **Drag & Drop**: Simply drag video URLs directly into the application

### Settings & Configuration
- **Language**: Switch between 10+ supported languages
- **Theme**: Toggle between light and dark modes
- **Output Directory**: Set custom download location (recommended: avoid default Downloads folder)
- **Format Selection**: Choose between video or audio-only downloads
- **Download History**: Track and manage your download history

### Important Notes
- **Download Directory**: Please choose a different download directory than the default Downloads folder
- **Download Status**: Ignore "download failed" errors temporarily - files are usually downloaded successfully
- **Audio Files**: Some audio-only downloads may require ffmpeg (auto-download available in settings)
- **Notifications**: The app will notify you when downloads complete

## 🔧 Troubleshooting

### Common Issues

**Windows SmartScreen Warning**
- Click "More info" when the warning appears
- Click "Run anyway" to proceed with installation

**FFmpeg Errors**
- Use the auto-download feature in Settings
- Download manually from [ffmpeg.org](https://ffmpeg.org/download.html) if needed

**Download Failures**
- Check internet connection
- Verify URL is accessible
- Use "Check for Updates" in Settings to update yt-dlp
- Check your download directory for completed files

**Installation Issues**
- Run installer as administrator if needed
- Temporarily disable antivirus during installation
- Ensure sufficient disk space (100MB minimum)

**Cannot find the downloaded file in the download directory**
- **File Date Issue**: Downloaded files retain the original video's upload date, not the download date. If you're sorting files by date modified, older videos may appear at the bottom of your file list.
- **Solution**: Create a dedicated folder for downloaded videos to keep them organized and easy to find
- **Alternative**: Use the app's download history feature to track your downloads 

### Getting Help
- **In-App Help**: Use the Help menu within the application
- **Email Support**: Contact mazmhmd493@gmail.com
- **GitHub Issues**: Report bugs and feature requests on GitHub

## 📋 System Requirements

### Windows
- Windows 10 or Windows 11
- 4GB RAM minimum
- 100MB free disk space

### macOS
- macOS 10.14 or later
- 4GB RAM minimum
- 100MB free disk space

### Linux
- Ubuntu 18.04+ or equivalent
- 4GB RAM minimum
- 100MB free disk space

## 📦 Package Contents

### Windows Package (`Windows.zip`)
- `MoazVideoDownloaderSetup.exe` - Main installer
- `README-Windows.md` - Windows-specific instructions
- `moaz.ico` - Application icon

### macOS Package (`macOS.zip`)
- `Moaz Downloader.app` - macOS application bundle
- `README-macOS.md` - macOS-specific instructions

### Linux Package (`Linux.zip`)
- `Moaz Downloader` - Linux executable
- `README-Linux.md` - Linux-specific instructions

## 🔄 Updates

The application includes automatic updates for:
- **yt-dlp**: Video downloader engine updates
- **FFmpeg**: Multimedia processing tool updates

Use the "Check for Updates" feature in Settings to keep components current.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video downloader engine
- [FFmpeg](https://ffmpeg.org/) - Multimedia processing
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework

---
Author: Moaz Mohamed (Abulbara)

**Note**: This application is for personal use only. Please respect copyright laws and terms of service of the websites you download from.
