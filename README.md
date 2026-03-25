# tiktok-downloadr

Download all videos from a TikTok account using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

Files are saved as `YYYYMMDD-title-id.mp4`, so they sort chronologically by filename.

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `brew install yt-dlp`
- [ffmpeg](https://ffmpeg.org/): `brew install ffmpeg` (needed to merge video + audio streams)

## Usage

```bash
# Download to ~/Downloads/Tiktok/<account>/
./download.sh briarcochran

# Download to a custom directory
./download.sh briarcochran ~/Videos/tiktok
```
