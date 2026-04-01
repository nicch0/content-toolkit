# content-toolkit

Unified CLI for downloading and transcribing social media content.

## Prerequisites

- [uv](https://docs.astral.sh/uv/): `brew install uv` (manages Python deps automatically)
- [ffmpeg](https://ffmpeg.org/): `brew install ffmpeg` (needed to merge video + audio streams)

## Usage

```bash
uv run ctk.py <command> [options]
```

Pass `-f` / `--force` before the command to skip confirmation prompts.

## Download

Downloads videos from TikTok, YouTube, or archives tweets from X/Twitter. Platform is auto-detected from the URL.

```bash
uv run ctk.py download <url> [options]
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory (default: `./output/<platform>/videos`) |
| `-f, --force` | Skip confirmation prompt |

### TikTok

```bash
uv run ctk.py download https://www.tiktok.com/@briarcochran
uv run ctk.py download https://www.tiktok.com/@briarcochran -o ~/Videos/tiktok
```

### YouTube

Caps video at 1080p. Uses a download archive to skip already-downloaded videos.

```bash
uv run ctk.py download https://www.youtube.com/watch?v=dQw4w9WgXcQ
uv run ctk.py download https://www.youtube.com/@channel
uv run ctk.py download https://www.youtube.com/playlist?list=PLxxx -o ~/Videos/yt
```

### X/Twitter

Archives tweets to Obsidian-compatible markdown with YAML frontmatter. Requires an auth token.

```bash
# Set auth token (get from browser DevTools > Application > Cookies > auth_token)
export X_AUTH_TOKEN="your_auth_token_here"

uv run ctk.py download https://x.com/username
uv run ctk.py download https://x.com/username -l 0 --since 2024-01-01
uv run ctk.py download https://x.com/username --include-replies
```

| Option | Description |
|--------|-------------|
| `-l, --limit` | Max tweets to fetch, 0 = all (default: 10) |
| `--include-replies` | Include replies (excluded by default) |
| `--since` | Start date (YYYY-MM-DD) |
| `--until` | End date (YYYY-MM-DD) |
| `--auth-token` | X auth_token cookie (or set `X_AUTH_TOKEN` env var) |
| `--proxy` | Proxy URL (or set `X_PROXY` env var) |

Files are saved as `YYYYMMDD-slug.md` in `output/x/<username>/`.

## Transcript

Transcribes `.mp4` files to markdown using [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

```bash
uv run ctk.py transcript <input_dir> [options]
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory (default: current directory) |
| `--split` | One sentence per line |
| `--limit <num>` | Max videos to transcribe |
| `--accurate` | Use large-v3 model (slower, ~3GB download) |
| `--model <name>` | Override whisper model name |
| `--subs` | Prefer YouTube subtitles over whisper (faster, needs video ID in filename) |

```bash
uv run ctk.py transcript ./output/tiktok/videos
uv run ctk.py transcript --split --accurate ./output/youtube/videos ./transcripts
uv run ctk.py transcript --subs --limit 5 ./output/youtube/videos
```

Already-transcribed videos are skipped. A summary of existing/successful/failed is shown at the end.
