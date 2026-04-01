# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Unified Python CLI (`ctk`) for downloading and transcribing social media content. Auto-detects platform from URL.

## Install

```bash
brew install uv ffmpeg
uv tool install .        # puts `ctk` on PATH
uv tool install . --force # reinstall after changes
```

## Usage

```bash
ctk download <url> [-o output_dir]           # video download (TikTok/YouTube)
ctk download https://x.com/<user>            # tweet archive (X/Twitter)
ctk transcript <input_dir> [-o output_dir]   # transcribe mp4s to markdown
ctk -f <command>                              # skip confirmation prompts
```

## Structure

- `src/ctk/cli.py` — main CLI module
- `pyproject.toml` — package config and deps
- `tests/` — unit tests (run with `uv run --with pytest pytest tests/`)
- `tiktok/` — legacy shell scripts
- `youtube/` — legacy shell scripts
- `twitter/` — legacy Python script
- `output/` — default download destination (gitignored via convention)
