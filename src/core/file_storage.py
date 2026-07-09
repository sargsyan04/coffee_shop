import io
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from PIL import Image, ImageChops, ImageOps

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}

MAX_SIZE = (256, 256)

def trim_whitespace(image: Image.Image, tolerance: int = 12) -> Image.Image:
    """Обрезает однородные поля по краям (белый/бежевый фон вокруг продукта)."""
    background = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, background)
    diff = ImageChops.add(diff, diff, 2.0, -tolerance)
    bbox = diff.getbbox()
    return image.crop(bbox) if bbox else image


def save_image(file: UploadFile, folder: str, resize: tuple[int, int] = MAX_SIZE) -> str:
    """Сохраняет файл на диск с изменением размера, возвращает веб-путь для БД."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Разрешены только JPEG, PNG, WEBP")

    media_dir = Path("media") / folder
    media_dir.mkdir(parents=True, exist_ok=True)

    # Читаем файл в память
    raw_bytes = file.file.read()

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.verify()  # проверка, что это валидная картинка
    except Exception:
        raise HTTPException(400, "Файл повреждён или не является изображением")

    # Открываем заново после verify() — Image.verify() "портит" объект для дальнейшей работы
    image = Image.open(io.BytesIO(raw_bytes))

    # Конвертируем в RGB, если это PNG с прозрачностью и сохраняем в JPEG — иначе будет ошибка
    if image.mode in ("RGBA", "P") and file.content_type == "image/jpeg":
        image = image.convert("RGB")

    image = Image.open(io.BytesIO(raw_bytes))

    # обрезаем пустые поля вокруг продукта
    image = trim_whitespace(image)

    # вписываем в квадрат, заполняя рамку целиком (а не просто уменьшая)
    image = ImageOps.fit(image, resize, Image.LANCZOS)

    # Изменение размера с сохранением пропорций (не увеличивает маленькие картинки)
    image.thumbnail(resize, Image.LANCZOS)

    # Определяем расширение и формат для сохранения
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
    """Удаляет старый файл, если он был."""
    if not image_url:
        return
    old_path = Path("media") / image_url.removeprefix("/media/")
    old_path.unlink(missing_ok=True)
