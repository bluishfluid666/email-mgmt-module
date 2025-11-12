from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


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

