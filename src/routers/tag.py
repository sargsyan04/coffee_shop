import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import db_session
from src.models.tag import Tag
from src.schemas.tag import TagCreate, TagResponse

router = APIRouter(prefix="/tags", tags=["Tags"])


_CYRILLIC_TO_LATIN = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def _slugify(name: str) -> str:
    transliterated = "".join(_CYRILLIC_TO_LATIN.get(char, char) for char in name.lower())
    slug = re.sub(r"[^a-z0-9]+", "-", transliterated).strip("-")
    return slug or "tag"


async def _unique_slug(db: AsyncSession, name: str) -> str:
    base_slug = _slugify(name)
    slug = base_slug
    suffix = 2
    while (await db.execute(select(Tag).where(Tag.slug == slug))).scalar():
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


@router.post("/", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(db_session),
):
    existing = await db.execute(select(Tag).where(Tag.name == data.name))
    if existing.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tag with that name already exists",
        )

    tag = Tag(name=data.name, slug=await _unique_slug(db, data.name))
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("/", response_model=list[TagResponse])
async def get_tags(db: AsyncSession = Depends(db_session)):
    result = await db.execute(select(Tag))
    return result.scalars().all()
