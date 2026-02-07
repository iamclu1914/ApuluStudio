import io
import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image

from app.core.database import get_supabase_admin
from app.core.config import get_settings

settings = get_settings()


# Aspect ratio numeric values for cropping (using string keys)
ASPECT_RATIOS = {
    "1:1": 1.0,
    "4:5": 4 / 5,
    "16:9": 16 / 9,
    "9:16": 9 / 16,
}


class StorageService:
    """Service for handling file uploads to Supabase Storage."""

    BUCKET_NAME = "media"
    ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm"}
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB

    def __init__(self):
        self.client = get_supabase_admin()

    async def upload_image(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        user_id: str,
        aspect_ratio: str | None = None,
    ) -> dict:
        """
        Upload an image to Supabase Storage.

        Args:
            file_data: Raw image bytes
            file_name: Original file name
            content_type: MIME type
            user_id: User ID for path
            aspect_ratio: If provided, auto-crop image to this ratio (e.g., "4:5", "1:1")
        """
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Invalid image type: {content_type}")

        if len(file_data) > self.MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large. Max size: {self.MAX_IMAGE_SIZE // 1024 // 1024}MB")

        # Auto-crop if aspect ratio specified
        processed_data = file_data
        was_cropped = False
        original_size = None
        new_size = None

        if aspect_ratio and aspect_ratio != "original":
            processed_data, was_cropped, original_size, new_size = self._crop_to_aspect_ratio(
                file_data, aspect_ratio
            )

        result = await self._upload_file(
            file_data=processed_data,
            file_name=file_name,
            content_type=content_type,
            user_id=user_id,
            folder="images",
        )

        # Add crop info to result
        if was_cropped:
            result["cropped"] = True
            result["original_size"] = original_size
            result["new_size"] = new_size
            result["aspect_ratio"] = aspect_ratio

        return result

    async def upload_image_with_variants(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        user_id: str,
        primary_aspect_ratio: str | None = None,
        variants: dict[str, str] | None = None,
    ) -> dict:
        """
        Upload an image and generate per-platform variants.

        Args:
            file_data: Raw image bytes
            file_name: Original file name
            content_type: MIME type
            user_id: User ID for path
            primary_aspect_ratio: Optional crop for the primary image
            variants: Mapping of variant key -> aspect ratio (e.g., "instagram": "1:1")
        """
        if content_type not in self.ALLOWED_IMAGE_TYPES:
            raise ValueError(f"Invalid image type: {content_type}")

        if len(file_data) > self.MAX_IMAGE_SIZE:
            raise ValueError(f"Image too large. Max size: {self.MAX_IMAGE_SIZE // 1024 // 1024}MB")

        variants = variants or {}

        ext = Path(file_name).suffix or ".jpg"
        base_id = uuid.uuid4()
        date_path = datetime.utcnow().strftime("%Y/%m")
        base_name = f"{base_id}{ext}"
        base_path = f"{user_id}/images/{date_path}/{base_name}"

        # Prepare primary image (optionally cropped)
        primary_data = file_data
        if primary_aspect_ratio and primary_aspect_ratio != "original":
            primary_data, _, _, _ = self._crop_to_aspect_ratio(
                file_data, primary_aspect_ratio
            )
            content_type = "image/jpeg"

        primary_result = await self._upload_file(
            file_data=primary_data,
            file_name=base_name,
            content_type=content_type,
            user_id=user_id,
            folder="images",
            file_path=base_path,
        )

        variant_results: dict[str, dict] = {}
        for variant_key, aspect_ratio in variants.items():
            if not aspect_ratio or aspect_ratio == "original":
                variant_results[variant_key] = {
                    "url": primary_result.get("url"),
                    "aspect_ratio": "original",
                    "cropped": False,
                }
                continue

            cropped_data, was_cropped, original_size, new_size = self._crop_to_aspect_ratio(
                file_data, aspect_ratio
            )
            variant_name = f"{base_id}__{variant_key}{ext}"
            variant_path = f"{user_id}/images/{date_path}/{variant_name}"
            variant_result = await self._upload_file(
                file_data=cropped_data,
                file_name=variant_name,
                content_type="image/jpeg",
                user_id=user_id,
                folder="images",
                file_path=variant_path,
            )
            variant_results[variant_key] = {
                "url": variant_result.get("url"),
                "aspect_ratio": aspect_ratio,
                "cropped": was_cropped,
                "original_size": original_size,
                "new_size": new_size,
            }

        return {
            **primary_result,
            "variants": variant_results,
        }

    def _crop_to_aspect_ratio(
        self,
        image_data: bytes,
        aspect_ratio: str,
    ) -> tuple[bytes, bool, tuple[int, int], tuple[int, int]]:
        """
        Crop image to specified aspect ratio using center crop.

        Returns:
            (processed_bytes, was_cropped, original_size, new_size)
        """
        img = Image.open(io.BytesIO(image_data))
        original_size = (img.width, img.height)

        # Convert to RGB if needed
        if img.mode in ("RGBA", "P", "LA"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode in ("RGBA", "LA"):
                background.paste(img, mask=img.split()[-1])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        target_ratio = ASPECT_RATIOS.get(aspect_ratio)
        if not target_ratio:
            # Return original if unknown ratio
            return image_data, False, original_size, original_size

        current_ratio = img.width / img.height

        # Check if already correct ratio (within 1% tolerance)
        if abs(current_ratio - target_ratio) < 0.01:
            return image_data, False, original_size, original_size

        # Center crop to target ratio
        if current_ratio > target_ratio:
            # Image is too wide, crop width
            new_width = int(img.height * target_ratio)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is too tall, crop height
            new_height = int(img.width / target_ratio)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))

        new_size = (img.width, img.height)

        # Save to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95, optimize=True)

        return buffer.getvalue(), True, original_size, new_size

    async def upload_video(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        user_id: str,
    ) -> dict:
        """Upload a video to Supabase Storage."""
        if content_type not in self.ALLOWED_VIDEO_TYPES:
            raise ValueError(f"Invalid video type: {content_type}")

        if len(file_data) > self.MAX_VIDEO_SIZE:
            raise ValueError(f"Video too large. Max size: {self.MAX_VIDEO_SIZE // 1024 // 1024}MB")

        return await self._upload_file(
            file_data=file_data,
            file_name=file_name,
            content_type=content_type,
            user_id=user_id,
            folder="videos",
        )

    async def _upload_file(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        user_id: str,
        folder: str,
        file_path: str | None = None,
    ) -> dict:
        """Internal method to upload a file."""
        # Generate unique file path
        if not file_path:
            ext = Path(file_name).suffix
            unique_name = f"{uuid.uuid4()}{ext}"
            date_path = datetime.utcnow().strftime("%Y/%m")
            file_path = f"{user_id}/{folder}/{date_path}/{unique_name}"

        try:
            # Upload to Supabase Storage
            result = self.client.storage.from_(self.BUCKET_NAME).upload(
                path=file_path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": "false",
                },
            )

            # Get public URL
            public_url = self.client.storage.from_(self.BUCKET_NAME).get_public_url(file_path)

            return {
                "success": True,
                "path": file_path,
                "url": public_url,
                "content_type": content_type,
                "size": len(file_data),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file from storage."""
        try:
            self.client.storage.from_(self.BUCKET_NAME).remove([file_path])
            return True
        except Exception:
            return False

    async def get_signed_url(
        self,
        file_path: str,
        expires_in: int = 3600,
    ) -> str | None:
        """Get a signed URL for private file access."""
        try:
            result = self.client.storage.from_(self.BUCKET_NAME).create_signed_url(
                path=file_path,
                expires_in=expires_in,
            )
            return result.get("signedURL")
        except Exception:
            return None

    async def list_user_files(
        self,
        user_id: str,
        folder: str = "",
        limit: int = 100,
    ) -> list[dict]:
        """List files for a user."""
        try:
            path = f"{user_id}/{folder}" if folder else user_id
            result = self.client.storage.from_(self.BUCKET_NAME).list(
                path=path,
                options={"limit": limit},
            )
            return result
        except Exception:
            return []

    @staticmethod
    def build_variant_url(original_url: str, variant_key: str) -> str | None:
        """Build a variant URL by inserting a suffix before the file extension."""
        if not original_url:
            return None

        base_url = original_url.split("?", 1)[0]
        last_dot = base_url.rfind(".")
        if last_dot == -1:
            return None

        return f"{base_url[:last_dot]}__{variant_key}{base_url[last_dot:]}"
