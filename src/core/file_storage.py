import io
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageChops, ImageOps

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE = (256, 256)


# ============================================================
# --> Image Preprocessing Helpers <--
# ============================================================

def trim_whitespace(image: Image.Image, tolerance: int = 12) -> Image.Image:
    """Crops uniform padding around the edges (white/beige background around the product)."""
    background = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    diff = ImageChops.add(diff, diff, 2.0, -tolerance)
    bbox = diff.getbbox()
    return image.crop(bbox) if bbox else image


# ============================================================
# --> Image Upload & Storage <--
# ============================================================

def save_image(file: UploadFile, folder: str, resize: tuple[int, int] = MAX_SIZE) -> str:
    """Saves the uploaded file to disk after validating, cropping, and resizing it.
    Returns the web-facing path to store in the database."""

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Only JPEG, PNG, and WEBP are allowed")

    media_dir = Path("media") / folder
    media_dir.mkdir(parents=True, exist_ok=True)

    raw_bytes = file.file.read()

    # --> Step 1: validate that the file is actually a readable image <--
    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.verify()
    except Exception:
        raise HTTPException(400, "The file is corrupted or not a valid image")

    # --> Image.verify() invalidates the object for further use — reopen it <--
    image = Image.open(io.BytesIO(raw_bytes))

    # --> Step 2: convert to RGB if saving a transparent PNG as JPEG
    #     (JPEG has no alpha channel and would otherwise fail to save) <--
    if image.mode in ("RGBA", "P") and file.content_type == "image/jpeg":
        image = image.convert("RGB")

    image = Image.open(io.BytesIO(raw_bytes))

    # --> Step 3: crop empty padding around the product <--
    image = trim_whitespace(image)

    # --> Step 4: fit into a square, filling the frame entirely (not just shrinking) <--
    image = ImageOps.fit(image, resize, Image.LANCZOS)

    # --> Step 5: resize while preserving aspect ratio (never upscales small images) <--
    image.thumbnail(resize, Image.LANCZOS)

    # --> Step 6: determine the file extension and save format <--
    ext_map = {
        "image/jpeg": ("jpg", "JPEG"),
        "image/png": ("png", "PNG"),
        "image/webp": ("webp", "WEBP"),
    }
    extension, pil_format = ext_map[file.content_type]

    filename = f"{uuid.uuid4()}.{extension}"
    filepath = media_dir / filename

    save_kwargs = {"quality": 85} if pil_format in ("JPEG", "WEBP") else {}
    image.save(filepath, format=pil_format, **save_kwargs)

    return f"/media/{folder}/{filename}"


def delete_image(image_url: str | None) -> None:
    """Deletes the old file from disk, if one existed."""
    if not image_url:
        return
    old_path = Path("media") / image_url.removeprefix("/media/")
    old_path.unlink(missing_ok=True)