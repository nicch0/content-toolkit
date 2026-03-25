# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Collection of shell scripts for downloading and managing social media content. Each platform lives in its own directory with standalone scripts.

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): `brew install yt-dlp`
- [ffmpeg](https://ffmpeg.org/): `brew install ffmpeg`

## Usage

```bash
# TikTok: download all videos from an account
./tiktok/download.sh <account> [output_dir]
# Output defaults to ./output/tiktok/<account>/
```

## Structure

- `tiktok/` — platform-specific download scripts
- `output/` — default download destination (gitignored via convention)
