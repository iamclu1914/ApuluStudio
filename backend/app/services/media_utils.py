from app.models.social_account import Platform


DEFAULT_PLATFORM_ASPECT_RATIOS: dict[Platform, str] = {
    Platform.INSTAGRAM: "4:5",
    Platform.FACEBOOK: "16:9",
    Platform.THREADS: "4:5",
    Platform.TIKTOK: "9:16",
    Platform.X: "16:9",
    Platform.BLUESKY: "16:9",
    Platform.LINKEDIN: "16:9",
}


def get_default_aspect_ratio(platform: Platform) -> str | None:
    return DEFAULT_PLATFORM_ASPECT_RATIOS.get(platform)
