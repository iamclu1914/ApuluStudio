from datetime import datetime
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.schemas.post import CaptionVariation, CaptionGenerateResponse
from app.models.social_account import Platform

settings = get_settings()


class AIService:
    """AI service for caption generation and content optimization."""

    # Platform character limits
    PLATFORM_LIMITS = {
        Platform.X: 280,
        Platform.INSTAGRAM: 2200,
        Platform.FACEBOOK: 63206,
        Platform.LINKEDIN: 3000,
        Platform.THREADS: 500,
        Platform.BLUESKY: 300,
        Platform.TIKTOK: 2200,
    }

    def __init__(self):
        if settings.ai_provider == "openai" and settings.openai_api_key:
            self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
            self.anthropic = None
        elif settings.ai_provider == "anthropic" and settings.anthropic_api_key:
            self.anthropic = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.openai = None
        else:
            raise ValueError("No valid AI provider configured")

    async def generate_captions(
        self,
        topic: str,
        url: str | None = None,
        tone: str | None = None,
        platform: Platform | None = None,
        include_hashtags: bool = True,
        max_length: int | None = None,
    ) -> CaptionGenerateResponse:
        """Generate caption variations for a topic."""

        # Determine character limit
        char_limit = max_length or (
            self.PLATFORM_LIMITS.get(platform, 2200) if platform else 2200
        )

        # Build the prompt
        prompt = self._build_caption_prompt(
            topic=topic,
            url=url,
            tone=tone,
            char_limit=char_limit,
            include_hashtags=include_hashtags,
        )

        # Generate with selected provider
        if self.openai:
            response_text = await self._generate_openai(prompt)
        else:
            response_text = await self._generate_anthropic(prompt)

        # Parse the response into variations
        variations = self._parse_caption_response(response_text, include_hashtags)

        return CaptionGenerateResponse(
            topic=topic,
            variations=variations,
            generated_at=datetime.utcnow(),
        )

    async def generate_hashtags(
        self,
        content: str,
        platform: Platform | None = None,
        count: int = 10,
    ) -> list[str]:
        """Generate relevant hashtags for content."""

        prompt = f"""Generate {count} relevant hashtags for the following social media content.

Content: {content}

Requirements:
- Return only hashtags, one per line
- No # symbol, just the text
- Mix of popular and niche hashtags
- Relevant to the content topic
- {"Optimized for " + platform.value if platform else "General social media"}

Return format (one hashtag per line):
hashtag1
hashtag2
..."""

        if self.openai:
            response = await self._generate_openai(prompt)
        else:
            response = await self._generate_anthropic(prompt)

        hashtags = [
            tag.strip().lstrip("#")
            for tag in response.strip().split("\n")
            if tag.strip()
        ]
        return hashtags[:count]

    async def optimize_for_platform(
        self,
        content: str,
        source_platform: Platform | None,
        target_platform: Platform,
    ) -> str:
        """Optimize content for a specific platform."""

        char_limit = self.PLATFORM_LIMITS.get(target_platform, 2200)

        platform_guidance = {
            Platform.X: "concise, punchy, use threads for longer content",
            Platform.INSTAGRAM: "visual storytelling, call-to-action, emoji-friendly",
            Platform.FACEBOOK: "conversational, shareable, community-focused",
            Platform.LINKEDIN: "professional, thought leadership, industry insights",
            Platform.THREADS: "conversational, authentic, personality-driven",
            Platform.BLUESKY: "concise, community-oriented, no hashtag overuse",
            Platform.TIKTOK: "trendy, casual, hook-driven",
        }

        prompt = f"""Adapt the following content for {target_platform.value}.

Original content:
{content}

Platform requirements:
- Maximum {char_limit} characters
- Style: {platform_guidance.get(target_platform, "engaging and clear")}
- Maintain the core message
- Optimize for engagement on this platform

Return only the adapted content, nothing else."""

        if self.openai:
            return await self._generate_openai(prompt)
        else:
            return await self._generate_anthropic(prompt)

    def _build_caption_prompt(
        self,
        topic: str,
        url: str | None,
        tone: str | None,
        char_limit: int,
        include_hashtags: bool,
    ) -> str:
        """Build the caption generation prompt."""

        url_context = f"\nReference URL for context: {url}" if url else ""

        hashtag_instruction = """
Also provide 3-5 relevant hashtags.""" if include_hashtags else ""

        # Check if user specified length preferences in their request
        topic_lower = topic.lower()
        length_hint = ""
        if "short" in topic_lower or "brief" in topic_lower:
            length_hint = "Keep it SHORT - under 100 characters. Be punchy and direct."
        elif "long" in topic_lower or "detailed" in topic_lower:
            length_hint = f"Can be longer, up to {char_limit} characters if needed."
        else:
            length_hint = "Keep it concise but impactful - around 100-200 characters."

        return f"""Write a viral social media caption based on this request:

"{topic}"{url_context}

Instructions:
- Follow the user's request exactly - if they ask for a specific tone, style, or length, use it
- {length_hint}
- Be CREATIVE and write something that could go VIRAL - hooks, bold statements, relatable content
- Write authentically, not like generic marketing copy
- Match the vibe the user is asking for{hashtag_instruction}
- Use hashtags that are currently TRENDING and VIRAL - mix popular broad hashtags with niche ones that real people search

Format your response exactly like this:
---
TONE: [the tone/style you used]
CAPTION: [the caption - no quotes around it]
HASHTAGS: [comma-separated viral/trending hashtags without #]
---"""

    def _parse_caption_response(
        self,
        response: str,
        include_hashtags: bool,
    ) -> list[CaptionVariation]:
        """Parse the AI response into caption variations."""

        variations = []
        sections = response.split("---")

        for section in sections:
            section = section.strip()
            if not section:
                continue

            tone = ""
            caption = ""
            hashtags = []

            lines = section.split("\n")
            for line in lines:
                line = line.strip()
                if line.upper().startswith("TONE:"):
                    tone = line.split(":", 1)[1].strip().lower()
                elif line.upper().startswith("CAPTION:"):
                    caption = line.split(":", 1)[1].strip()
                elif line.upper().startswith("HASHTAGS:"):
                    hashtag_str = line.split(":", 1)[1].strip()
                    hashtags = [
                        h.strip().lstrip("#")
                        for h in hashtag_str.split(",")
                        if h.strip()
                    ]

            if tone and caption:
                variations.append(CaptionVariation(
                    tone=tone,
                    caption=caption,
                    hashtags=hashtags if include_hashtags else [],
                    character_count=len(caption),
                ))

        # Fallback if parsing fails
        if not variations:
            variations.append(CaptionVariation(
                tone="general",
                caption=response.strip()[:2200],
                hashtags=[],
                character_count=len(response.strip()[:2200]),
            ))

        return variations

    async def _generate_openai(self, prompt: str) -> str:
        """Generate text using OpenAI."""
        response = await self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You write viral social media captions. Be CREATIVE - write hooks, bold statements, and content that makes people stop scrolling. Follow the user's instructions exactly. Never write generic marketing fluff. Use trending hashtags that real people actually search for."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.8,
        )
        return response.choices[0].message.content

    async def _generate_anthropic(self, prompt: str) -> str:
        """Generate text using Anthropic."""
        response = await self.anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ],
            system="You write viral social media captions. Be CREATIVE - write hooks, bold statements, and content that makes people stop scrolling. Follow the user's instructions exactly. Never write generic marketing fluff. Use trending hashtags that real people actually search for.",
        )
        return response.content[0].text
