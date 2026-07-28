"""
Async loader that inserts fixture data into the database, resolving
cross-references (products -> categories/tags).

Idempotent by default: records are matched by natural keys (e.g. user email,
category name, tag slug, product name) and skipped if they already exist,
unless `force=True` is passed, in which case matching rows are deleted and
recreated.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.fixtures.data import (
    get_categories_fixtures,
    get_products_fixtures,
    get_super_admin_fixture,
    get_tags_fixtures,
    get_users_fixtures,
)
from src.models import Category, Product, Tag, User
from src.services import hash_password

# ============================================================
# --> Users <--
# ============================================================


async def _load_users(session: AsyncSession, fixtures: list[dict], force: bool) -> list[User]:
    created: list[User] = []
    for data in fixtures:
        existing = await session.scalar(select(User).where(User.email == data["email"]))
        if existing:
            if not force:
                print(f"  [skip] user already exists: {data['email']}")
                created.append(existing)
                continue
            await session.delete(existing)
            await session.flush()
            print(f"  [replace] user: {data['email']}")

        user = User(
            name=data["name"],
            email=data["email"],
            hashed_password=hash_password(data["password"]).decode("utf-8"),
            phone=data.get("phone"),
            address=data.get("address"),
            birth_date=data.get("birth_date"),
            role=data["role"],
            is_active=data.get("is_active", True),
            is_email_verified=data.get("is_email_verified", False),
            must_change_password=data.get("must_change_password", False),
        )
        session.add(user)
        await session.flush()
        created.append(user)
        print(f"  [created] user: {data['email']} (role={data['role'].value})")

    return created


async def load_users(session: AsyncSession, force: bool = False) -> list[User]:
    return await _load_users(session, get_users_fixtures(), force=force)


async def load_super_admin(session: AsyncSession, force: bool = False) -> User:
    users = await _load_users(session, [get_super_admin_fixture()], force=force)
    return users[0]


# ============================================================
# --> Categories <--
# ============================================================


async def load_categories(session: AsyncSession, force: bool = False) -> list[Category]:
    created: list[Category] = []
    for data in get_categories_fixtures():
        existing = await session.scalar(select(Category).where(Category.name == data["name"]))
        if existing:
            if not force:
                print(f"  [skip] category already exists: {data['name']}")
                created.append(existing)
                continue
            await session.delete(existing)
            await session.flush()
            print(f"  [replace] category: {data['name']}")

        category = Category(**data)
        session.add(category)
        await session.flush()
        created.append(category)
        print(f"  [created] category: {data['name']}")

    return created


# ============================================================
# --> Tags <--
# ============================================================


async def load_tags(session: AsyncSession, force: bool = False) -> list[Tag]:
    created: list[Tag] = []
    for data in get_tags_fixtures():
        existing = await session.scalar(select(Tag).where(Tag.slug == data["slug"]))
        if existing:
            if not force:
                print(f"  [skip] tag already exists: {data['slug']}")
                created.append(existing)
                continue
            await session.delete(existing)
            await session.flush()
            print(f"  [replace] tag: {data['slug']}")

        tag = Tag(**data)
        session.add(tag)
        await session.flush()
        created.append(tag)
        print(f"  [created] tag: {data['name']}")

    return created


# ============================================================
# --> Products <--
# ============================================================
# --> "category" references Category.name, "tags" references Tag.slug —
#     resolved here to real foreign keys, so categories/tags must already
#     exist (run load_categories()/load_tags() first, or use
#     `loaddata --models all`) <--


async def load_products(session: AsyncSession, force: bool = False) -> list[Product]:
    created: list[Product] = []
    for data in get_products_fixtures():
        existing = await session.scalar(select(Product).where(Product.name == data["name"]))
        if existing:
            if not force:
                print(f"  [skip] product already exists: {data['name']}")
                created.append(existing)
                continue
            await session.delete(existing)
            await session.flush()
            print(f"  [replace] product: {data['name']}")

        category = await session.scalar(select(Category).where(Category.name == data["category"]))
        if category is None:
            print(f"  [error] category '{data['category']}' not found — skipping product '{data['name']}'")
            continue

        tags = []
        for slug in data.get("tags", []):
            tag = await session.scalar(select(Tag).where(Tag.slug == slug))
            if tag:
                tags.append(tag)
            else:
                print(f"  [warn] tag '{slug}' not found for product '{data['name']}'")

        product = Product(
            name=data["name"],
            description=data.get("description"),
            price=data["price"],
            category_id=category.id,
            is_available=data.get("is_available", True),
        )
        product.tags = tags

        session.add(product)
        await session.flush()
        created.append(product)
        print(f"  [created] product: {data['name']}")

    return created


async def load_all(session: AsyncSession, force: bool = False) -> None:
    print("Loading users...")
    await load_users(session, force=force)

    print("Loading categories...")
    await load_categories(session, force=force)

    print("Loading tags...")
    await load_tags(session, force=force)

    print("Loading products...")
    await load_products(session, force=force)


LOADERS = {
    "users": load_users,
    "categories": load_categories,
    "tags": load_tags,
    "products": load_products,
}
