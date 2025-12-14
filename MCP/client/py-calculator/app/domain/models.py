"""Domain models for the calculator client."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MessageRole(str, Enum):
    """Message roles in the conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(BaseModel):
    """Represents a message in the conversation."""

    model_config = ConfigDict(frozen=True)

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    tool_call_id: str | None = None
    tool_name: str | None = None


class ToolCall(BaseModel):
    """Represents an LLM's decision to call a tool."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """Result from executing an MCP tool."""

    model_config = ConfigDict(frozen=True)

    tool_call_id: str
    tool_name: str
    success: bool
    result: Any
    error: str | None = None


class ConversationContext(BaseModel):
    """Container for conversation history and state."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    messages: list[Message] = Field(default_factory=list)
    max_history: int = 50

    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

    def get_recent_messages(self, limit: int | None = None) -> list[Message]:
        """Get recent messages from the conversation."""
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit > 0 else []

    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()
