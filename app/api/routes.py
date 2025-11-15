from fastapi import APIRouter, HTTPException, Depends, status
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from typing import List, Optional
from app.models import (
    UserResponse, InboxResponse, SendEmailRequest, SendEmailResponse,
    HealthResponse, TokenResponse, ErrorResponse, EmailMessage, EmailAddress,
    Recipient, ItemBody, FollowupFlag, Attachment,
    ConversationsResponse, Conversation, FilterConversationsRequest,
    FilterNudgingConversationsRequest
)
from app.graph_service import GraphService
from app.config import settings
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Import the dependency function
from app.dependencies import get_graph_service


def _convert_graph_recipient(graph_recipient) -> Optional[Recipient]:
    if not graph_recipient or not getattr(graph_recipient, "email_address", None):
        return None

    email_address = graph_recipient.email_address
    return Recipient(
        email_address=EmailAddress(
            name=getattr(email_address, "name", None),
            address=getattr(email_address, "address", None)
        )
    )


def _convert_graph_recipient_list(graph_recipients) -> Optional[List[Recipient]]:
    if not graph_recipients:
        return None

    converted = [
        recipient for recipient in (
            _convert_graph_recipient(graph_recipient)
            for graph_recipient in graph_recipients
        )
        if recipient is not None
    ]

    return converted or None


def _convert_graph_item_body(body) -> Optional[ItemBody]:
    if body is None:
        return None

    return ItemBody(
        content_type=getattr(body, "content_type", None),
        content=getattr(body, "content", None)
    )


def _convert_graph_followup_flag(flag) -> Optional[FollowupFlag]:
    if flag is None:
        return None

    return FollowupFlag(
        status=getattr(flag, "flag_status", None) or getattr(flag, "status", None),
        completed_date_time=getattr(flag, "completed_date_time", None),
        due_date_time=getattr(flag, "due_date_time", None),
        start_date_time=getattr(flag, "start_date_time", None)
    )


