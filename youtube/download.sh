#!/bin/bash

URL="$1"
OUTPUT_DIR="${2:-./output/youtube}/videos"

if [ -z "$URL" ]; then
  echo "Usage: ./download.sh <url> [output_dir]"
  echo ""
  echo "Arguments:"
  echo "  url          YouTube video, playlist, or channel URL"
  echo "  output_dir   Where to save videos (default: ./output/youtube/videos)"
  echo ""
  echo "Examples:"
  echo "  ./download.sh https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  echo "  ./download.sh https://www.youtube.com/@channel"
  echo "  ./download.sh https://www.youtube.com/playlist?list=PLxxx ~/Videos/yt"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

yt-dlp "$URL" \
  -f "bestvideo[height<=1080]+bestaudio/best[height<=1080]" \
  --merge-output-format mp4 \
  --download-archive "$OUTPUT_DIR/.archive" \
  -o "$OUTPUT_DIR/%(upload_date)s-%(title)s-%(id)s.%(ext)s"
