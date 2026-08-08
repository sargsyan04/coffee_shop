import io
import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("app.file_storage")

MEDIA_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "media"

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = (256, 256)


def center_crop_square(image: Image.Image) -> Image.Image:
    """Crop the image to a centered square by trimming the longer side."""
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def save_image(
    file: UploadFile,
    folder: str,
    filename_prefix: str,
    entity_id: int,
    resize: tuple[int, int] = MAX_SIZE,
) -> str:
    """
    Validate, process and save an uploaded image.

    Args:
        file: Uploaded image.
        folder: Folder inside the media directory.
        filename_prefix: Prefix for the filename (e.g. "product", "user").
        entity_id: ID of the entity the image belongs to.
        resize: Final image size.

    Returns:
        Relative path to the saved image.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG, PNG, and WEBP images are allowed.",
        )

    media_dir = MEDIA_ROOT / folder
    media_dir.mkdir(parents=True, exist_ok=True)

    raw_bytes = file.file.read()

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is corrupted or is not a valid image.",
        ) from exc

    # verify() leaves the image unusable, so it needs to be reopened
    image = Image.open(io.BytesIO(raw_bytes))

    # JPEG has no alpha channel, so drop it before saving
    if image.mode in ("RGBA", "LA", "P") and file.content_type == "image/jpeg":
        image = image.convert("RGB")

    image = center_crop_square(image)

    if image.width > resize[0]:
        image = image.resize(resize, Image.LANCZOS)
    else:
        image.thumbnail(resize, Image.LANCZOS)

    extension_map = {
        "image/jpeg": ("jpg", "JPEG"),
        "image/png": ("png", "PNG"),
        "image/webp": ("webp", "WEBP"),
    }
    extension, image_format = extension_map[file.content_type]

    filename = f"{filename_prefix}_{entity_id}-{uuid.uuid4().hex}.{extension}"
    filepath = media_dir / filename

    save_kwargs = {"quality": 85} if image_format in ("JPEG", "WEBP") else {}
    image.save(filepath, format=image_format, **save_kwargs)

    return f"/media/{folder}/{filename}"


def delete_image(image_url: str | None) -> None:
    if not image_url:
        return
    old_path = MEDIA_ROOT / image_url.removeprefix("/media/")
    try:
        old_path.unlink(missing_ok=True)
    except PermissionError:
        logger.warning("Could not delete old image %s - file is locked by another process", old_path)
    except OSError:
        logger.warning("Could not delete old image %s", old_path, exc_info=True)
