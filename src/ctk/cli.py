"""Content toolkit — download, transcribe, and archive social media content."""

import argparse
import os
import re
import sys
import tempfile
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_platform(url: str) -> str:
    """Return 'tiktok', 'youtube', 'x', or 'other' based on the URL."""
    if "tiktok.com" in url:
        return "tiktok"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "x.com" in url or "twitter.com" in url:
        return "x"
    return "other"


def confirm(message: str, force: bool) -> bool:
    """Prompt user for confirmation. Returns True if confirmed or forced."""
    if force:
        return True
    try:
        reply = input(f"{message} [Y/n] ").strip().lower()
        return reply in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


# ---------------------------------------------------------------------------
# download
# ---------------------------------------------------------------------------

def cmd_download(args):
    url = args.url
    platform = detect_platform(url)

    if platform == "x":
        return _download_x(args, url)

    return _download_video(args, url, platform)


def _download_video(args, url: str, platform: str):
    import yt_dlp

    output_dir = args.output or f"./output/{platform}/videos"

    print(f"Platform:  {platform}")
    print(f"URL:       {url}")
    print(f"Output:    {output_dir}")

    if not confirm("\nProceed?", args.force):
        print("Aborted.")
        return

    os.makedirs(output_dir, exist_ok=True)

    outtmpl = os.path.join(output_dir, "%(upload_date)s-%(title)s-%(id)s.%(ext)s")

    opts = {
        "outtmpl": outtmpl,
        "merge_output_format": "mp4",
    }

    if platform == "tiktok":
        opts["format"] = "bestvideo+bestaudio/best"
    elif platform == "youtube":
        opts["format"] = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        opts["download_archive"] = os.path.join(output_dir, ".archive")
    else:
        opts["format"] = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def _download_x(args, url: str):
    """Download (archive) tweets from an X/Twitter URL."""
    # Extract username from URL like https://x.com/username or https://x.com/username/status/123
    match = re.search(r"(?:x\.com|twitter\.com)/(@?\w+)", url)
    if not match:
        print(f"Error: could not extract username from URL: {url}")
        sys.exit(1)

    username = match.group(1).lstrip("@")

    auth_token = args.auth_token or os.environ.get("X_AUTH_TOKEN")
    if not auth_token:
        print("Error: provide --auth-token or set X_AUTH_TOKEN env var")
        print()
        print("To get your auth_token:")
        print("  1. Log into x.com in your browser")
        print("  2. Open DevTools (F12) > Application > Cookies > https://x.com")
        print("  3. Copy the 'auth_token' value")
        sys.exit(1)

    proxy = args.proxy or os.environ.get("X_PROXY")
    output_dir = os.path.abspath(os.path.join(args.output or "output/x", username))
    limit = args.limit or 10

    print(f"Platform:  x")
    print(f"User:      @{username}")
    print(f"Output:    {output_dir}")
    print(f"Limit:     {limit} tweets")
    if args.include_replies:
        print(f"Replies:   included")
    if args.since:
        print(f"Since:     {args.since}")
    if args.until:
        print(f"Until:     {args.until}")

    if not confirm("\nProceed?", args.force):
        print("Aborted.")
        return

    try:
        from Scweet import Scweet
    except ImportError:
        print("Error: Scweet not installed. Run: uv pip install Scweet")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(os.path.dirname(output_dir), "scweet_state.db")

    scweet_args = {"auth_token": auth_token, "db_path": db_path}
    if proxy:
        scweet_args["proxy"] = proxy

    s = Scweet(**scweet_args)

    print(f"\nArchiving tweets from @{username}...")

    search_args = {"from_users": [username], "save": False}

    if not args.include_replies:
        search_args["tweet_type"] = "originals_only"
    if limit > 0:
        search_args["limit"] = limit
    if args.since:
        search_args["since"] = args.since
    if args.until:
        search_args["until"] = args.until

    tweets = s.search(**search_args)

    if not tweets:
        print("No tweets found.")
        return

    existing_ids = get_existing_tweet_ids(output_dir)
    written = 0
    skipped = 0

    for tweet in tweets:
        if tweet.get("tweet_id") in existing_ids:
            skipped += 1
            continue

        ts = datetime.strptime(tweet["timestamp"], "%a %b %d %H:%M:%S %z %Y")
        date_prefix = ts.strftime("%Y%m%d")
        slug = slugify(tweet.get("text", ""))
        filename = f"{date_prefix}-{slug}.md"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            f.write(tweet_to_md(tweet))
        written += 1

    print(f"Done. {written} new, {skipped} already archived in {output_dir}/")


