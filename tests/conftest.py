import itertools
import os
from datetime import UTC
from decimal import Decimal

# Settings() gets built the moment src.core.config is imported, so these
# need to exist before pytest touches anything under src/
os.environ.setdefault("SECRET_KEY", "pytest-secret-key")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_USER", "postgres")
os.environ.setdefault("DB_PASSWORD", "pytest")
os.environ.setdefault("DB_NAME", "pytest")
os.environ.setdefault("MAIL_FROM", "test@example.com")

import pytest
import pytest_asyncio
from sqlalchemy import BIGINT
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.sqlite import base as sqlite_base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator

from src.models.base import BaseModel
import src.models  # noqa: F401 - registers the models on BaseModel.metadata
from src.models import Order, Product, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# SQLite only auto-generates a primary key when the column type is exactly
# INTEGER - our models use BIGINT (fine on Postgres), which SQLite treats
# as a plain column with no auto-increment, so id stays NULL on insert.
@compiles(BIGINT, "sqlite")
def _bigint_as_integer_on_sqlite(type_, compiler, **kw):
    return "INTEGER"


# SQLite silently drops the tzinfo on DateTime(timezone=True) columns, so
# anything read back from the DB comes out as a naive datetime. That blows
# up any code comparing it against an aware datetime.now(UTC) - which works
# fine on real Postgres, just not here. This patches the datetime type used
# for THIS test engine only, so it hands back UTC-aware datetimes like Postgres would.
class _UTCDateTime(TypeDecorator):
    impl = sqlite_base.DATETIME
    cache_ok = True

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    # StaticPool, otherwise ':memory:' gives a fresh empty db per connection
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)
    engine.sync_engine.dialect.colspecs[SADateTime] = _UTCDateTime

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def user_factory(db_session):
    """Creates as many users as a test needs, with sane defaults that can be
    overridden (role, email, whatever). email has to be unique in the DB, so
    each call gets its own by default unless one is passed in explicitly.
    """
    email_counter = itertools.count(1)

    async def _make_user(**overrides) -> User:
        fields = {
            "email": f"user{next(email_counter)}@example.com",
            "hashed_password": "fakehash",
            "name": "Test User",
        }
        fields.update(overrides)

        user = User(**fields)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _make_user


@pytest_asyncio.fixture
async def order_factory(db_session):
    """Same idea as user_factory, but for orders - pass in the owning user
    (or a user_id override) plus whatever else the test cares about.
    """

    async def _make_order(user: User | None = None, **overrides) -> Order:
        fields = {
            "total_price": Decimal("1000.00"),
        }
        if user is not None:
            fields["user_id"] = user.id
        fields.update(overrides)

        order = Order(**fields)
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        return order

    return _make_order


@pytest_asyncio.fixture
async def product_factory(db_session):
    """Same idea as user_factory/order_factory - creates a Product with sane
    defaults (available, has a price), override whatever the test needs.
    """
    name_counter = itertools.count(1)

    async def _make_product(**overrides) -> Product:
        fields = {
            "name": f"Product {next(name_counter)}",
            "price": Decimal("500.00"),
            "is_available": True,
        }
        fields.update(overrides)

        product = Product(**fields)
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        return product

    return _make_product
