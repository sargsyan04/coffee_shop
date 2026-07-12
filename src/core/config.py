from pydantic import SecretStr
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

load_dotenv()


class Settings(BaseSettings):

    # --> JWT & Auth <--
    SECRET_KEY: SecretStr
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 15
    DEACTIVATION_GRACE_PERIOD_DAYS: int = 30

    # --> SMTP / Email Delivery <--
    MAIL_FROM: str = ""
    MAIL_PORT: int = 465
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # --> Database <--
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str
    DB_NAME: str

    # --> Initial Admin Account — seeded once on startup if no admin exists yet <--
    ADMIN_EMAIL: str = "admin@coffeeshop.local"
    ADMIN_PASSWORD: str = "change-me-please"
    ADMIN_NAME: str = "Administrator"


settings = Settings()

# --> Database Engine & Session Setup <--
database_url = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

engine = create_async_engine(database_url)
session_factory = async_sessionmaker(engine)


async def db_session():
    """FastAPI dependency — use with Depends(db_session).
    Not meant to be called directly as an async context manager
    (use session_factory() for that, e.g. in startup/lifespan code)."""
    async with session_factory() as session:
        yield session
        await session.close()