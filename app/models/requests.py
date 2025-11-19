from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AttachmentRequest(BaseModel):
    """Request model for email attachment"""
    name: str
    content: str  # Base64 encoded file content
    content_type: str = Field(alias="contentType")  # MIME type (e.g., "application/pdf", "image/png")
    size: Optional[int] = None  # File size in bytes

    model_config = ConfigDict(populate_by_name=True)


class SendEmailRequest(BaseModel):
    """Request model for sending emails"""

    recipient: EmailStr
    subject: str
    body: str
    body_type: str = Field(default="text", alias="bodyType")  # "text" or "html"
    attachments: Optional[List[AttachmentRequest]] = None

    model_config = ConfigDict(populate_by_name=True)


class FilterConversationsRequest(BaseModel):
    """Request model for filtering conversations"""

    conversations: List["Conversation"]


class FilterNudgingConversationsRequest(BaseModel):
    """Request model for filtering conversations that need nudging"""

    conversations: List["Conversation"]


from .conversation import Conversation  # noqa: E402  (circular import)

FilterConversationsRequest.model_rebuild()
FilterNudgingConversationsRequest.model_rebuild()


