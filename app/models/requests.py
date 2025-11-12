from typing import List

from pydantic import BaseModel, EmailStr


class SendEmailRequest(BaseModel):
    """Request model for sending emails"""

    recipient: EmailStr
    subject: str
    body: str
    body_type: str = "text"  # "text" or "html"


class FilterConversationsRequest(BaseModel):
    """Request model for filtering conversations"""

    conversations: List["Conversation"]


class FilterNudgingConversationsRequest(BaseModel):
    """Request model for filtering conversations that need nudging"""

    conversations: List["Conversation"]


from .conversation import Conversation  # noqa: E402  (circular import)

FilterConversationsRequest.model_rebuild()
FilterNudgingConversationsRequest.model_rebuild()