# ---------------------------------------------------------------------------
# transcript
# ---------------------------------------------------------------------------

def fetch_youtube_subs(video_id: str) -> str | None:
    """Fetch YouTube auto-subtitles via yt-dlp and return plain text."""
    import yt_dlp

    with tempfile.TemporaryDirectory() as tmpdir:
        outtmpl = os.path.join(tmpdir, "%(id)s")
        opts = {
            "outtmpl": outtmpl,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "vtt",
            "skip_download": True,
            "quiet": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        except Exception:
            return None

        vtt_file = os.path.join(tmpdir, f"{video_id}.en.vtt")
        if not os.path.exists(vtt_file):
            return None

        with open(vtt_file) as f:
            text = f.read()

    lines = []
    for line in text.split("\n"):
        if re.match(r"^\d{2}:", line) or line.startswith(("WEBVTT", "Kind:", "Language:")) or line.strip() == "":
            continue
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean and clean not in lines[-1:]:
            lines.append(clean)

    return " ".join(lines) if lines else None


def transcribe_whisper(video_path: str, model_name: str) -> str | None:
    """Transcribe a video file using faster-whisper."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(video_path, language="en")
    full = " ".join(s.text.strip() for s in segments)
    return full if full.strip() else None


def split_sentences(text: str) -> str:
    """Split text into one sentence per line."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return "\n".join(s.strip() for s in sentences if s.strip())


def cmd_transcript(args):
    input_dir = args.input_dir
    output_dir = args.output or "."
    use_subs = args.subs
    do_split = args.split
    limit = args.limit
    model_name = args.model or ("large-v3" if args.accurate else "base")

    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a directory")
        sys.exit(1)

    mp4s = sorted(Path(input_dir).glob("*.mp4"))

    print(f"Input:     {input_dir}")
    print(f"Output:    {output_dir}")
    print(f"Videos:    {len(mp4s)} found")
    print(f"Model:     {model_name}")
    if use_subs:
        print(f"Subs:      YouTube subtitles preferred")
    if do_split:
        print(f"Split:     one sentence per line")
    if limit > 0:
        print(f"Limit:     {limit}")

    if not confirm("\nProceed?", args.force):
        print("Aborted.")
        return

    os.makedirs(output_dir, exist_ok=True)

    existing = []
    successful = []
    failed = []
    count = 0

    for video in mp4s:
        basename = video.stem
        output_file = os.path.join(output_dir, f"{basename}.md")

        if os.path.exists(output_file):
            print(f"Skipping (already exists): {basename}")
            existing.append(basename)
            continue

        if limit > 0 and count >= limit:
            break

        print(f"Transcribing: {basename}")

        transcript = None

        # Try YouTube subtitles first
        if use_subs:
            video_id = re.search(r"[A-Za-z0-9_-]{11}$", basename)
            if video_id:
                transcript = fetch_youtube_subs(video_id.group())

        # Fall back to whisper
        if transcript is None:
            transcript = transcribe_whisper(str(video), model_name)

        if transcript:
            if do_split:
                transcript = split_sentences(transcript)
            with open(output_file, "w") as f:
                f.write(f"# {basename}\n\n{transcript}\n")
            successful.append(basename)
            count += 1
        else:
            failed.append(basename)
            count += 1

    # Summary
    print("\n=== Summary ===")
    if existing:
        print(f"\nExisting ({len(existing)}):")
        for f in existing:
            print(f"  {f}")
    if successful:
        print(f"\nSuccessful ({len(successful)}):")
        for f in successful:
            print(f"  {f}")
    if failed:
        print(f"\nFailed ({len(failed)}):")
        for f in failed:
            print(f"  {f}")
    print(f"\nTotal: {len(existing)} existing, {len(successful)} successful, {len(failed)} failed")


# ---------------------------------------------------------------------------
# archive
# ---------------------------------------------------------------------------

def tweet_to_md(tweet: dict) -> str:
    """Convert a tweet dict to Obsidian-flavored markdown."""
    ts = datetime.strptime(tweet["timestamp"], "%a %b %d %H:%M:%S %z %Y")
    text = tweet.get("text", "")
    url = tweet.get("tweet_url", "")
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    comments = tweet.get("comments", 0)
    user = tweet.get("user", {})

    lines = [
        "---",
        f'tweet_id: "{tweet.get("tweet_id", "")}"',
        f'author: "{user.get("name", "")}"',
        f'handle: "{user.get("screen_name", "")}"',
        f"post_date: {ts.strftime('%Y-%m-%dT%H:%M')}",
        f"created_date: {datetime.now().strftime('%Y-%m-%dT%H:%M')}",
        f"likes: {likes}",
        f"retweets: {retweets}",
        f"replies: {comments}",
        f'url: "{url}"',
        "---",
        "",
        text,
    ]

    if tweet.get("embedded_text"):
        lines += ["", "> " + tweet["embedded_text"]]

    return "\n".join(lines) + "\n"


def slugify(text: str) -> str:
    """Make a filename-safe slug from tweet text."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_]+", "-", text).strip("-")
    return text[:60] if text else "tweet"


def get_existing_tweet_ids(output_dir: str) -> set[str]:
    """Read tweet_ids from existing markdown files in the output dir."""
    ids = set()
    if not os.path.isdir(output_dir):
        return ids
    for fname in os.listdir(output_dir):
        if not fname.endswith(".md"):
            continue
        filepath = os.path.join(output_dir, fname)
        with open(filepath) as f:
            for line in f:
                if line.startswith("tweet_id:"):
                    tid = line.split(":", 1)[1].strip().strip('"')
                    if tid:
                        ids.add(tid)
                    break
                if not line.startswith(("---", "#")) and line.strip():
                    break
    return ids


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="ctk",
        description="Content toolkit — download, transcribe, and archive social media content.",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Skip confirmation prompts")
    subs = parser.add_subparsers(dest="command", required=True)

    # -- download --
    dl = subs.add_parser("download", help="Download content (TikTok, YouTube, X/Twitter)")
    dl.add_argument("url", help="URL (video, playlist, channel, or X profile)")
    dl.add_argument("-o", "--output", help="Output directory")
    # X/Twitter-specific options
    dl.add_argument("-l", "--limit", type=int, default=0, help="Max tweets to fetch (X only, default: 10)")
    dl.add_argument("--include-replies", action="store_true", help="Include replies (X only)")
    dl.add_argument("--since", help="Start date YYYY-MM-DD (X only)")
    dl.add_argument("--until", help="End date YYYY-MM-DD (X only)")
    dl.add_argument("--auth-token", help="X auth_token cookie (or set X_AUTH_TOKEN env var)")
    dl.add_argument("--proxy", help="Proxy URL (or set X_PROXY env var)")

    # -- transcript --
    tr = subs.add_parser("transcript", help="Transcribe videos to markdown")
    tr.add_argument("input_dir", help="Folder containing .mp4 files")
    tr.add_argument("-o", "--output", help="Output directory (default: current directory)")
    tr.add_argument("--split", action="store_true", help="One sentence per line")
    tr.add_argument("--limit", type=int, default=0, help="Max videos to transcribe")
    tr.add_argument("--accurate", action="store_true", help="Use large-v3 model (slower, ~3GB)")
    tr.add_argument("--model", help="Override whisper model name")
    tr.add_argument("--subs", action="store_true", help="Prefer YouTube subtitles over whisper")

    args = parser.parse_args()

    match args.command:
        case "download":
            cmd_download(args)
        case "transcript":
            cmd_transcript(args)


if __name__ == "__main__":
    main()
