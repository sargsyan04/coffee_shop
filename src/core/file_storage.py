import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

def save_image(file: UploadFile, folder: str) -> str:
    """Сохраняет файл на диск, возвращает веб-путь для БД."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Разрешены только JPEG, PNG, WEBP")

    media_dir = Path("media") / folder
    media_dir.mkdir(parents=True, exist_ok=True)

    extension = file.filename.rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = media_dir / filename

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return f"/media/{folder}/{filename}"


def delete_image(image_url: str | None) -> None:
    """Удаляет старый файл, если он был."""
    if not image_url:
        return
    old_path = Path("media") / image_url.removeprefix("/media/")
    old_path.unlink(missing_ok=True)