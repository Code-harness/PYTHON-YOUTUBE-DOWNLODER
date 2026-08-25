# TubeStream Pro

A desktop YouTube downloader with real per-video quality detection, codec/container control, audio extraction, subtitles, and thumbnail/metadata embedding — built on `yt-dlp` and `customtkinter`.

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/yt--dlp-2026.8%2B-FF0000?logo=youtube&logoColor=white" alt="yt-dlp">
  <img src="https://img.shields.io/badge/customtkinter-5.2%2B-1F6AA5" alt="customtkinter">
  <img src="https://img.shields.io/badge/ffmpeg-required-007808?logo=ffmpeg&logoColor=white" alt="ffmpeg required">
  <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT">
</p>

---

## Features

- **Real quality detection** — probes the actual video and lists the resolutions YouTube is really serving for it, instead of guessing from a fixed ladder.
- **Codec control** — choose H.264 for maximum compatibility, VP9 for a size/quality balance, or AV1 for the best efficiency, with automatic fallback if a codec isn't available at the chosen height.
- **Container choice** — MP4, MKV, or WebM output.
- **Audio-only extraction** — MP3, M4A, Opus, WAV, or FLAC at 128–320 kbps.
- **Thumbnail and metadata embedding** — tags files with title/uploader metadata and an embedded cover image.
- **Subtitles** — manual and/or auto-generated captions, multiple languages, embedded directly into the output file.
- **Playlist and single-video modes** — playlists download into a per-playlist folder with numbered filenames.
- **Resilient by design** — adapts to YouTube's client/token requirements automatically, with browser-cookie authentication and Deno-powered signature solving for when extra hardening is needed.
- **Persistent settings** — every option is remembered between launches via `settings.json`.

---

## Requirements

| Requirement | Why it's needed | Notes |
|---|---|---|
| **Python 3.9+** | Runs the app | 3.11+ recommended |
| **ffmpeg** | Merges video/audio, extracts audio, embeds thumbnails/subtitles | Must be on your system `PATH` |
| **Deno** (recommended) | Lets yt-dlp solve YouTube's JavaScript signature challenges | App auto-detects it; without it, some high-quality formats may be unavailable |
| A modern browser, logged into YouTube (optional) | Enables the cookie-authentication fallback for restricted videos | Only needed if downloads get blocked or capped at low quality |

---

## Installation

### 1. Get the code

Place `main.py`, `yt_downloader.py`, and `requirements.txt` in one folder.

### 2. Install ffmpeg

<details>
<summary><b>Windows</b></summary>

**Option A — winget (recommended):**
```powershell
winget install Gyan.FFmpeg
```

**Option B — manual:**
1. Download a build from https://www.gyan.dev/ffmpeg/builds/
2. Extract it (e.g. to `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to your `PATH` environment variable
4. Verify: `ffmpeg -version`
</details>

<details>
<summary><b>macOS</b></summary>

```bash
brew install ffmpeg
```
</details>

<details>
<summary><b>Linux (Debian/Ubuntu)</b></summary>

```bash
sudo apt update && sudo apt install ffmpeg
```
</details>

<details>
<summary><b>Linux (Fedora)</b></summary>

```bash
sudo dnf install ffmpeg
```
</details>

<details>
<summary><b>Linux (Arch)</b></summary>

```bash
sudo pacman -S ffmpeg
```
</details>

### 3. Install Deno (recommended)

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
irm https://deno.land/install.ps1 | iex
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
curl -fsSL https://deno.land/install.sh | sh
```

Then add it to your shell's startup file so it's always available:

```bash
echo 'export PATH="$HOME/.deno/bin:$PATH"' >> ~/.bashrc   # or ~/.zshrc
source ~/.bashrc
```
</details>

Verify with:
```bash
deno --version
```

> The app also looks for Deno directly at `~/.deno/bin/deno` and other common install paths, so it will find it even if a particular terminal session's `PATH` hasn't been updated yet.

### 4. Set up a Python environment and install dependencies

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
</details>

### 5. Run it

```bash
python main.py
```
(On Windows with the venv active, this is just `python main.py` as well.)

---

## Usage

1. Paste a YouTube video or playlist URL.
2. Click **Detect Available Qualities** to populate the quality list with what that video actually offers, or leave it on **Best Available**.
3. Pick a codec and container (defaults — H.264/MP4 — work everywhere).
4. Toggle **Audio Only** if you just want the audio track, and pick a format/bitrate.
5. Choose a download folder and hit **Download Now**.
6. Use **Skip / Stop** to abort the current item, or **Cancel** to stop entirely.

All choices — mode, quality, codec, container, subtitles, cookies, theme — persist automatically to `settings.json` next to the app.

---

## screenshot

![Graphical user Interface](/screenshots/gui.png)

## Troubleshooting

YouTube frequently changes what unauthenticated clients are allowed to download, so occasional failures are expected and usually fixable without code changes:

| Symptom | Fix |
|---|---|
| `HTTP Error 403: Forbidden` | Set **Browser Cookies** (sidebar) to a browser you're logged into YouTube with, then close that browser fully before retrying — most browsers lock their cookie file while running. |
| Downloads always cap at low resolution | Same fix as above — authenticated sessions unlock far more formats than anonymous access. |
| `No supported JavaScript runtime could be found` | Install Deno (see above) and relaunch the app from a terminal where `deno --version` works. |
| `Only images are available for download` | YouTube is requiring sign-in for this video's streams — enable Browser Cookies. |
| Detection or download hangs | Check your internet connection and confirm the URL opens in a normal browser; some videos are region-locked or private. |
| `yt-dlp` itself seems out of date | `pip install -U yt-dlp` — YouTube-side breakage is usually patched upstream within days. |

For persistent issues, the **PO Token** field (Advanced) accepts a manually obtained token as a last resort — see the [yt-dlp PO Token guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide).

---

## Project Structure

```
.
├── main.py             # GUI (customtkinter)
├── yt_downloader.py    # Download engine (yt-dlp wrapper)
├── requirements.txt    # Python dependencies
├── settings.json        # Auto-generated on first run; stores your preferences
└── README.md
```

---

## Legal

This tool is intended for downloading content you own the rights to, that is licensed for offline use, or that is otherwise permitted under YouTube's Terms of Service and applicable copyright law. You are responsible for how you use it.

---

## License

MIT — see [LICENSE](LICENSE) for details.