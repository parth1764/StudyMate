"""YouTube ingestion: pulls the existing caption track for a video (no audio
download, no speech-to-text) and its title, so it can be indexed the same way
as an uploaded transcript file.
"""

from urllib.parse import parse_qs, urlparse

import httpx
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

_PREFERRED_LANGUAGES = ("en", "en-US", "en-GB")


class YouTubeIngestError(ValueError):
    pass


def extract_video_id(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().removeprefix("www.")

    video_id = ""
    if host == "youtu.be":
        video_id = parsed.path.lstrip("/").split("/")[0]
    elif host in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/shorts/", "/embed/", "/live/")):
            parts = parsed.path.split("/")
            video_id = parts[2] if len(parts) > 2 else ""

    if not video_id or len(video_id) != 11:
        raise YouTubeIngestError(f"Could not extract a YouTube video ID from: {url}")
    return video_id


def fetch_transcript(video_id: str) -> str:
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=_PREFERRED_LANGUAGES)
    except (NoTranscriptFound, TranscriptsDisabled, VideoUnavailable):
        try:
            transcript_list = api.list(video_id)
            transcript = next(iter(transcript_list))
            fetched = transcript.fetch()
        except TranscriptsDisabled as exc:
            raise YouTubeIngestError("Captions are disabled for this video.") from exc
        except VideoUnavailable as exc:
            raise YouTubeIngestError("This video is unavailable.") from exc
        except (NoTranscriptFound, StopIteration) as exc:
            raise YouTubeIngestError("No captions are available for this video.") from exc
    except Exception as exc:
        raise YouTubeIngestError(f"Failed to fetch transcript: {exc}") from exc

    text = " ".join(snippet.text.strip() for snippet in fetched if snippet.text.strip())
    if not text:
        raise YouTubeIngestError("The transcript for this video was empty.")
    return text


def fetch_title(video_id: str) -> str:
    oembed_url = (
        f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}"
        "&format=json"
    )
    try:
        resp = httpx.get(oembed_url, timeout=10)
        resp.raise_for_status()
        return resp.json().get("title", video_id)
    except Exception:
        return video_id
