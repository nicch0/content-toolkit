# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Collection of shell scripts for downloading and managing social media content. Each platform lives in its own directory with standalone scripts.

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `brew install yt-dlp`
- [ffmpeg](https://ffmpeg.org/): `brew install ffmpeg`
- [uv](https://docs.astral.sh/uv/): `brew install uv`

## Usage

```bash
# TikTok: download all videos from an account
./tiktok/download.sh <account> [output_dir]

# TikTok: transcribe downloaded videos to markdown
./tiktok/transcript.sh [options] <input_dir> [output_dir]
# Options: --split (one line per sentence), --limit <num>, --accurate (large-v3 model)

# Twitter/X: archive all tweets from an account
python twitter/archive.py <username> [options]
# Requires: X_AUTH_TOKEN env var or --auth-token flag
```

## Structure

- `tiktok/download.sh` — download all videos from a TikTok account
- `tiktok/transcript.sh` — transcribe videos to markdown using faster-whisper
- `twitter/archive.py` — archive all tweets from an X/Twitter account using Scweet
- `output/` — default download destination (gitignored via convention)
