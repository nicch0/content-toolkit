# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Unified Python CLI (`ctk.py`) for downloading and transcribing social media content. Auto-detects platform from URL.

## Prerequisites

- [uv](https://docs.astral.sh/uv/): `brew install uv`
- [ffmpeg](https://ffmpeg.org/): `brew install ffmpeg`

## Usage

```bash
# Download videos (platform auto-detected from URL)
uv run ctk.py download <url> [-o output_dir]

# Transcribe videos to markdown
uv run ctk.py transcript <input_dir> [-o output_dir]
# Options: --split, --limit <num>, --accurate, --model <name>, --subs

# Download tweets from X (auto-detected from x.com/twitter.com URL)
uv run ctk.py download https://x.com/<username> [--auth-token TOKEN]
# Options: -l/--limit, --since, --until, --include-replies, --proxy

# Skip confirmation prompts
uv run ctk.py -f download <url>
```

## Structure

- `ctk.py` — unified CLI (download, transcript)
- `tiktok/` — legacy shell scripts
- `youtube/` — legacy shell scripts
- `twitter/` — legacy Python script
- `output/` — default download destination (gitignored via convention)
