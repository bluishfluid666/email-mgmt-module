from pydantic import BaseModel, EmailStr, Field
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

class FilterNudgingConversationsRequest(BaseModel):
    """Request model for filtering conversations that need nudging"""
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


class Recipient(BaseModel):
    """Microsoft Graph recipient model"""
    email_address: Optional[EmailAddress] = Field(default=None, alias="emailAddress")

    class Config:
        allow_population_by_field_name = True


class ItemBody(BaseModel):
    """Microsoft Graph item body model"""
    content_type: Optional[str] = Field(default=None, alias="contentType")
    content: Optional[str] = None

    class Config:
        allow_population_by_field_name = True


class FollowupFlag(BaseModel):
    """Microsoft Graph follow-up flag model"""
    status: Optional[str] = None
    completed_date_time: Optional[datetime] = Field(default=None, alias="completedDateTime")
    due_date_time: Optional[datetime] = Field(default=None, alias="dueDateTime")
    start_date_time: Optional[datetime] = Field(default=None, alias="startDateTime")

    class Config:
        allow_population_by_field_name = True


class Attachment(BaseModel):
    """Microsoft Graph attachment model"""
    odata_type: Optional[str] = Field(default=None, alias="@odata.type")
    id: Optional[str] = None
    name: Optional[str] = None
    content_type: Optional[str] = Field(default=None, alias="contentType")
    size: Optional[int] = None
    is_inline: Optional[bool] = Field(default=None, alias="isInline")
    last_modified_date_time: Optional[datetime] = Field(default=None, alias="lastModifiedDateTime")

    class Config:
        allow_population_by_field_name = True

class EmailMessage(BaseModel):
    """Unified message model for emails and conversations"""
    message_id: Optional[str] = Field(default=None, alias="id")
    bcc_recipients: Optional[List[Recipient]] = Field(default=None, alias="bccRecipients")
    body: Optional[ItemBody] = None
    cc_recipients: Optional[List[Recipient]] = Field(default=None, alias="ccRecipients")
    conversation_id: Optional[str] = Field(default=None, alias="conversationId")
    created_date_time: Optional[datetime] = Field(default=None, alias="createdDateTime")
    flag: Optional[FollowupFlag] = None
    from_: Optional[Recipient] = Field(default=None, alias="from")
    has_attachments: Optional[bool] = Field(default=None, alias="hasAttachments")
    importance: Optional[str] = None
    is_delivery_receipt_requested: Optional[bool] = Field(default=None, alias="isDeliveryReceiptRequested")
    is_draft: Optional[bool] = Field(default=None, alias="isDraft")
    is_read: bool = Field(default=False, alias="isRead")
    is_read_receipt_requested: Optional[bool] = Field(default=None, alias="isReadReceiptRequested")
    last_modified_date_time: Optional[datetime] = Field(default=None, alias="lastModifiedDateTime")
    received_date_time: Optional[datetime] = Field(default=None, alias="receivedDateTime")
    reply_to: Optional[List[Recipient]] = Field(default=None, alias="replyTo")
    sender: Optional[Recipient] = None
    sent_date_time: Optional[datetime] = Field(default=None, alias="sentDateTime")
    subject: Optional[str] = None
    to_recipients: Optional[List[Recipient]] = Field(default=None, alias="toRecipients")
    unique_body: Optional[ItemBody] = Field(default=None, alias="uniqueBody")
    attachments: Optional[List[Attachment]] = None
    message_type: str = "unknown"  # "initial", "reply", "follow_up", or "nudge"
    is_from_current_user: bool = False

    class Config:
        allow_population_by_field_name = True

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

class Conversation(BaseModel):
    """Conversation model"""
    conversation_id: str
    messages: List[EmailMessage]
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
