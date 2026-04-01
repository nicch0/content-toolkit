"""Tests for ctk CLI."""

import os
import textwrap
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ctk.cli import (
    confirm,
    detect_platform,
    get_existing_tweet_ids,
    main,
    slugify,
    split_sentences,
    tweet_to_md,
    cmd_transcript,
    cmd_download,
    _download_video,
)


# ---------------------------------------------------------------------------
# detect_platform
# ---------------------------------------------------------------------------

class TestDetectPlatform:
    def test_tiktok(self):
        assert detect_platform("https://www.tiktok.com/@user") == "tiktok"
        assert detect_platform("https://tiktok.com/@user/video/123") == "tiktok"

    def test_youtube(self):
        assert detect_platform("https://www.youtube.com/watch?v=abc") == "youtube"
        assert detect_platform("https://youtu.be/abc") == "youtube"
        assert detect_platform("https://youtube.com/@channel") == "youtube"

    def test_x(self):
        assert detect_platform("https://x.com/user") == "x"
        assert detect_platform("https://twitter.com/user") == "x"
        assert detect_platform("https://x.com/user/status/123") == "x"

    def test_other(self):
        assert detect_platform("https://vimeo.com/123") == "other"
        assert detect_platform("https://example.com") == "other"


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------

class TestConfirm:
    def test_force_returns_true(self):
        assert confirm("proceed?", force=True) is True

    def test_yes_inputs(self):
        for reply in ["y", "Y", "yes", "YES", ""]:
            with patch("builtins.input", return_value=reply):
                assert confirm("proceed?", force=False) is True

    def test_no_inputs(self):
        for reply in ["n", "no", "x", "nope"]:
            with patch("builtins.input", return_value=reply):
                assert confirm("proceed?", force=False) is False

    def test_eof_returns_false(self):
        with patch("builtins.input", side_effect=EOFError):
            assert confirm("proceed?", force=False) is False

    def test_keyboard_interrupt_returns_false(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            assert confirm("proceed?", force=False) is False


# ---------------------------------------------------------------------------
# split_sentences
# ---------------------------------------------------------------------------

class TestSplitSentences:
    def test_basic(self):
        result = split_sentences("Hello world. How are you? I am fine!")
        assert result == "Hello world.\nHow are you?\nI am fine!"

    def test_single_sentence(self):
        assert split_sentences("No period here") == "No period here"

    def test_empty(self):
        assert split_sentences("") == ""

    def test_extra_whitespace(self):
        result = split_sentences("First.   Second.  Third.")
        assert result == "First.\nSecond.\nThird."


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("What's up? #trending @user") == "whats-up-trending-user"

    def test_truncation(self):
        long_text = "a" * 100
        assert len(slugify(long_text)) == 60

    def test_empty(self):
        assert slugify("") == "tweet"

    def test_only_special_chars(self):
        assert slugify("!!!???") == "tweet"

    def test_underscores_and_spaces(self):
        assert slugify("hello_world  foo") == "hello-world-foo"


# ---------------------------------------------------------------------------
# tweet_to_md
# ---------------------------------------------------------------------------

class TestTweetToMd:
    def make_tweet(self, **overrides):
        base = {
            "tweet_id": "123456",
            "timestamp": "Mon Jan 15 10:30:00 +0000 2024",
            "text": "Hello world",
            "tweet_url": "https://x.com/user/status/123456",
            "likes": 42,
            "retweets": 5,
            "comments": 3,
            "user": {"name": "Test User", "screen_name": "testuser"},
        }
        base.update(overrides)
        return base

    def test_basic_frontmatter(self):
        md = tweet_to_md(self.make_tweet())
        assert '---' in md
        assert 'tweet_id: "123456"' in md
        assert 'author: "Test User"' in md
        assert 'handle: "testuser"' in md
        assert "likes: 42" in md
        assert "retweets: 5" in md
        assert "replies: 3" in md
        assert "Hello world" in md

    def test_post_date_format(self):
        md = tweet_to_md(self.make_tweet())
        assert "post_date: 2024-01-15T10:30" in md

    def test_embedded_text(self):
        md = tweet_to_md(self.make_tweet(embedded_text="quoted tweet"))
        assert "> quoted tweet" in md

    def test_no_embedded_text(self):
        md = tweet_to_md(self.make_tweet())
        assert ">" not in md


# ---------------------------------------------------------------------------
# get_existing_tweet_ids
# ---------------------------------------------------------------------------

class TestGetExistingTweetIds:
    def test_reads_ids_from_files(self, tmp_path):
        (tmp_path / "tweet1.md").write_text('---\ntweet_id: "111"\n---\nHello\n')
        (tmp_path / "tweet2.md").write_text('---\ntweet_id: "222"\n---\nWorld\n')
        ids = get_existing_tweet_ids(str(tmp_path))
        assert ids == {"111", "222"}

    def test_skips_non_md_files(self, tmp_path):
        (tmp_path / "notes.txt").write_text('tweet_id: "999"\n')
        ids = get_existing_tweet_ids(str(tmp_path))
        assert ids == set()

    def test_empty_dir(self, tmp_path):
        ids = get_existing_tweet_ids(str(tmp_path))
        assert ids == set()

    def test_nonexistent_dir(self):
        ids = get_existing_tweet_ids("/nonexistent/path")
        assert ids == set()

    def test_missing_tweet_id(self, tmp_path):
        (tmp_path / "tweet.md").write_text("---\nauthor: test\n---\nHello\n")
        ids = get_existing_tweet_ids(str(tmp_path))
        assert ids == set()

    def test_stops_at_non_frontmatter(self, tmp_path):
        (tmp_path / "tweet.md").write_text("Some random text\ntweet_id: \"999\"\n")
        ids = get_existing_tweet_ids(str(tmp_path))
        assert ids == set()


# ---------------------------------------------------------------------------
# cmd_download (video)
# ---------------------------------------------------------------------------

class TestDownloadVideo:
    def make_args(self, url="https://www.youtube.com/watch?v=abc", **kwargs):
        defaults = {
            "url": url,
            "output": None,
            "force": True,
            "limit": 0,
            "include_replies": False,
            "since": None,
            "until": None,
            "auth_token": None,
            "proxy": None,
        }
        defaults.update(kwargs)
        return Namespace(**defaults)

    @patch("yt_dlp.YoutubeDL")
    def test_youtube_opts(self, mock_ydl_cls, tmp_path):
        args = self.make_args(output=str(tmp_path))
        _download_video(args, args.url, "youtube")

        call_opts = mock_ydl_cls.call_args[0][0]
        assert "1080" in call_opts["format"]
        assert "download_archive" in call_opts

    @patch("yt_dlp.YoutubeDL")
    def test_tiktok_opts(self, mock_ydl_cls, tmp_path):
        args = self.make_args(
            url="https://www.tiktok.com/@user",
            output=str(tmp_path),
        )
        _download_video(args, args.url, "tiktok")

        call_opts = mock_ydl_cls.call_args[0][0]
        assert call_opts["format"] == "bestvideo+bestaudio/best"
        assert "download_archive" not in call_opts

    def test_aborts_when_not_confirmed(self, capsys):
        args = self.make_args(force=False)
        with patch("builtins.input", return_value="n"):
            _download_video(args, args.url, "youtube")
        assert "Aborted" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# cmd_download (X routing)
# ---------------------------------------------------------------------------

class TestDownloadRouting:
    def make_args(self, url, **kwargs):
        defaults = {
            "url": url,
            "output": None,
            "force": True,
            "limit": 0,
            "include_replies": False,
            "since": None,
            "until": None,
            "auth_token": None,
            "proxy": None,
        }
        defaults.update(kwargs)
        return Namespace(**defaults)

    @patch("ctk.cli._download_x")
    def test_routes_x_url(self, mock_dl_x):
        args = self.make_args("https://x.com/someuser")
        cmd_download(args)
        mock_dl_x.assert_called_once_with(args, "https://x.com/someuser")

    @patch("ctk.cli._download_video")
    def test_routes_youtube_url(self, mock_dl_video):
        args = self.make_args("https://youtube.com/watch?v=abc")
        cmd_download(args)
        mock_dl_video.assert_called_once_with(args, "https://youtube.com/watch?v=abc", "youtube")

    @patch("ctk.cli._download_video")
    def test_routes_tiktok_url(self, mock_dl_video):
        args = self.make_args("https://tiktok.com/@user")
        cmd_download(args)
        mock_dl_video.assert_called_once_with(args, "https://tiktok.com/@user", "tiktok")


# ---------------------------------------------------------------------------
# cmd_transcript
# ---------------------------------------------------------------------------

class TestTranscript:
    def make_args(self, input_dir, **kwargs):
        defaults = {
            "input_dir": input_dir,
            "output": None,
            "force": True,
            "split": False,
            "limit": 0,
            "accurate": False,
            "model": None,
            "subs": False,
        }
        defaults.update(kwargs)
        return Namespace(**defaults)

    @patch("ctk.cli.transcribe_whisper", return_value="Hello world. This is a test.")
    def test_creates_markdown(self, mock_whisper, tmp_path):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        (video_dir / "20240101-test-abc123.mp4").write_bytes(b"\x00")

        out_dir = tmp_path / "out"
        args = self.make_args(str(video_dir), output=str(out_dir))
        cmd_transcript(args)

        md_file = out_dir / "20240101-test-abc123.md"
        assert md_file.exists()
        content = md_file.read_text()
        assert content.startswith("# 20240101-test-abc123")
        assert "Hello world" in content

    @patch("ctk.cli.transcribe_whisper", return_value="First. Second. Third.")
    def test_split_mode(self, mock_whisper, tmp_path):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        (video_dir / "video.mp4").write_bytes(b"\x00")

        out_dir = tmp_path / "out"
        args = self.make_args(str(video_dir), output=str(out_dir), split=True)
        cmd_transcript(args)

        content = (out_dir / "video.md").read_text()
        assert "First.\nSecond.\nThird." in content

    @patch("ctk.cli.transcribe_whisper", return_value="Some text here.")
    def test_skips_existing(self, mock_whisper, tmp_path):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        (video_dir / "existing.mp4").write_bytes(b"\x00")

        out_dir = tmp_path / "out"
        out_dir.mkdir()
        (out_dir / "existing.md").write_text("already here")

        args = self.make_args(str(video_dir), output=str(out_dir))
        cmd_transcript(args)

        # whisper should not have been called
        mock_whisper.assert_not_called()

    @patch("ctk.cli.transcribe_whisper", return_value="text")
    def test_limit(self, mock_whisper, tmp_path):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        for i in range(5):
            (video_dir / f"video{i}.mp4").write_bytes(b"\x00")

        out_dir = tmp_path / "out"
        args = self.make_args(str(video_dir), output=str(out_dir), limit=2)
        cmd_transcript(args)

        assert mock_whisper.call_count == 2

    @patch("ctk.cli.transcribe_whisper", return_value=None)
    def test_failed_transcription(self, mock_whisper, tmp_path, capsys):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        (video_dir / "bad.mp4").write_bytes(b"\x00")

        out_dir = tmp_path / "out"
        args = self.make_args(str(video_dir), output=str(out_dir))
        cmd_transcript(args)

        assert not (out_dir / "bad.md").exists()
        output = capsys.readouterr().out
        assert "Failed (1)" in output

    def test_nonexistent_dir(self):
        args = self.make_args("/nonexistent/path")
        with pytest.raises(SystemExit):
            cmd_transcript(args)

    def test_accurate_sets_model(self, tmp_path, capsys):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        # no mp4s, just check the confirmation output
        args = self.make_args(str(video_dir), accurate=True)
        cmd_transcript(args)
        output = capsys.readouterr().out
        assert "large-v3" in output

    def test_model_override(self, tmp_path, capsys):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        args = self.make_args(str(video_dir), model="medium")
        cmd_transcript(args)
        output = capsys.readouterr().out
        assert "medium" in output

    def test_aborts_when_not_confirmed(self, tmp_path, capsys):
        video_dir = tmp_path / "videos"
        video_dir.mkdir()
        (video_dir / "test.mp4").write_bytes(b"\x00")

        args = self.make_args(str(video_dir), force=False)
        with patch("builtins.input", return_value="n"):
            cmd_transcript(args)
        assert "Aborted" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

class TestArgParsing:
    def test_download_parses(self):
        with patch("ctk.cli.cmd_download") as mock:
            with patch("sys.argv", ["ctk", "download", "https://youtube.com/watch?v=x"]):
                main()
            args = mock.call_args[0][0]
            assert args.url == "https://youtube.com/watch?v=x"
            assert args.force is False

    def test_force_flag(self):
        with patch("ctk.cli.cmd_download") as mock:
            with patch("sys.argv", ["ctk", "-f", "download", "https://youtube.com/watch?v=x"]):
                main()
            assert mock.call_args[0][0].force is True

    def test_transcript_parses(self):
        with patch("ctk.cli.cmd_transcript") as mock:
            with patch("sys.argv", ["ctk", "transcript", "/some/dir", "--split", "--limit", "5"]):
                main()
            args = mock.call_args[0][0]
            assert args.input_dir == "/some/dir"
            assert args.split is True
            assert args.limit == 5

    def test_download_x_options(self):
        with patch("ctk.cli.cmd_download") as mock:
            with patch("sys.argv", [
                "ctk", "download", "https://x.com/user",
                "-l", "50", "--since", "2024-01-01", "--include-replies",
            ]):
                main()
            args = mock.call_args[0][0]
            assert args.limit == 50
            assert args.since == "2024-01-01"
            assert args.include_replies is True

    def test_no_command_fails(self):
        with patch("sys.argv", ["ctk"]):
            with pytest.raises(SystemExit):
                main()
