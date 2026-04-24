import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_async_session():
    """Create a mock async database session."""
    session = AsyncMock()
    execute_result = AsyncMock()
    session.execute = execute_result
    return session


@pytest.fixture
def mock_redis():
    """Create a mock redis client."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request object."""
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def mock_db_connection():
    """Mock the database engine and session for testing without real DB."""
    with patch("app.db.session.get_engine") as mock_engine, \
         patch("app.db.session.Sessions") as mock_sessions, \
         patch("app.db.session.AsyncSession") as mock_async_session_cls:
        mock_async_session_cls.return_value.__aenter__ = AsyncMock()
        mock_async_session_cls.return_value.__aexit__ = AsyncMock()
        yield mock_async_session_cls
