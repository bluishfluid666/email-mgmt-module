from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Request Models
class SendEmailRequest(BaseModel):
    """Request model for sending emails"""
    recipient: EmailStr
    subject: str
    body: str
    body_type: str = "text"  # "text" or "html"

class FilterConversationsRequest(BaseModel):
    """Request model for filtering conversations"""
    conversations: List['Conversation']

# Response Models
class UserResponse(BaseModel):
    """Response model for user information"""
    display_name: Optional[str] = None
    email: Optional[str] = None
    user_principal_name: Optional[str] = None

class EmailAddress(BaseModel):
    """Email address model"""
    name: Optional[str] = None
    address: Optional[str] = None

class EmailSender(BaseModel):
    """Email sender model"""
    email_address: Optional[EmailAddress] = None

class EmailMessage(BaseModel):
    """Email message model"""
    subject: Optional[str] = None
    body_content: Optional[str] = None
    from_sender: Optional[EmailSender] = None
    is_read: bool = False
    received_date_time: Optional[datetime] = None

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

class ConversationMessage(BaseModel):
    """Message within a conversation"""
    subject: Optional[str] = None
    body_content: Optional[str] = None
    from_sender: Optional[EmailSender] = None
    is_read: bool = False
    received_date_time: Optional[datetime] = None
    conversation_id: Optional[str] = None
    message_type: str = "unknown"  # "initial", "reply", or "follow_up"
    is_from_current_user: bool = False

class Conversation(BaseModel):
    """Conversation model"""
    conversation_id: str
    messages: List[ConversationMessage]
    total_messages: int
    last_message_status: str  # "initial", "reply", or "follow_up"

class ConversationsResponse(BaseModel):
    """Response model for conversations"""
    conversations: List[Conversation]
    total_conversations: int
    total_messages: int

# Error Models
class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    status_code: int
