from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.exc import OperationalError

from src.core import db_session as get_db_session
from src.main import app

# The lifespan hook (default admin creation) is NOT triggered here:
# ASGITransport does not run startup/shutdown events, so these tests
# never touch a real database.


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
        yield http_client

    # Always remove overrides, otherwise they leak into other tests
    app.dependency_overrides.clear()


def override_session(session):
    """Make the app use `session` instead of a real database session."""

    async def _override():
        yield session

    app.dependency_overrides[get_db_session] = _override


async def test_health_ok_when_database_is_up(client, db_session):
    # `db_session` here is the SQLite fixture from tests/conftest.py
    override_session(db_session)

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


@pytest.mark.parametrize(
    "error",
    [
        OSError("connection refused"),
        OperationalError("SELECT 1", {}, Exception("server closed the connection")),
        TimeoutError(),
    ],
    ids=["os_error", "sqlalchemy_error", "timeout"],
)
async def test_health_503_when_database_is_down(client, error):
    broken_session = AsyncMock()
    broken_session.execute.side_effect = error
    override_session(broken_session)

    response = await client.get("/health")

    assert response.status_code == 503
    # Exactly the body from the spec, not wrapped into {"detail": ...}
    assert response.json() == {"status": "degraded", "database": "down"}


async def test_health_does_not_require_authentication(client, db_session):
    override_session(db_session)

    # No Authorization header at all
    response = await client.get("/health")

    assert response.status_code == 200


def test_health_response_schema_is_documented():
    # Swagger must describe the 200 response with the HealthResponse fields
    schema = app.openapi()["components"]["schemas"]["HealthResponse"]

    assert set(schema["properties"]) == {"status", "database"}
