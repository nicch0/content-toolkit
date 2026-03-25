#!/bin/bash

SPLIT=false
LIMIT=0
MODEL="base"
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --split) SPLIT=true; shift ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --accurate) MODEL="large-v3"; shift ;;
    -*) echo "Unknown option: $1"; exit 1 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

INPUT_DIR="${ARGS[0]}"
OUTPUT_DIR="${ARGS[1]:-.}"

if [ -z "$INPUT_DIR" ]; then
  echo "Usage: ./transcript.sh [options] <input_dir> [output_dir]"
  echo ""
  echo "Arguments:"
  echo "  input_dir          Folder containing .mp4 files to transcribe"
  echo "  output_dir         Where to save .md transcripts (default: current directory)"
  echo ""
  echo "Options:"
  echo "  --split          Split transcript into one line per sentence"
  echo "  --limit <num>    Only transcribe up to <num> videos"
  echo "  --accurate       Use large-v3 model for better punctuation (slower, ~3GB download)"
  echo ""
  echo "By default, the transcript is a single block of text."
  echo ""
  echo "Examples:"
  echo "  ./transcript.sh ./output/tiktok/briarcochran/videos"
  echo "  ./transcript.sh --split ./output/tiktok/briarcochran/videos ./transcripts"
  echo "  ./transcript.sh --limit 5 ./output/tiktok/briarcochran/videos"
  exit 1
fi

if ! command -v uv &> /dev/null; then
  echo "Error: uv is not installed."
  echo "Install with: brew install uv"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

existing=()
successful=()
failed=()
count=0

for video in "$INPUT_DIR"/*.mp4; do
  [ -f "$video" ] || continue

  basename=$(basename "$video" .mp4)
  output_file="$OUTPUT_DIR/$basename.md"

  if [ -f "$output_file" ]; then
    echo "Skipping (already exists): $basename"
    existing+=("$basename")
    continue
  fi

  if [ "$LIMIT" -gt 0 ] && [ "$count" -ge "$LIMIT" ]; then
    break
  fi

  echo "Transcribing: $basename"

  transcript=$(uv run --with faster-whisper python3 -c "
import re
from faster_whisper import WhisperModel
model = WhisperModel('$MODEL', device='cpu', compute_type='int8')
segments, _ = model.transcribe('$video', language='en')
full = ' '.join(s.text.strip() for s in segments)
if $SPLIT:
    sentences = re.split(r'(?<=[.!?])\s+', full)
    print('\n'.join(s.strip() for s in sentences if s.strip()))
else:
    print(full)
" 2>/dev/null)

  if [ -n "$transcript" ]; then
    echo "# $basename" > "$output_file"
    echo "" >> "$output_file"
    echo "$transcript" >> "$output_file"
    successful+=("$basename")
    count=$((count + 1))
  else
    failed+=("$basename")
    count=$((count + 1))
  fi
done

echo ""
echo "=== Summary ==="
if [ ${#existing[@]} -gt 0 ]; then
  echo ""
  echo "Existing (${#existing[@]}):"
  for f in "${existing[@]}"; do echo "  $f"; done
fi
if [ ${#successful[@]} -gt 0 ]; then
  echo ""
  echo "Successful (${#successful[@]}):"
  for f in "${successful[@]}"; do echo "  $f"; done
fi
if [ ${#failed[@]} -gt 0 ]; then
  echo ""
  echo "Failed (${#failed[@]}):"
  for f in "${failed[@]}"; do echo "  $f"; done
fi
echo ""
echo "Total: ${#existing[@]} existing, ${#successful[@]} successful, ${#failed[@]} failed"
