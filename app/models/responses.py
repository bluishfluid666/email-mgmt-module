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


# Tracking Models
class BrowserInfo(BaseModel):
    """Browser information model"""
    name: Optional[str] = None
    version: Optional[str] = None


class DeviceInfo(BaseModel):
    """Device information model"""
    type: Optional[str] = None
    name: Optional[str] = None


class OSInfo(BaseModel):
    """Operating system information model"""
    name: Optional[str] = None
    version: Optional[str] = None


class LocationInfo(BaseModel):
    """Location information model"""
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    isp: Optional[str] = None
    district: Optional[str] = None


class EmailView(BaseModel):
    """Email view tracking data model"""
    timestamp: Optional[datetime] = None
    ip: Optional[str] = None
    userAgent: Optional[str] = None
    referrer: Optional[str] = None
    browser: Optional[BrowserInfo] = None
    device: Optional[DeviceInfo] = None
    os: Optional[OSInfo] = None
    location: Optional[LocationInfo] = None


class EmailTrackingResponse(BaseModel):
    """Response model for email tracking data"""
    uuid: str
    createdAt: Optional[datetime] = None
    views: List[EmailView] = []
    total_views: int = 0


class UploadProgressResponse(BaseModel):
    """Response model for upload progress"""
    upload_id: str
    filename: str
    status: str
    bytes_read: int
    total_size: int
    progress_percent: float
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

