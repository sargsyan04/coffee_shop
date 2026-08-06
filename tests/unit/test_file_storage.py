import io
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from src.core.file_storage import center_crop_square, delete_image, save_image


def _make_upload_file(image: Image.Image, content_type: str, fmt: str) -> UploadFile:
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    buf.seek(0)
    return UploadFile(file=buf, filename=f"test.{fmt.lower()}", headers={"content-type": content_type})


# center_crop_square


def test_center_crop_square_wide_image():
    image = Image.new("RGB", (400, 200))

    cropped = center_crop_square(image)

    assert cropped.size == (200, 200)


def test_center_crop_square_tall_image():
    image = Image.new("RGB", (150, 500))

    cropped = center_crop_square(image)

    assert cropped.size == (150, 150)


def test_center_crop_square_already_square():
    image = Image.new("RGB", (300, 300))

    cropped = center_crop_square(image)

    assert cropped.size == (300, 300)


# save_image


def test_save_image_rejects_unsupported_content_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = Image.new("RGB", (100, 100))
    upload = _make_upload_file(image, "image/gif", "PNG")

    with pytest.raises(HTTPException) as exc_info:
        save_image(upload, folder="products", filename_prefix="Product", entity_id=1)

    assert exc_info.value.status_code == 400


def test_save_image_rejects_corrupted_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    upload = UploadFile(
        file=io.BytesIO(b"this is not a real image"),
        filename="broken.jpg",
        headers={"content-type": "image/jpeg"},
    )

    with pytest.raises(HTTPException) as exc_info:
        save_image(upload, folder="products", filename_prefix="Product", entity_id=1)

    assert exc_info.value.status_code == 400


def test_save_image_saves_and_returns_relative_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = Image.new("RGB", (400, 300), color="blue")
    upload = _make_upload_file(image, "image/jpeg", "JPEG")

    url = save_image(upload, folder="products", filename_prefix="Product", entity_id=7)

    assert url.startswith("/media/products/Product_7-")
    assert url.endswith(".jpg")
    saved_path = tmp_path / "media" / "products" / Path(url).name
    assert saved_path.exists()

    with Image.open(saved_path) as saved:
        # resized down to MAX_SIZE (256, 256) and cropped square
        assert saved.size == (256, 256)


def test_save_image_thumbnails_small_image_instead_of_upscaling(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = Image.new("RGB", (100, 100), color="green")
    upload = _make_upload_file(image, "image/png", "PNG")

    url = save_image(upload, folder="users", filename_prefix="User", entity_id=3)

    saved_path = tmp_path / "media" / "users" / Path(url).name
    with Image.open(saved_path) as saved:
        # thumbnail() only shrinks, so a 100x100 source should stay 100x100,
        # not get upscaled to 256x256
        assert saved.size == (100, 100)


def test_save_image_converts_rgba_png_to_jpeg_without_alpha(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = Image.new("RGBA", (200, 200), color=(255, 0, 0, 128))
    upload = _make_upload_file(image, "image/jpeg", "PNG")

    url = save_image(upload, folder="products", filename_prefix="Product", entity_id=9)

    saved_path = tmp_path / "media" / "products" / Path(url).name
    with Image.open(saved_path) as saved:
        assert saved.mode == "RGB"


# delete_image


def test_delete_image_removes_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    media_dir = tmp_path / "media" / "products"
    media_dir.mkdir(parents=True)
    file_path = media_dir / "old.jpg"
    file_path.write_bytes(b"fake image bytes")

    delete_image("/media/products/old.jpg")

    assert not file_path.exists()


def test_delete_image_missing_file_does_not_raise(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # should not raise even though the file was never created
    delete_image("/media/products/does-not-exist.jpg")


def test_delete_image_with_none_is_a_noop():
    # should not raise / not attempt any filesystem access
    delete_image(None)