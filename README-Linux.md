# Moaz Downloader for Linux

Thank you for downloading Moaz Downloader! This guide will walk you through running the application on your Linux system.

## How to Run

1.  **Unzip the File:**
    After downloading `Linux.zip`, unzip it. This will create a folder containing the application (`MoazDownloader`) and this guide.

2.  **Open a terminal** in the newly created folder.

3.  **Make the application executable:**
    In the terminal, run the following command to give the `MoazDownloader` file execute permissions. You only need to do this once.
    ```bash
    chmod +x MoazDownloader
    ```

4.  **Run the application:**
    Now you can launch the application directly from the terminal:
    ```bash
    ./MoazDownloader
    ```
    An application window should appear, and you're ready to start downloading!

## Optional: Install for System-Wide Access (Advanced)

If you want to run `MoazDownloader` from any terminal location without navigating to its folder, you can move it to a directory that is in your system's `PATH`.

1.  Move the file to `/usr/local/bin`:
    ```bash
    sudo mv MoazDownloader /usr/local/bin/moaz-downloader
    ```
2.  Now you can run the application from anywhere by simply typing:
    ```bash
    moaz-downloader
    ```

## System Requirements
*   A modern Linux distribution.
*   No external dependencies are required as they are all bundled.

## Troubleshooting
If you encounter a "Permission denied" error, it means the file is not executable. Please run the `chmod +x MoazDownloader` command again as described in the steps above. 