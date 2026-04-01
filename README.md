# content-toolkit

Collection of shell scripts for downloading and managing social media content.

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `brew install yt-dlp`
- [ffmpeg](https://ffmpeg.org/): `brew install ffmpeg` (needed to merge video + audio streams)
- [uv](https://docs.astral.sh/uv/): `brew install uv` (runs Python tools without global installs)

## TikTok

### Download videos

```bash
./tiktok/download.sh <account> [output_dir]
```

| Argument | Description |
|----------|-------------|
| `account` | TikTok username (without the @ prefix) |
| `output_dir` | Where to save videos (default: `./output/tiktok/<account>/videos`) |

```bash
./tiktok/download.sh briarcochran
./tiktok/download.sh briarcochran ~/Videos/tiktok
```

Files are saved as `YYYYMMDD-title-id.mp4`, so they sort chronologically.

### Transcribe videos

Uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (via `uv`) to transcribe `.mp4` files to markdown.

```bash
./tiktok/transcript.sh [options] <input_dir> [output_dir]
```

| Argument | Description |
|----------|-------------|
| `input_dir` | Folder containing `.mp4` files to transcribe |
| `output_dir` | Where to save `.md` transcripts (default: current directory) |

| Option | Description |
|--------|-------------|
| `--split` | Split transcript into one line per sentence |
| `--limit <num>` | Only transcribe up to `<num>` videos |
| `--accurate` | Use large-v3 model for better punctuation (slower, ~3GB download) |

```bash
./tiktok/transcript.sh ./output/tiktok/briarcochran/videos
./tiktok/transcript.sh --split --accurate ./output/tiktok/briarcochran/videos ./transcripts
./tiktok/transcript.sh --limit 5 ./output/tiktok/briarcochran/videos
```

Already-transcribed videos are skipped. A summary of existing/successful/failed is shown at the end.

## Twitter/X

### Archive tweets

Archives tweets from an X account to Obsidian-compatible markdown files using [Scweet](https://github.com/Altimis/Scweet). Replies are excluded by default.

```bash
# Set auth token (get from browser DevTools > Application > Cookies > auth_token)
export X_AUTH_TOKEN="your_auth_token_here"

# Archive recent tweets (default: 10)
uv run twitter/archive.py username

# Get all tweets with date range
uv run twitter/archive.py username -l 0 --since 2024-01-01

# Include replies
uv run twitter/archive.py username --include-replies
```

| Argument | Description |
|----------|-------------|
| `username` | X/Twitter username (without @) |

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory (default: `output/x`) |
| `-l, --limit` | Max tweets to fetch, 0 = all (default: 10) |
| `--include-replies` | Include replies (excluded by default) |
| `--since` | Start date in YYYY-MM-DD format |
| `--until` | End date in YYYY-MM-DD format |
| `--auth-token` | X auth_token cookie (or set `X_AUTH_TOKEN` env var) |
| `--proxy` | Proxy URL (or set `X_PROXY` env var) |

Files are saved as `YYYYMMDD-slug.md` in `output/x/<username>/` with Obsidian YAML frontmatter (date, likes, retweets, replies, url).
