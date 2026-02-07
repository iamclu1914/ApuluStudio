"""Utility functions for the Apulu Suite backend."""


VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"]


def detect_media_type(url: str) -> str:
    """
    Detect if a URL points to an image or video based on extension.

    Args:
        url: The media URL to analyze

    Returns:
        "video" if the URL appears to be a video, "image" otherwise
    """
    url_lower = url.lower()
    if any(ext in url_lower for ext in VIDEO_EXTENSIONS):
        return "video"
    return "image"


def detect_media_types(urls: list[str]) -> list[str]:
    """
    Detect media types for a list of URLs.

    Args:
        urls: List of media URLs to analyze

    Returns:
        List of media types ("image" or "video") for each URL
    """
    return [detect_media_type(url) for url in urls]
