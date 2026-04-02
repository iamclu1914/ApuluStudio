from app.models.social_account import Platform


DEFAULT_PLATFORM_ASPECT_RATIOS: dict[Platform, str] = {
    Platform.INSTAGRAM: "original",
    Platform.FACEBOOK: "16:9",
    Platform.THREADS: "original",
    Platform.TIKTOK: "original",
    Platform.X: "original",
    Platform.BLUESKY: "original",
    Platform.LINKEDIN: "16:9",
}


def get_default_aspect_ratio(platform: Platform) -> str | None:
    return DEFAULT_PLATFORM_ASPECT_RATIOS.get(platform)
