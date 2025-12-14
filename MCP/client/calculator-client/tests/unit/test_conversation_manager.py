"""Unit tests for ConversationManager."""

from app.domain.models import Message, MessageRole
from app.services.conversation_manager import ConversationManager


def test_add_message(conversation_manager, sample_message):
    """Test adding a message to the conversation."""
    conversation_manager.add_message(sample_message)

    assert len(conversation_manager) == 1
    assert not conversation_manager.is_empty


def test_get_history(conversation_manager):
    """Test getting conversation history."""
    msg1 = Message(role=MessageRole.USER, content="Hello")
    msg2 = Message(role=MessageRole.ASSISTANT, content="Hi there")

    conversation_manager.add_message(msg1)
    conversation_manager.add_message(msg2)

    history = conversation_manager.get_history()
    assert len(history) == 2
    assert history[0].content == "Hello"
    assert history[1].content == "Hi there"


def test_get_history_with_limit(conversation_manager):
    """Test getting limited conversation history."""
    for i in range(5):
        msg = Message(role=MessageRole.USER, content=f"Message {i}")
        conversation_manager.add_message(msg)

    history = conversation_manager.get_history(limit=3)
    assert len(history) == 3
    assert history[0].content == "Message 2"
    assert history[-1].content == "Message 4"


def test_max_history_limit():
    """Test that conversation manager respects max history limit."""
    manager = ConversationManager(max_history=5)

    for i in range(10):
        msg = Message(role=MessageRole.USER, content=f"Message {i}")
        manager.add_message(msg)

    assert len(manager) == 5
    history = manager.get_history()
    assert history[0].content == "Message 5"
    assert history[-1].content == "Message 9"


def test_to_ollama_format(conversation_manager):
    """Test converting conversation to Ollama format."""
    msg1 = Message(role=MessageRole.USER, content="What is 2 + 2?")
    msg2 = Message(role=MessageRole.ASSISTANT, content="The result is 4.")

    conversation_manager.add_message(msg1)
    conversation_manager.add_message(msg2)

    ollama_messages = conversation_manager.to_ollama_format()

    assert len(ollama_messages) == 2
    assert ollama_messages[0]["role"] == "user"
    assert ollama_messages[0]["content"] == "What is 2 + 2?"
    assert ollama_messages[1]["role"] == "assistant"
    assert ollama_messages[1]["content"] == "The result is 4."


def test_clear(conversation_manager, sample_message):
    """Test clearing conversation history."""
    conversation_manager.add_message(sample_message)
    assert len(conversation_manager) == 1

    conversation_manager.clear()
    assert len(conversation_manager) == 0
    assert conversation_manager.is_empty


def test_empty_conversation():
    """Test empty conversation manager."""
    manager = ConversationManager()
    assert manager.is_empty
    assert len(manager) == 0
    assert manager.get_history() == []
