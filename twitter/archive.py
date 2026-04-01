#!/usr/bin/env python3
"""Archive all tweets from an X/Twitter account to markdown files."""

import argparse
import os
import re
import sys
from datetime import datetime


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
        f"tweet_id: \"{tweet.get('tweet_id', '')}\"",
        f"author: \"{user.get('name', '')}\"",
        f"handle: \"{user.get('screen_name', '')}\"",
        f"post_date: {ts.strftime('%Y-%m-%dT%H:%M')}",
        f"created_date: {datetime.now().strftime('%Y-%m-%dT%H:%M')}",
        f"likes: {likes}",
        f"retweets: {retweets}",
        f"replies: {comments}",
        f"url: \"{url}\"",
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


def main():
    parser = argparse.ArgumentParser(
        description="Archive all tweets from an X/Twitter account"
    )
    parser.add_argument("username", help="X/Twitter username to archive (without @)")
    parser.add_argument(
        "-o", "--output", default="output/x", help="Output directory (default: output/x)"
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Max tweets to fetch (0 = all, default: 10)"
    )
    parser.add_argument(
        "--include-replies", action="store_true",
        help="Include replies (excluded by default)",
    )
    parser.add_argument(
        "--since", help="Start date in YYYY-MM-DD format (default: fetch all)"
    )
    parser.add_argument(
        "--until", help="End date in YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--auth-token",
        help="X auth_token cookie (or set X_AUTH_TOKEN env var)",
    )
    parser.add_argument(
        "--proxy", help="Proxy URL (or set X_PROXY env var)"
    )
    args = parser.parse_args()

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

    try:
        from Scweet import Scweet
    except ImportError:
        print("Error: Scweet not installed. Run: uv pip install Scweet")
        sys.exit(1)

    username = args.username.lstrip("@")
    output_dir = os.path.abspath(os.path.join(args.output, username))
    os.makedirs(output_dir, exist_ok=True)
    db_path = os.path.join(os.path.abspath(args.output), "scweet_state.db")

    scweet_args = {"auth_token": auth_token, "db_path": db_path}
    if proxy:
        scweet_args["proxy"] = proxy

    s = Scweet(**scweet_args)

    print(f"Archiving tweets from @{username}...")

    search_args = {
        "from_users": [username],
        "save": False,
    }

    if not args.include_replies:
        search_args["tweet_type"] = "originals_only"

    if args.limit > 0:
        search_args["limit"] = args.limit

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


if __name__ == "__main__":
    main()
