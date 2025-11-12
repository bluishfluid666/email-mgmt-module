from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .conversation import Conversation
from .email import EmailMessage


class UserResponse(BaseModel):
    """Response model for user information"""

    display_name: Optional[str] = None
    email: Optional[str] = None
    user_principal_name: Optional[str] = None


class InboxResponse(BaseModel):
    """Response model for inbox messages"""

    messages: List[EmailMessage]
    total_count: int
    has_more: bool = False


class SendEmailResponse(BaseModel):
    """Response model for send email operation"""

    success: bool
    message: str


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str
    app_name: str
    version: str
    timestamp: datetime


class TokenResponse(BaseModel):
    """Response model for token information"""

    has_valid_token: bool
    scopes: List[str]


class ConversationsResponse(BaseModel):
    """Response model for conversations"""

    conversations: List[Conversation]
    total_conversations: int
    total_messages: int

