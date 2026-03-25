#!/bin/bash

ACCOUNT="$1"
OUTPUT_DIR="${2:-$HOME/Downloads/Tiktok/$ACCOUNT}"

if [ -z "$ACCOUNT" ]; then
  echo "Usage: ./download.sh <account> [output_dir]"
  echo "Example: ./download.sh briarcochran"
  echo "Example: ./download.sh briarcochran ~/Videos/tiktok"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

yt-dlp "https://www.tiktok.com/@$ACCOUNT" \
  -f "bestvideo+bestaudio/best" \
  --merge-output-format mp4 \
  -o "$OUTPUT_DIR/%(upload_date)s-%(title)s-%(id)s.%(ext)s"
