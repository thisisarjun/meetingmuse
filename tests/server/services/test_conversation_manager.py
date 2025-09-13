"""
Test suite for ConversationManager service.
"""


from server.models.conversation import ActiveConversation, ConversationStatus


class TestConversationManager:
    """Test suite for ConversationManager."""

    def test_initialize_conversation_new_client(self, conversation_manager):
        """Test initializing conversation for a new client."""
        client_id = "test_client_123"

        conversation_manager.initialize_conversation(client_id)

        assert client_id in conversation_manager.active_conversations
        conversation = conversation_manager.active_conversations[client_id]
        assert isinstance(conversation, ActiveConversation)
        assert conversation.message_count == 0
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.session_id is None
        assert conversation.authenticated is False

    def test_initialize_conversation_with_session_id(self, conversation_manager):
        """Test initializing conversation with session ID."""
        client_id = "test_client_123"
        session_id = "session_456"

        conversation_manager.initialize_conversation(client_id, session_id)

        conversation = conversation_manager.active_conversations[client_id]
        assert conversation.session_id == session_id
        assert conversation.authenticated is True

    async def test_handle_reconnection_with_existing_conversation(
        self, conversation_manager, mock_message_processor
    ):
        """Test handling reconnection with existing conversation."""
        client_id = "test_client_123"

        # Initialize conversation first
        conversation_manager.initialize_conversation(client_id)
        original_activity = conversation_manager.active_conversations[
            client_id
        ].last_activity

        # Mock message processor to return True (conversation exists)
        mock_message_processor.get_conversation_state.return_value = True

        result = await conversation_manager.handle_reconnection(client_id)

        assert result is True
        mock_message_processor.get_conversation_state.assert_called_once_with(client_id)

        # Check that conversation was updated
        conversation = conversation_manager.active_conversations[client_id]
        assert conversation.status == ConversationStatus.RESUMED
        assert conversation.last_activity != original_activity

    async def test_handle_reconnection_no_existing_conversation(
        self, conversation_manager, mock_message_processor
    ):
        """Test handling reconnection with no existing conversation."""
        client_id = "test_client_123"

        # Mock message processor to return False (no conversation)
        mock_message_processor.get_conversation_state.return_value = False

        result = await conversation_manager.handle_reconnection(client_id)

        assert result is False
        mock_message_processor.get_conversation_state.assert_called_once_with(client_id)

    async def test_handle_reconnection_exception(
        self, conversation_manager, mock_message_processor, mock_logger
    ):
        """Test handling exception during reconnection."""
        client_id = "test_client_123"

        # Mock message processor to raise exception
        mock_message_processor.get_conversation_state.side_effect = Exception(
            "Processor error"
        )

        result = await conversation_manager.handle_reconnection(client_id)

        assert result is False
        mock_logger.error.assert_called_once()

    def test_update_conversation_activity_existing_client(self, conversation_manager):
        """Test updating conversation activity for existing client."""
        client_id = "test_client_123"

        # Initialize conversation first
        conversation_manager.initialize_conversation(client_id)
        original_activity = conversation_manager.active_conversations[
            client_id
        ].last_activity
        original_count = conversation_manager.active_conversations[
            client_id
        ].message_count

        conversation_manager.update_conversation_activity(client_id)

        conversation = conversation_manager.active_conversations[client_id]
        assert conversation.last_activity != original_activity
        assert conversation.message_count == original_count + 1

    def test_update_conversation_activity_nonexistent_client(
        self, conversation_manager
    ):
        """Test updating conversation activity for non-existent client."""
        client_id = "nonexistent_client"

        # Should not raise exception
        conversation_manager.update_conversation_activity(client_id)

        assert client_id not in conversation_manager.active_conversations

    async def test_end_conversation_existing_client(self, conversation_manager):
        """Test ending conversation for existing client."""
        client_id = "test_client_123"

        # Initialize conversation first
        conversation_manager.initialize_conversation(client_id)

        await conversation_manager.end_conversation(client_id)

        conversation = conversation_manager.active_conversations[client_id]
        assert conversation.status == ConversationStatus.ENDED
        assert conversation.ended_at is not None

    async def test_end_conversation_nonexistent_client(self, conversation_manager):
        """Test ending conversation for non-existent client."""
        client_id = "nonexistent_client"

        # Should not raise exception
        await conversation_manager.end_conversation(client_id)

        assert client_id not in conversation_manager.active_conversations

    def test_get_session_id_existing_client(self, conversation_manager):
        """Test getting session ID for existing client."""
        client_id = "test_client_123"
        session_id = "session_456"

        # Initialize conversation with session ID
        conversation_manager.initialize_conversation(client_id, session_id)

        result = conversation_manager.get_session_id(client_id)

        assert result == session_id

    def test_get_session_id_existing_client_no_session(self, conversation_manager):
        """Test getting session ID for existing client without session."""
        client_id = "test_client_123"

        # Initialize conversation without session ID
        conversation_manager.initialize_conversation(client_id)

        result = conversation_manager.get_session_id(client_id)

        assert result is None

    def test_get_session_id_nonexistent_client(self, conversation_manager):
        """Test getting session ID for non-existent client."""
        client_id = "nonexistent_client"

        result = conversation_manager.get_session_id(client_id)

        assert result is None
