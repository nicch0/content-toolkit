# content-toolkit

Unified CLI for downloading and transcribing social media content.

## Install

Requires [uv](https://docs.astral.sh/uv/) (`brew install uv`) and [ffmpeg](https://ffmpeg.org/) (`brew install ffmpeg`).

```bash
uv tool install .
```

This puts `ctk` on your PATH.

## Usage

```bash
ctk <command> [options]
```

Pass `-f` / `--force` before the command to skip confirmation prompts.

## Download

Downloads videos from TikTok, YouTube, or archives tweets from X/Twitter. Platform is auto-detected from the URL.

```bash
ctk download <url> [options]
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory (default: `./output/<platform>/videos`) |
| `-f, --force` | Skip confirmation prompt |

### TikTok

```bash
ctk download https://www.tiktok.com/@briarcochran
ctk download https://www.tiktok.com/@briarcochran -o ~/Videos/tiktok
```

### YouTube

Caps video at 1080p. Uses a download archive to skip already-downloaded videos.

```bash
ctk download https://www.youtube.com/watch?v=dQw4w9WgXcQ
ctk download https://www.youtube.com/@channel
ctk download https://www.youtube.com/playlist?list=PLxxx -o ~/Videos/yt
```

### X/Twitter

Archives tweets to Obsidian-compatible markdown with YAML frontmatter. Requires an auth token.

```bash
# Set auth token (get from browser DevTools > Application > Cookies > auth_token)
export X_AUTH_TOKEN="your_auth_token_here"

ctk download https://x.com/username
ctk download https://x.com/username -l 0 --since 2024-01-01
ctk download https://x.com/username --include-replies
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
ctk transcript <input_dir> [options]
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
ctk transcript ./output/tiktok/videos
ctk transcript --split --accurate ./output/youtube/videos ./transcripts
ctk transcript --subs --limit 5 ./output/youtube/videos
```

Already-transcribed videos are skipped. A summary of existing/successful/failed is shown at the end.

## Development

```bash
# Run tests
uv run --with pytest pytest tests/ -v

# Reinstall after code changes
uv tool install . --force
```

## Project Structure

```
src/ctk/cli.py      — main CLI module
pyproject.toml       — package config and dependencies
tests/test_cli.py    — unit tests
tiktok/              — legacy shell scripts
youtube/             — legacy shell scripts
twitter/             — legacy Python script
```
