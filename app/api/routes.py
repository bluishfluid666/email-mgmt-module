from fastapi import APIRouter, HTTPException, Depends, status
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from app.models import (
    UserResponse, InboxResponse, SendEmailRequest, SendEmailResponse,
    HealthResponse, TokenResponse, ErrorResponse, EmailMessage, EmailSender, EmailAddress,
    ConversationsResponse, Conversation, ConversationMessage
)
from app.graph_service import GraphService
from app.config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import the dependency function
from app.dependencies import get_graph_service

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now()
    )

@router.get("/user", response_model=UserResponse)
async def get_user(
    graph_service: GraphService = Depends(get_graph_service)
):
    """Get authenticated user information"""
    try:
        user = await graph_service.get_user()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            display_name=user.display_name,
            email=user.mail,
            user_principal_name=user.user_principal_name
        )
    except ODataError as e:
        logger.error(f"Graph API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph API error: {e.error.message if e.error else str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/emails/inbox", response_model=InboxResponse)
async def get_inbox(
    limit: int = 50,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Get inbox messages"""
    try:
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        message_page = await graph_service.get_inbox(top=limit)
        
        if not message_page or not message_page.value:
            return InboxResponse(
                messages=[],
                total_count=0,
                has_more=False
            )
        
        # Convert messages to our response model
        email_messages = []
        for message in message_page.value:
            email_sender = None
            if message.from_ and message.from_.email_address:
                email_sender = EmailSender(
                    email_address=EmailAddress(
                        name=message.from_.email_address.name,
                        address=message.from_.email_address.address
                    )
                )
            
            email_message = EmailMessage(
                subject=message.subject,
                body_content=message.body.content if message.body else None,
                from_sender=email_sender,
                is_read=message.is_read or False,
                received_date_time=message.received_date_time
            )
            email_messages.append(email_message)
        
        return InboxResponse(
            messages=email_messages,
            total_count=len(email_messages),
            has_more=message_page.odata_next_link is not None
        )
        
    except ODataError as e:
        logger.error(f"Graph API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph API error: {e.error.message if e.error else str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting inbox: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/emails/send", response_model=SendEmailResponse)
async def send_email(
    email_request: SendEmailRequest,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Send an email"""
    try:
        await graph_service.send_mail(
            subject=email_request.subject,
            body=email_request.body,
            recipient=str(email_request.recipient),
            body_type=email_request.body_type
        )
        
        return SendEmailResponse(
            success=True,
            message=f"Email sent successfully to {email_request.recipient}"
        )
        
    except ODataError as e:
        logger.error(f"Graph API error sending email: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph API error: {e.error.message if e.error else str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/auth/token", response_model=TokenResponse)
async def get_token_info(
    graph_service: GraphService = Depends(get_graph_service)
):
    """Get token information"""
    try:
        token = await graph_service.get_user_token()
        return TokenResponse(
            has_valid_token=token is not None,
            scopes=graph_service.graph_scopes
        )
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/conversations", response_model=ConversationsResponse)
async def get_conversations(
    inbox_limit: int = 50,
    sent_limit: int = 50,
    graph_service: GraphService = Depends(get_graph_service)
):
    """Get conversations grouped by conversation ID from sent folder"""
    try:
        # Validate limits
        if inbox_limit < 1 or inbox_limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inbox limit must be between 1 and 100"
            )
        if sent_limit < 1 or sent_limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sent limit must be between 1 and 100"
            )
        
        # Get conversations from graph service
        conversations_dict = await graph_service.get_conversations(
            inbox_top=inbox_limit, 
            sent_top=sent_limit
        )
        
        if not conversations_dict:
            return ConversationsResponse(
                conversations=[],
                total_conversations=0,
                total_messages=0
            )
        
        # Convert to response models
        conversations = []
        total_messages = 0
        
        for conversation_id, messages in conversations_dict.items():
            conversation_messages = []
            has_sent_messages = False
            has_received_messages = False
            
            for message in messages:
                # Determine message type (simplified heuristic)
                # In a real implementation, you'd track this during grouping
                message_type = "received"  # Default to received
                if hasattr(message, 'is_read') and message.is_read is None:
                    message_type = "sent"
                
                if message_type == "sent":
                    has_sent_messages = True
                else:
                    has_received_messages = True
                
                # Extract sender information
                email_sender = None
                if message.from_ and message.from_.email_address:
                    email_sender = EmailSender(
                        email_address=EmailAddress(
                            name=message.from_.email_address.name,
                            address=message.from_.email_address.address
                        )
                    )
                
                conversation_message = ConversationMessage(
                    subject=message.subject,
                    body_content=message.body.content if message.body else None,
                    from_sender=email_sender,
                    is_read=message.is_read or False,
                    received_date_time=message.received_date_time,
                    conversation_id=conversation_id,
                    message_type=message_type
                )
                conversation_messages.append(conversation_message)
            
            conversation = Conversation(
                conversation_id=conversation_id,
                messages=conversation_messages,
                total_messages=len(conversation_messages),
                has_sent_messages=has_sent_messages,
                has_received_messages=has_received_messages
            )
            conversations.append(conversation)
            total_messages += len(conversation_messages)
        
        return ConversationsResponse(
            conversations=conversations,
            total_conversations=len(conversations),
            total_messages=total_messages
        )
        
    except ODataError as e:
        logger.error(f"Graph API error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph API error: {e.error.message if e.error else str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
