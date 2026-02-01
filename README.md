# YouTube Downloader (Python)

A simple Python project to download videos from YouTube and other supported sites using **yt-dlp**. Designed for easy setup, learning, and use by beginners and advanced users alike.

## Features

* Download videos from YouTube and other supported sites
* Lightweight and easy to use
* Cross-platform (Linux, macOS, Windows)
* Command-line interface (CLI)
* Extendable with features like progress bars, format selection, and playlists

## Installation

1. Clone the repository

```bash
git clone https://github.com/<your-username>/YT_DOWNLOADER.git
cd YT_DOWNLOADER
```

2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** Do not commit the `venv/` folder to GitHub. It is included in `.gitignore`.

## Usage

Run the downloader with a video URL:

```bash
python yt_downloader.py <video_url>
```

Example:

```bash
python yt_downloader.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

## Dependencies

* Python 3.10+
* [yt-dlp](https://github.com/yt-dlp/yt-dlp)
* Optional: `requests`, `tqdm` (if you add progress bars or extra features)

All dependencies are listed in `requirements.txt`.

## Contributing

Contributions are welcome!

* Fork the project
* Add your improvements
* Submit a pull request

Please ensure your code is clean and documented.

## License

This project is open-source and free to use for learning, personal, or educational purposes.
