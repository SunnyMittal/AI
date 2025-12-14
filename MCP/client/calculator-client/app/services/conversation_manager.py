"""Conversation manager for handling chat history."""

import logging
from typing import Any

from app.domain.models import Message, MessageRole

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation history and format conversion."""

    def __init__(self, max_history: int = 50) -> None:
        """Initialize the conversation manager.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.max_history = max_history
        self._messages: list[Message] = []

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history.

        Args:
            message: Message to add
        """
        self._messages.append(message)

        if len(self._messages) > self.max_history:
            self._messages = self._messages[-self.max_history :]
            logger.debug(f"Trimmed conversation history to {self.max_history} messages")

    def get_history(self, limit: int | None = None) -> list[Message]:
        """Get conversation history.

        Args:
            limit: Maximum number of recent messages to return

        Returns:
            List of messages
        """
        if limit is None:
            return self._messages.copy()
        return self._messages[-limit:] if limit > 0 else []

    def to_ollama_format(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Convert conversation history to Ollama message format.

        Args:
            limit: Maximum number of recent messages to convert

        Returns:
            List of messages in Ollama format
        """
        messages = self.get_history(limit)
        ollama_messages = []

        for msg in messages:
            ollama_msg: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content,
            }

            if msg.tool_call_id:
                ollama_msg["tool_call_id"] = msg.tool_call_id

            if msg.tool_name:
                ollama_msg["name"] = msg.tool_name

            ollama_messages.append(ollama_msg)

        return ollama_messages

    def clear(self) -> None:
        """Clear the conversation history."""
        self._messages.clear()
        logger.info("Cleared conversation history")

    def __len__(self) -> int:
        """Get the number of messages in the conversation."""
        return len(self._messages)

    @property
    def is_empty(self) -> bool:
        """Check if conversation is empty."""
        return len(self._messages) == 0