def _convert_graph_attachments(attachments) -> Optional[List[Attachment]]:
    if not attachments:
        return None

    converted: List[Attachment] = []
    for attachment in attachments:
        additional_data = getattr(attachment, "additional_data", {}) or {}
        converted.append(
            Attachment(
                odata_type=getattr(attachment, "odata_type", None) or additional_data.get("@odata.type"),
                id=getattr(attachment, "id", None),
                name=getattr(attachment, "name", None),
                content_type=getattr(attachment, "content_type", None),
                size=getattr(attachment, "size", None),
                is_inline=getattr(attachment, "is_inline", None),
                last_modified_date_time=getattr(attachment, "last_modified_date_time", None)
            )
        )

    return converted or None


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
        email_messages: List[EmailMessage] = []
        for message in message_page.value:
            email_message = EmailMessage(
                message_id=getattr(message, "id", None),
                subject=getattr(message, "subject", None),
                body=_convert_graph_item_body(getattr(message, "body", None)),
                unique_body=_convert_graph_item_body(getattr(message, "unique_body", None)),
                from_=_convert_graph_recipient(getattr(message, "from_", None)),
                sender=_convert_graph_recipient(getattr(message, "sender", None)),
                to_recipients=_convert_graph_recipient_list(getattr(message, "to_recipients", None)),
                cc_recipients=_convert_graph_recipient_list(getattr(message, "cc_recipients", None)),
                bcc_recipients=_convert_graph_recipient_list(getattr(message, "bcc_recipients", None)),
                reply_to=_convert_graph_recipient_list(getattr(message, "reply_to", None)),
                is_read=bool(getattr(message, "is_read", False)),
                is_draft=getattr(message, "is_draft", None),
                is_delivery_receipt_requested=getattr(message, "is_delivery_receipt_requested", None),
                is_read_receipt_requested=getattr(message, "is_read_receipt_requested", None),
                has_attachments=getattr(message, "has_attachments", None),
                attachments=_convert_graph_attachments(getattr(message, "attachments", None)),
                conversation_id=getattr(message, "conversation_id", None),
                importance=getattr(message, "importance", None),
                created_date_time=getattr(message, "created_date_time", None),
                last_modified_date_time=getattr(message, "last_modified_date_time", None),
                received_date_time=getattr(message, "received_date_time", None),
                sent_date_time=getattr(message, "sent_date_time", None),
                flag=_convert_graph_followup_flag(getattr(message, "flag", None))
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


@router.post("/emails/draft")
async def create_empty_draft_email(
        graph_service: GraphService = Depends(get_graph_service)
):
    """Create an empty draft email and return its ID"""
    try:
        draft_id = await graph_service.create_empty_draft()

        return {
            "success": True,
            "message": "Empty draft created successfully",
            "draft_id": draft_id
        }

    except ODataError as e:
        logger.error(f"Graph API error creating draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph API error: {e.error.message if e.error else str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/emails/send/{draft_id}", response_model=SendEmailResponse)
async def send_draft_email(
        draft_id: str,
        email_request: SendEmailRequest,
        graph_service: GraphService = Depends(get_graph_service)
):
    """Update draft with content and send it"""
    try:
        # Update the draft with content
        await graph_service.update_draft(
            draft_id=draft_id,
            subject=email_request.subject,
            body=email_request.body,
            recipient=str(email_request.recipient),
            body_type=email_request.body_type
        )

        # Send the draft
        await graph_service.send_draft(draft_id)

        return SendEmailResponse(
            success=True,
            message=f"Email sent successfully to {email_request.recipient}"
        )

    except ODataError as e:
        logger.error(f"Graph API error sending draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph API error: {e.error.message if e.error else str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error sending draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/emails/send", response_model=SendEmailResponse)
async def send_email(
        email_request: SendEmailRequest,
        graph_service: GraphService = Depends(get_graph_service)
):
    """Send an email (convenience method that creates draft and sends immediately)"""
    try:
        # Create draft first
        draft_id = await graph_service.create_empty_draft(
            subject=email_request.subject,
            body=email_request.body,
            recipient=str(email_request.recipient),
            body_type=email_request.body_type
        )

        # Then send it
        await graph_service.send_draft(draft_id)

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


@router.get("/conversations/{folder}", response_model=ConversationsResponse)
async def get_conversations(
        folder: str,
        limit: int = 50,
        graph_service: GraphService = Depends(get_graph_service)
):
    """Get conversations grouped by conversation ID from specified folder (inbox or sent)"""
    try:
        # Validate folder name
        folder_lower = folder.lower()
        if folder_lower not in ['inbox', 'sent', 'sentitems']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder must be 'inbox' or 'sent'"
            )
        
        # Validate limit
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )

        # Get current user context for reply detection
        current_user = await graph_service.get_user()
        current_user_email = None
        if current_user:
            current_user_email = current_user.mail or current_user.user_principal_name

        # Get messages from specified folder
        message_page = await graph_service.get_messages_from_folder(folder_lower, top=limit)
        
        if not message_page or not message_page.value:
            return ConversationsResponse(
                conversations=[],
                total_conversations=0,
                total_messages=0
            )
        
        # Group messages by conversation ID
        conversations_dict = graph_service.group_messages_by_conversation_single_folder(message_page.value)

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

            # Sort messages chronologically to determine message types
            sorted_messages = sorted(
                messages,
                key=lambda msg: getattr(msg, "received_date_time", None)
                or getattr(msg, "sent_date_time", None)
                or ""
            )

            # Track conversation flow for message type determination
            first_user_message_found = False
            last_message_status = "unknown"

            for i, message in enumerate(sorted_messages):
                # Determine if message is from current user
                is_from_current_user = False
                if current_user_email and message.from_ and message.from_.email_address:
                    sender_email = message.from_.email_address.address
                    if sender_email and sender_email.lower() == current_user_email.lower():
                        is_from_current_user = True

                # Determine message type based on conversation flow
                message_type = "unknown"
                if is_from_current_user:
                    if not first_user_message_found:
                        message_type = "initial"
                        first_user_message_found = True
                    else:
                        # Check if this is a nudge message
                        is_nudge = False
                        if i > 0:  # There's a previous message
                            previous_message = sorted_messages[i - 1]
                            previous_is_from_user = False
                            if current_user_email and previous_message.from_ and previous_message.from_.email_address:
                                prev_sender_email = previous_message.from_.email_address.address
                                if prev_sender_email and prev_sender_email.lower() == current_user_email.lower():
                                    previous_is_from_user = True

                            # Check if previous message was initial or follow_up from current user
                            if previous_is_from_user:
                                # Check time elapsed between messages (3 days)
                                current_time = message.received_date_time or message.sent_date_time
                                previous_time = previous_message.received_date_time or previous_message.sent_date_time

                                if current_time and previous_time:
                                    # Normalize both datetimes for safe comparison
                                    normalized_current_time = _normalize_datetime(current_time)
                                    normalized_previous_time = _normalize_datetime(previous_time)

                                    if normalized_current_time and normalized_previous_time:
                                        time_diff = normalized_current_time - normalized_previous_time
                                        if time_diff >= timedelta(days=3):
                                            is_nudge = True

                        if is_nudge:
                            message_type = "nudge"
                        else:
                            message_type = "follow_up"
                else:
                    message_type = "reply"

                # Update last message status (this will be the final value after the loop)
                last_message_status = message_type

                conversation_message = EmailMessage(
                    message_id=getattr(message, "id", None),
                    subject=getattr(message, "subject", None),
                    body=_convert_graph_item_body(getattr(message, "body", None)),
                    unique_body=_convert_graph_item_body(getattr(message, "unique_body", None)),
                    from_=_convert_graph_recipient(getattr(message, "from_", None)),
                    sender=_convert_graph_recipient(getattr(message, "sender", None)),
                    to_recipients=_convert_graph_recipient_list(getattr(message, "to_recipients", None)),
                    cc_recipients=_convert_graph_recipient_list(getattr(message, "cc_recipients", None)),
                    bcc_recipients=_convert_graph_recipient_list(getattr(message, "bcc_recipients", None)),
                    reply_to=_convert_graph_recipient_list(getattr(message, "reply_to", None)),
                    is_read=bool(getattr(message, "is_read", False)),
                    is_draft=getattr(message, "is_draft", None),
                    is_delivery_receipt_requested=getattr(message, "is_delivery_receipt_requested", None),
                    is_read_receipt_requested=getattr(message, "is_read_receipt_requested", None),
                    has_attachments=getattr(message, "has_attachments", None),
                    attachments=_convert_graph_attachments(getattr(message, "attachments", None)),
                    conversation_id=conversation_id or getattr(message, "conversation_id", None),
                    importance=getattr(message, "importance", None),
                    created_date_time=getattr(message, "created_date_time", None),
                    last_modified_date_time=getattr(message, "last_modified_date_time", None),
                    received_date_time=getattr(message, "received_date_time", None),
                    sent_date_time=getattr(message, "sent_date_time", None),
                    flag=_convert_graph_followup_flag(getattr(message, "flag", None)),
                    message_type=message_type,
                    is_from_current_user=is_from_current_user
                )
                conversation_messages.append(conversation_message)

            conversation = Conversation(
                conversation_id=conversation_id,
                messages=conversation_messages,
                total_messages=len(conversation_messages),
                last_message_status=last_message_status
            )
            conversations.append(conversation)
            total_messages = len(conversation_messages)

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


