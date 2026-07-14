"""YouTube video transcript extraction and summarization prep."""

import logging
import re
from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi

logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
        r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_youtube_transcript(url: str) -> dict[str, Any]:
    """Fetch transcript for a YouTube video."""
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    logger.info("Fetching YouTube transcript for video: %s", video_id)

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = None
        try:
            transcript = transcript_list.find_transcript(["en"])
        except Exception:
            for t in transcript_list:
                transcript = t
                break

        if transcript is None:
            raise ValueError("No transcript available for this video")

        entries = transcript.fetch()
        segments = [{"start": e.start, "text": e.text, "duration": e.duration} for e in entries]
        full_text = " ".join(e.text for e in entries)

        return {
            "video_id": video_id,
            "url": url,
            "segments": segments,
            "full_text": full_text,
            "segment_count": len(segments),
        }
    except Exception:
        logger.exception("Failed to get YouTube transcript for %s", url)
        raise


def format_transcript_with_timestamps(data: dict[str, Any]) -> str:
    """Format transcript with timestamps for LLM."""
    lines = [f"YouTube Video: {data['url']}\n"]
    for seg in data.get("segments", [])[:200]:
        minutes = int(seg["start"] // 60)
        seconds = int(seg["start"] % 60)
        lines.append(f"[{minutes:02d}:{seconds:02d}] {seg['text']}")
    return "\n".join(lines)
