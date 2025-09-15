"""Tests for RedisStorageAdapter."""

import pytest


@pytest.mark.asyncio
async def test_get_nonexistent_key(redis_adapter):
    """Test getting a nonexistent key returns None."""
    result = await redis_adapter.get("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_set_and_get(redis_adapter):
    """Test setting and getting a value."""
    key = "test_key"
    value = "test_value"

    # Set the value
    success = await redis_adapter.set(key, value)
    assert success is True

    # Get the value
    retrieved = await redis_adapter.get(key)
    assert retrieved == value


@pytest.mark.asyncio
async def test_set_overwrite(redis_adapter):
    """Test overwriting an existing key."""
    key = "test_key"
    value1 = "value1"
    value2 = "value2"

    # Set initial value
    await redis_adapter.set(key, value1)

    # Overwrite with new value
    success = await redis_adapter.set(key, value2)
    assert success is True

    # Verify new value
    retrieved = await redis_adapter.get(key)
    assert retrieved == value2


@pytest.mark.asyncio
async def test_delete_existing_key(redis_adapter):
    """Test deleting an existing key."""
    key = "test_key"
    value = "test_value"

    # Set a value first
    await redis_adapter.set(key, value)

    # Delete the key
    success = await redis_adapter.delete(key)
    assert success is True

    # Verify it's gone
    result = await redis_adapter.get(key)
    assert result is None


@pytest.mark.asyncio
async def test_delete_nonexistent_key(redis_adapter):
    """Test deleting a nonexistent key returns False."""
    success = await redis_adapter.delete("nonexistent")
    assert success is False


@pytest.mark.asyncio
async def test_get_all_by_prefix_empty(redis_adapter):
    """Test getting all keys by prefix when no matches exist."""
    result = await redis_adapter.get_all_by_prefix("test_")
    assert result == []


@pytest.mark.asyncio
async def test_get_all_by_prefix_with_matches(redis_adapter):
    """Test getting all keys by prefix with matching keys."""
    # Set up test data
    test_data = {
        "user_1": "data1",
        "user_2": "data2",
        "admin_1": "admin_data",
        "user_3": "data3",
    }

    for key, value in test_data.items():
        await redis_adapter.set(key, value)

    # Get all keys with "user_" prefix
    result = await redis_adapter.get_all_by_prefix("user_")

    # fakeredis returns a list of keys, not a dict
    # so we need to check that the right keys are returned
    expected_keys = ["user_1", "user_2", "user_3"]
    assert sorted(result) == sorted(expected_keys)


@pytest.mark.asyncio
async def test_multiple_operations(redis_adapter):
    """Test multiple operations in sequence."""
    # Set multiple keys
    keys_values = {"key1": "value1", "key2": "value2", "key3": "value3"}

    for key, value in keys_values.items():
        success = await redis_adapter.set(key, value)
        assert success is True

    # Get all values
    for key, expected_value in keys_values.items():
        actual_value = await redis_adapter.get(key)
        assert actual_value == expected_value

    # Delete one key
    success = await redis_adapter.delete("key2")
    assert success is True

    # Verify deletion
    assert await redis_adapter.get("key2") is None
    assert await redis_adapter.get("key1") == "value1"
    assert await redis_adapter.get("key3") == "value3"


@pytest.mark.asyncio
async def test_empty_string_value(redis_adapter):
    """Test setting and getting empty string values."""
    key = "empty_key"
    value = ""

    success = await redis_adapter.set(key, value)
    assert success is True

    retrieved = await redis_adapter.get(key)
    assert retrieved == value


@pytest.mark.asyncio
async def test_special_characters_in_key_and_value(redis_adapter):
    """Test keys and values with special characters."""
    key = "key:with:colons"
    value = "value with spaces and symbols !@#$%"

    success = await redis_adapter.set(key, value)
    assert success is True

    retrieved = await redis_adapter.get(key)
    assert retrieved == value
