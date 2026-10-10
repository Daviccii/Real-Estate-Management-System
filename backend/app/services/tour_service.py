"""Virtual-tour URL handling (P4-36).

Owners/managers paste a 360° tour *share* URL (Matterport, Kuula, RoundMe,
Sketchfab, YouTube). Only the provider sites below are embeddable, and the
embed URL is always REBUILT from the extracted identifier — the raw
user-supplied URL is never placed into an iframe src. Anything else stays a
plain link (`embed_url = None`), so an attacker cannot smuggle an arbitrary
https page into an iframe through this field.

Rules enforced in `parse_tour_url`:
- https scheme only, no whitespace/control characters;
- provider match on the parsed hostname (userinfo tricks like
  ``https://my.matterport.com@evil.com/…`` resolve to host ``evil.com`` and
  therefore match nothing);
- provider ids must match a strict charset before any embed URL is built.
"""
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

EMBEDDABLE_PROVIDERS = ("matterport", "kuula", "roundme", "sketchfab", "youtube")

_MATTERPORT_ID = re.compile(r"^[A-Za-z0-9]{6,64}$")
_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{6,20}$")
_KUULA_ID = re.compile(r"^[A-Za-z0-9_-]{4,64}$")
_ROUNDME_ID = re.compile(r"^[0-9]{3,20}$")
_SKETCHFAB_ID = re.compile(r"^[0-9a-f]{32}$", re.IGNORECASE)

MAX_URL_LENGTH = 1000


@dataclass(frozen=True)
class ParsedTour:
    provider: str
    embed_url: Optional[str]


def _host_matches(hostname: str, domain: str) -> bool:
    host = hostname.lower()
    return host == domain or host.endswith(f".{domain}")


def _parse_matterport(parsed) -> Optional[str]:
    parts = [p for p in parsed.path.split("/") if p]
    tour_id: Optional[str] = None
    if "show" in parts:
        tour_id = (parse_qs(parsed.query).get("m") or [None])[0]
    elif "models" in parts:
        idx = parts.index("models")
        if idx + 1 < len(parts):
            tour_id = parts[idx + 1]
    if tour_id and _MATTERPORT_ID.match(tour_id):
        return f"https://my.matterport.com/show/?m={tour_id}"
    return None


def _parse_kuula(parsed) -> Optional[str]:
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] in ("share", "post") and _KUULA_ID.match(parts[1]):
        return f"https://kuula.co/share/{parts[1]}"
    return None


def _parse_roundme(parsed) -> Optional[str]:
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "tour" and _ROUNDME_ID.match(parts[1]):
        return f"https://roundme.com/tour/{parts[1]}/"
    return None


def _parse_sketchfab(parsed) -> Optional[str]:
    parts = [p for p in parsed.path.split("/") if p]
    candidate: Optional[str] = None
    if len(parts) >= 2 and parts[0] == "3d-models":
        candidate = parts[1].rsplit("-", 1)[-1]
    elif len(parts) >= 2 and parts[0] == "models":
        candidate = parts[1]
    if candidate and _SKETCHFAB_ID.match(candidate):
        return f"https://sketchfab.com/models/{candidate.lower()}/embed"
    return None


def _parse_youtube(parsed) -> Optional[str]:
    host = parsed.hostname.lower()
    parts = [p for p in parsed.path.split("/") if p]
    video_id: Optional[str] = None
    if _host_matches(host, "youtu.be"):
        if parts:
            video_id = parts[0]
    elif "watch" in parts:
        video_id = (parse_qs(parsed.query).get("v") or [None])[0]
    elif parts and parts[0] in ("shorts", "embed", "live") and len(parts) >= 2:
        video_id = parts[1]
    if video_id and _YOUTUBE_ID.match(video_id):
        # Privacy-enhanced embed host; 360° videos play the same way.
        return f"https://www.youtube-nocookie.com/embed/{video_id}"
    return None


def parse_tour_url(raw: str) -> ParsedTour:
    """Classify a tour share URL. Raises ValueError for anything unusable."""
    if not raw or not raw.strip():
        raise ValueError("Tour URL is required")
    url = raw.strip()
    if len(url) > MAX_URL_LENGTH:
        raise ValueError("Tour URL is too long")
    if any(ch.isspace() or ord(ch) < 0x20 for ch in url):
        raise ValueError("Tour URL must not contain spaces or control characters")

    try:
        parsed = urlparse(url)
    except ValueError:
        raise ValueError("Enter a valid URL")
    if parsed.scheme.lower() != "https":
        raise ValueError("Tour links must start with https://")
    if not parsed.hostname:
        raise ValueError("Enter a valid URL")

    host = parsed.hostname.lower()
    if _host_matches(host, "matterport.com"):
        return ParsedTour("matterport", _parse_matterport(parsed))
    if _host_matches(host, "kuula.co"):
        return ParsedTour("kuula", _parse_kuula(parsed))
    if _host_matches(host, "roundme.com"):
        return ParsedTour("roundme", _parse_roundme(parsed))
    if _host_matches(host, "sketchfab.com"):
        return ParsedTour("sketchfab", _parse_sketchfab(parsed))
    if _host_matches(host, "youtube.com") or _host_matches(host, "youtu.be"):
        return ParsedTour("youtube", _parse_youtube(parsed))

    # Not a provider we can safely embed — keep it as an external link only.
    return ParsedTour("link", None)
