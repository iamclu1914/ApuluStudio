from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.post import CaptionGenerateRequest, CaptionGenerateResponse
from app.services.ai_service import AIService
from app.models.social_account import Platform
from app.api.deps import CurrentActiveUser

router = APIRouter()


def get_ai_service() -> AIService:
    """Dependency for AI service."""
    try:
        return AIService()
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/generate-caption", response_model=CaptionGenerateResponse)
async def generate_caption(
    data: CaptionGenerateRequest,
    ai_service: Annotated[AIService, Depends(get_ai_service)],
):
    """Generate caption variations for a topic."""
    try:
        result = await ai_service.generate_captions(
            topic=data.topic,
            url=data.url,
            tone=data.tone,
            platform=data.platform,
            include_hashtags=data.include_hashtags,
            max_length=data.max_length,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-hashtags")
async def generate_hashtags(
    content: str,
    platform: Platform | None = None,
    count: int = 10,
    ai_service: Annotated[AIService, Depends(get_ai_service)] = None,
):
    """Generate hashtags for content."""
    try:
        hashtags = await ai_service.generate_hashtags(
            content=content,
            platform=platform,
            count=count,
        )
        return {"hashtags": hashtags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-content")
async def optimize_content(
    content: str,
    target_platform: Platform,
    source_platform: Platform | None = None,
    ai_service: Annotated[AIService, Depends(get_ai_service)] = None,
):
    """Optimize content for a specific platform."""
    try:
        optimized = await ai_service.optimize_for_platform(
            content=content,
            source_platform=source_platform,
            target_platform=target_platform,
        )
        return {
            "original": content,
            "optimized": optimized,
            "target_platform": target_platform.value,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/character-limits")
async def get_character_limits():
    """Get character limits for all platforms."""
    return {
        "limits": {
            Platform.X.value: 280,
            Platform.INSTAGRAM.value: 2200,
            Platform.FACEBOOK.value: 63206,
            Platform.LINKEDIN.value: 3000,
            Platform.THREADS.value: 500,
            Platform.BLUESKY.value: 300,
            Platform.TIKTOK.value: 2200,
        }
    }
