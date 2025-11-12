from typing import List

from pydantic import BaseModel

from .email import EmailMessage


class Conversation(BaseModel):
    """Conversation model"""

    conversation_id: str
    messages: List[EmailMessage]
    total_messages: int
    last_message_status: str  # "initial", "reply", or "follow_up"

