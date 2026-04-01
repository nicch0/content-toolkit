#!/bin/bash

SPLIT=false
LIMIT=0
MODEL="base"
USE_SUBTITLES=false
ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --split) SPLIT=true; shift ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --accurate) MODEL="large-v3"; shift ;;
    --subs) USE_SUBTITLES=true; shift ;;
    -*) echo "Unknown option: $1"; exit 1 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done

INPUT="${ARGS[0]}"
OUTPUT_DIR="${ARGS[1]:-.}"

if [ -z "$INPUT" ]; then
  echo "Usage: ./transcript.sh [options] <input> [output_dir]"
  echo ""
  echo "Arguments:"
  echo "  input              File or folder containing .mp4 files to transcribe"
  echo "  output_dir         Where to save .md transcripts (default: current directory)"
  echo ""
  echo "Options:"
  echo "  --split          Split transcript into one line per sentence"
  echo "  --limit <num>    Only transcribe up to <num> videos"
  echo "  --accurate       Use large-v3 model for better punctuation (slower, ~3GB download)"
  echo "  --subs           Prefer YouTube subtitles over whisper (faster, requires yt-dlp)"
  echo ""
  echo "Examples:"
  echo "  ./transcript.sh ./output/youtube/videos"
  echo "  ./transcript.sh --split ./output/youtube/videos ./transcripts"
  echo "  ./transcript.sh --subs --limit 5 ./output/youtube/videos"
  echo "  ./transcript.sh --split ./output/youtube/videos/video.mp4"
  exit 1
fi

if ! command -v uv &> /dev/null; then
  echo "Error: uv is not installed."
  echo "Install with: brew install uv"
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Build file list: single file or directory glob
videos=()
if [ -f "$INPUT" ]; then
  videos=("$INPUT")
elif [ -d "$INPUT" ]; then
  for v in "$INPUT"/*.mp4; do
    [ -f "$v" ] && videos+=("$v")
  done
else
  echo "Error: $INPUT is not a file or directory"
  exit 1
fi

existing=()
successful=()
failed=()
count=0

for video in "${videos[@]}"; do
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

  # Try YouTube subtitles first if --subs flag is set
  if [ "$USE_SUBTITLES" = true ]; then
    # Extract video ID from filename (last segment before .mp4)
    video_id=$(echo "$basename" | grep -oE '[A-Za-z0-9_-]{11}$')
    if [ -n "$video_id" ]; then
      transcript=$(yt-dlp --write-auto-sub --sub-lang en --skip-download \
        --sub-format vtt -o "/tmp/yt-sub-%(id)s" \
        "https://www.youtube.com/watch?v=$video_id" 2>/dev/null && \
        SUB_FILE="/tmp/yt-sub-${video_id}.en.vtt" WHISPER_SPLIT="$SPLIT" \
        python3 -c "
import os, re
sub_file = os.environ['SUB_FILE']
if not os.path.exists(sub_file):
    exit(1)
with open(sub_file) as f:
    text = f.read()
# Strip VTT headers and timestamps
lines = []
for line in text.split('\n'):
    if re.match(r'^\d{2}:', line) or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or line.strip() == '':
        continue
    # Remove VTT tags
    clean = re.sub(r'<[^>]+>', '', line).strip()
    if clean and clean not in lines[-1:]:
        lines.append(clean)
full = ' '.join(lines)
if os.environ['WHISPER_SPLIT'] == 'true':
    sentences = re.split(r'(?<=[.!?])\s+', full)
    print('\n'.join(s.strip() for s in sentences if s.strip()))
else:
    print(full)
" 2>/dev/null)
      rm -f "/tmp/yt-sub-${video_id}.en.vtt"
    fi
  fi

  # Fall back to whisper if no subtitle transcript
  if [ -z "$transcript" ]; then
    transcript=$(VIDEO_PATH="$video" WHISPER_MODEL="$MODEL" WHISPER_SPLIT="$SPLIT" \
      uv run --with faster-whisper python3 -c "
import os, re
from faster_whisper import WhisperModel
model = WhisperModel(os.environ['WHISPER_MODEL'], device='cpu', compute_type='int8')
segments, _ = model.transcribe(os.environ['VIDEO_PATH'], language='en')
full = ' '.join(s.text.strip() for s in segments)
if os.environ['WHISPER_SPLIT'] == 'true':
    sentences = re.split(r'(?<=[.!?])\s+', full)
    print('\n'.join(s.strip() for s in sentences if s.strip()))
else:
    print(full)
")
  fi

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
