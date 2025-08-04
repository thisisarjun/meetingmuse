"""
Tests for LangGraph Factory
Unit tests for the LangGraph factory and graph creation
"""
import os
import sys
from unittest.mock import Mock, patch

import pytest

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from server.langgraph.langgraph_factory import LangGraphSingletonFactory  # noqa: E402


class TestLangGraphSingletonFactory:
    """Test suite for LangGraph Factory"""

    def test_factory_initialization(self):
        """Test that the factory initializes correctly"""
        factory = LangGraphSingletonFactory.get_instance()

        assert not factory.is_initialized()
        assert factory._graph_instance is None
        assert factory._model_name == "meta-llama/Meta-Llama-3-8B-Instruct"

    @patch("meetingmuse_server.langgraph.langgraph_factory.HuggingFaceModel")
    @patch("meetingmuse_server.langgraph.langgraph_factory.GraphBuilder")
    def test_create_conversation_graph(self, mock_graph_builder, mock_hugging_face):
        """Test that get_graph creates a graph successfully through the private method"""
        # Reset singleton to ensure clean test
        factory = LangGraphSingletonFactory()
        factory.reset()

        # Mock the dependencies
        mock_model = Mock()
        mock_hugging_face.return_value = mock_model

        mock_graph = Mock()
        mock_builder_instance = Mock()
        mock_builder_instance.build.return_value = mock_graph
        mock_graph_builder.return_value = mock_builder_instance

        # Get graph through public interface
        result = LangGraphSingletonFactory.get_graph()

        # Verify the graph was created
        assert result == mock_graph
        mock_hugging_face.assert_called_once_with("meta-llama/Meta-Llama-3-8B-Instruct")
        mock_builder_instance.build.assert_called_once()

    def test_static_graph_creation(self):
        """Test static graph creation method through public interface"""
        # Reset singleton to ensure clean test
        factory = LangGraphSingletonFactory()
        factory.reset()

        result = LangGraphSingletonFactory.get_graph()

        # Should return a compiled graph
        assert result is not None
        # Could add more specific assertions about the graph structure

    @patch(
        "meetingmuse_server.langgraph.langgraph_factory.LangGraphSingletonFactory._create_conversation_graph"
    )
    def test_get_graph_instance_caching(self, mock_create):
        """Test that get_graph_instance returns a singleton"""
        mock_graph = Mock()
        mock_create.return_value = mock_graph

        factory = LangGraphSingletonFactory.get_instance()

        # Reset any previous state
        factory.reset()

        # First call should create the graph
        graph1 = factory.get_graph_instance()
        assert graph1 == mock_graph
        assert factory.is_initialized()

        # Second call should return the same instance
        graph2 = factory.get_graph_instance()
        assert graph2 == mock_graph
        assert graph1 is graph2

        # create_conversation_graph should only be called once
        mock_create.assert_called_once()

    def test_reset(self):
        """Test that reset clears the factory state"""
        factory = LangGraphSingletonFactory.get_instance()
        factory._graph_instance = Mock()
        factory._initialized = True

        factory.reset()

        assert factory._graph_instance is None
        assert not factory.is_initialized()

    @patch("meetingmuse_server.langgraph.langgraph_factory.HuggingFaceModel")
    def test_create_conversation_graph_error_handling(self, mock_hugging_face):
        """Test error handling in create_conversation_graph"""
        # Mock an exception during model creation
        mock_hugging_face.side_effect = Exception("Model initialization failed")

        with pytest.raises(Exception) as exc_info:
            LangGraphSingletonFactory._create_conversation_graph()

        assert "Model initialization failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
