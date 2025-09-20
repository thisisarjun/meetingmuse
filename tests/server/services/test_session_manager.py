"""Tests for SessionManager."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from server.models.session import TokenInfo, UserSession
from server.services.session_manager import SessionManager


@pytest.fixture
def session_manager(mock_storage_adapter, mock_logger):
    """Create a SessionManager instance for testing."""
    with patch("server.services.session_manager.config") as mock_config:
        mock_config.SESSION_ENCRYPTION_KEY = "test_key_123456789012345678901"
        return SessionManager(mock_storage_adapter, mock_logger)


@pytest.fixture
def sample_token_info():
    """Create sample token info for testing."""
    return TokenInfo(
        access_token="access_token_123",
        refresh_token="refresh_token_456",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scopes=["scope1", "scope2"],
    )


@pytest.fixture
def sample_session(sample_token_info):
    """Create sample session for testing."""
    return UserSession(
        session_id="session_123",
        client_id="client_456",
        tokens=sample_token_info,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


async def test_store_session_success(
    session_manager, mock_storage_adapter, sample_session
):
    """Test successful session storage."""
    mock_storage_adapter.set.return_value = True

    result = await session_manager.store_session(sample_session)

    assert result is True
    mock_storage_adapter.set.call_count == 2
    call_args = mock_storage_adapter.set.call_args_list
    assert call_args[0][0][0] == "client_456"  # session_id
    assert call_args[1][0][0] == "session_123"  # client_id


async def test_store_session_failure(
    session_manager, mock_storage_adapter, sample_session
):
    """Test session storage failure."""
    mock_storage_adapter.set.side_effect = Exception("Storage error")

    result = await session_manager.store_session(sample_session)

    assert result is False


async def test_get_session_success(
    session_manager, mock_storage_adapter, sample_session
):
    """Test successful session retrieval."""
    # Store the session first to get encrypted version
    encrypted_session = session_manager._encrypt_session(sample_session)
    mock_storage_adapter.get.return_value = encrypted_session.model_dump_json()

    result = await session_manager.get_session("session_123")

    assert result is not None
    assert result.session_id == "session_123"
    assert result.client_id == "client_456"
    assert result.tokens.access_token == "access_token_123"


async def test_get_session_not_found(session_manager, mock_storage_adapter):
    """Test session not found."""
    mock_storage_adapter.get.return_value = None

    result = await session_manager.get_session("nonexistent")

    assert result is None


async def test_get_session_expired(
    session_manager, mock_storage_adapter, sample_session
):
    """Test expired session removal."""
    # Create expired session
    expired_tokens = TokenInfo(
        access_token="access_token_123",
        refresh_token="refresh_token_456",
        token_expiry=datetime.now(timezone.utc) - timedelta(hours=1),  # Expired
        scopes=["scope1", "scope2"],
    )
    expired_session = UserSession(
        session_id="session_123",
        client_id="client_456",
        tokens=expired_tokens,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    encrypted_session = session_manager._encrypt_session(expired_session)
    mock_storage_adapter.get.return_value = encrypted_session.model_dump_json()
    mock_storage_adapter.delete.return_value = True

    result = await session_manager.get_session("session_123")

    assert result is None
    mock_storage_adapter.delete.assert_called_once_with("session_123")


async def test_update_session_tokens_success(
    session_manager, mock_storage_adapter, sample_session, sample_token_info
):
    """Test successful token update."""
    # Mock get_session to return existing session
    encrypted_session = session_manager._encrypt_session(sample_session)
    mock_storage_adapter.get.return_value = encrypted_session.model_dump_json()
    mock_storage_adapter.set.return_value = True

    new_tokens = TokenInfo(
        access_token="new_access_token",
        refresh_token="new_refresh_token",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=2),
        scopes=["new_scope"],
    )

    result = await session_manager.update_session_tokens("session_123", new_tokens)

    assert result is True


async def test_update_session_tokens_session_not_found(
    session_manager, mock_storage_adapter, sample_token_info
):
    """Test token update for non-existent session."""
    mock_storage_adapter.get.return_value = None

    result = await session_manager.update_session_tokens(
        "nonexistent", sample_token_info
    )

    assert result is False


async def test_delete_session(session_manager, mock_storage_adapter):
    """Test session deletion."""
    mock_storage_adapter.delete.return_value = True

    result = await session_manager.delete_session("session_123", "client_456")

    assert result is True
    mock_storage_adapter.delete.call_count == 2
    call_args = mock_storage_adapter.delete.call_args_list
    assert call_args[0][0][0] == "client_456"  # session_id
    assert call_args[1][0][0] == "session_123"  # client_id


async def test_is_token_valid_true(
    session_manager, mock_storage_adapter, sample_session
):
    """Test valid token check."""
    encrypted_session = session_manager._encrypt_session(sample_session)
    mock_storage_adapter.get.return_value = encrypted_session.model_dump_json()

    result = await session_manager.is_token_valid("session_123")

    assert result is True


async def test_is_token_valid_false(session_manager, mock_storage_adapter):
    """Test invalid token check."""
    mock_storage_adapter.get.return_value = None

    result = await session_manager.is_token_valid("session_123")

    assert result is False


async def test_get_session_by_client_id_success(
    session_manager, mock_storage_adapter, sample_session
):
    """Test finding session by client ID."""
    encrypted_session = session_manager._encrypt_session(sample_session)

    mock_storage_adapter.get.return_value = encrypted_session.model_dump_json()

    result = await session_manager.get_session_by_client_id("client_456")

    assert result is not None
    assert result.client_id == "client_456"


async def test_get_session_by_client_id_not_found(
    session_manager, mock_storage_adapter
):
    """Test client ID not found."""

    result = await session_manager.get_session_by_client_id("nonexistent")

    assert result is None


def test_encryption_decryption(session_manager, sample_session):
    """Test token encryption and decryption."""
    encrypted_session = session_manager._encrypt_session(sample_session)
    decrypted_session = session_manager._decrypt_session(encrypted_session)

    assert decrypted_session.session_id == sample_session.session_id
    assert decrypted_session.client_id == sample_session.client_id
    assert decrypted_session.tokens.access_token == sample_session.tokens.access_token
    assert decrypted_session.tokens.refresh_token == sample_session.tokens.refresh_token