def _normalize_datetime(dt: datetime) -> datetime:
    """
    Normalize datetime to timezone-aware UTC for safe comparison
    
    Args:
        dt: datetime object (may be naive or aware)
        
    Returns:
        timezone-aware datetime in UTC
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Aware datetime - convert to UTC
        return dt.astimezone(timezone.utc)


def filter_conversations_needing_immediate_followup(conversations: List[Conversation]) -> List[Conversation]:
    """
    Filter conversations that need immediate follow-up (last message status is 'reply')
    
    Args:
        conversations: List of conversation objects
        
    Returns:
        List of conversations where last_message_status is 'reply'
    """
    return [conv for conv in conversations if conv.last_message_status == "reply"]


@router.post("/conversations/filter", response_model=ConversationsResponse)
async def filter_conversations(
        filter_request: FilterConversationsRequest
):
    """Filter conversations needing immediate follow-up (last message status is 'reply')"""
    try:
        # Filter conversations that need follow-up
        filtered_conversations = filter_conversations_needing_immediate_followup(filter_request.conversations)

        # Calculate total messages in filtered conversations
        total_messages = sum(conv.total_messages for conv in filtered_conversations)

        return ConversationsResponse(
            conversations=filtered_conversations,
            total_conversations=len(filtered_conversations),
            total_messages=total_messages
        )

    except Exception as e:
        logger.error(f"Error filtering conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


def filter_conversations_needing_nudging(conversations: List[Conversation]) -> List[Conversation]:
    """
    Filter conversations that need nudging (last message is initial, follow_up, or nudge)
    and are within the last 3 months
    
    Args:
        conversations: List of conversation objects
        
    Returns:
        List of conversations where last_message_status is 'initial', 'follow_up', or 'nudge'
        and the last message is within the last 3 months
    """
    # Use timezone-aware datetime for comparison
    three_months_ago = datetime.now(timezone.utc) - timedelta(days=90)

    filtered_conversations = []
    for conv in conversations:
        # Check if last message status indicates user sent the last message
        if conv.last_message_status in ["initial", "follow_up", "nudge"]:
            # Check if the last message is within the last 3 months
            if conv.messages:
                last_message = conv.messages[-1]  # Messages are sorted chronologically
                last_message_time = last_message.received_date_time

                if last_message_time:
                    # Normalize both datetimes for safe comparison
                    normalized_last_message_time = _normalize_datetime(last_message_time)
                    normalized_three_months_ago = _normalize_datetime(three_months_ago)

                    if normalized_last_message_time and normalized_three_months_ago:
                        if normalized_last_message_time >= normalized_three_months_ago:
                            filtered_conversations.append(conv)

    return filtered_conversations


@router.post("/conversations/needing-nudging", response_model=ConversationsResponse)
async def filter_conversations_needing_nudging_endpoint(
        filter_request: FilterNudgingConversationsRequest
):
    """Filter conversations that need nudging (last message from user, within 3 months)"""
    try:
        # Filter conversations that need nudging
        filtered_conversations = filter_conversations_needing_nudging(filter_request.conversations)

        # Calculate total messages in filtered conversations
        total_messages = sum(conv.total_messages for conv in filtered_conversations)

        return ConversationsResponse(
            conversations=filtered_conversations,
            total_conversations=len(filtered_conversations),
            total_messages=total_messages
        )

    except Exception as e:
        logger.error(f"Error filtering conversations needing nudging: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
