import asyncio
import base64
import logging
import httpx
from typing import Optional, List, Dict, Callable

from azure.identity import ClientSecretCredential
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph import GraphServiceClient
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.file_attachment import FileAttachment
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.message import Message
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder)
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder

logger = logging.getLogger(__name__)


class GraphService:
    """Enhanced Graph service for API usage"""

    def __init__(self, client_id: str, tenant_id: str, client_secret: str):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.client_secret = client_secret

        self.client_credential = ClientSecretCredential(tenant_id, client_id, client_secret)

        self.user_client = GraphServiceClient(
            self.client_credential,
        )

    async def get_user_token(self) -> Optional[str]:
        """Get user access token"""
        try:
            access_token = self.device_code_credential.get_token(' '.join(self.graph_scopes))
            return access_token.token
        except Exception as e:
            logger.error(f"Error getting user token: {e}")
            return None

    async def get_user(self):
        """Get current user information"""
        try:
            query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
                select=['displayName', 'mail', 'userPrincipalName']
            )

            request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )

            user = await self.user_client.users.by_user_id('sales@powertrans.vn').get(request_configuration=request_config)
            return user
        except ODataError as e:
            logger.error(f"OData error getting user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise

    async def get_inbox(self, top: int = 50):
        """Get inbox messages"""
        try:
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['from', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId', 'internetMessageId'],
                top=top,
                orderby=['receivedDateTime DESC']
            )
            request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )

            messages = await self.user_client.users.by_user_id('sales@powertrans.vn').mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config)
            return messages
        except ODataError as e:
            logger.error(f"OData error getting inbox: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting inbox: {e}")
            raise

    async def get_sent(self, top: int = 50):
        """Get sent messages"""
        try:
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['from', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId', 'internetMessageId', 'id'],
                top=top,
                orderby=['sentDateTime DESC']
            )
            request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            # Use ImmutableId preference when retrieving
            request_config.headers = RequestConfiguration().headers
            request_config.headers.add("Prefer", "IdType=\"ImmutableId\"")

            messages = await self.user_client.users.by_user_id('sales@powertrans.vn').mail_folders.by_mail_folder_id('sentitems').messages.get(
                request_configuration=request_config)
            return messages
        except ODataError as e:
            logger.error(f"OData error getting sent messages: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting sent messages: {e}")
            raise

    async def get_messages_from_folder(self, folder_name: str, top: int = 50):
        """
        Get messages from a specific folder by folder name
        
        Args:
            folder_name: Name of the folder ('inbox' or 'sent')
            top: Maximum number of messages to fetch
            
        Returns:
            Messages response from Microsoft Graph
        """
        try:
            # Map folder names to folder IDs
            folder_id_map = {
                'inbox': 'inbox',
                'sent': 'sentitems',
                'sentitems': 'sentitems'
            }
            
            folder_id = folder_id_map.get(folder_name.lower(), folder_name.lower())
            
            query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
                select=['from', 'isRead', 'receivedDateTime', 'subject', 'body', 'conversationId', 'internetMessageId', 
                        'id', 'uniqueBody', 'sender', 'toRecipients', 'ccRecipients', 'bccRecipients', 'replyTo',
                        'isDraft', 'isDeliveryReceiptRequested', 'isReadReceiptRequested', 'hasAttachments',
                        'attachments', 'importance', 'createdDateTime', 'lastModifiedDateTime', 'sentDateTime', 'flag'],
                top=top,
                orderby=['sentDateTime DESC' if folder_id == 'sentitems' else 'receivedDateTime DESC']
            )
            request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )
            # Use ImmutableId preference when retrieving
            request_config.headers = RequestConfiguration().headers
            request_config.headers.add("Prefer", "IdType=\"ImmutableId\"")

            messages = await self.user_client.users.by_user_id('sales@powertrans.vn').mail_folders.by_mail_folder_id(folder_id).messages.get(
                request_configuration=request_config)
            return messages
        except ODataError as e:
            logger.error(f"OData error getting messages from folder {folder_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting messages from folder {folder_name}: {e}")
            raise

    async def create_empty_draft(self) -> str:
        """
        Create an empty draft email message

        Returns:
        Draft message ID (immutable)
        """


        try:
            message = Message()
            message.subject = ""

            message.body = ItemBody()
            message.body.content_type = BodyType.Text
            message.body.content = ""

            # Create draft with ImmutableId preference

            request_config = RequestConfiguration()
            request_config.headers.add("Prefer", "IdType=\"ImmutableId\"")

            draft = await self.user_client.users.by_user_id('sales@powertrans.vn').messages.post(body=message, request_configuration=request_config)

            logger.info(f"Empty draft created with ID: {draft.id}")

            return draft.id

        except ODataError as e:
            logger.error(f"OData error creating empty draft: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating empty draft: {e}")
            raise

    async def update_draft(self, draft_id: str, subject: str, body: str, recipient: str, body_type: str = "text") -> bool:
        """
        Update an existing draft email message with content

        Args:
            draft_id: The immutable ID of the draft message
            subject: Email subject
            body: Email body content
            recipient: Recipient email address
            body_type: Content type ("text" or "html")

        Returns:
            True if successful
        """
        try:
            message = Message()
            message.subject = subject

            message.body = ItemBody()
            message.body.content_type = BodyType.Html if body_type.lower() == "html" else BodyType.Text
            message.body.content = body

            to_recipient = Recipient()
            to_recipient.email_address = EmailAddress()
            to_recipient.email_address.address = recipient
            message.to_recipients = [to_recipient]

            # Update draft with ImmutableId preference
            request_config = RequestConfiguration()
            request_config.headers.add("Prefer", "IdType=\"ImmutableId\"")

            await self.user_client.users.by_user_id('sales@powertrans.vn').messages.by_message_id(draft_id).patch(body=message, request_configuration=request_config)

            logger.info(f"Draft {draft_id} updated successfully")
            return True
        except ODataError as e:
            logger.error(f"OData error updating draft: {e}")
            raise
        except Exception as e:
            logger.error(f"Error updating draft: {e}")

        raise

    async def create_upload_session(
        self,
        draft_id: str,
        filename: str,
        file_size: int,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Create an upload session for a large file attachment

        Args:
            draft_id: The immutable ID of the draft message
            filename: Name of the file
            file_size: Size of the file in bytes
            content_type: MIME type of the file

        Returns:
            Upload URL for chunked uploads
        """
        try:
            # Get access token
            token = self.client_credential.get_token("https://graph.microsoft.com/.default").token
            
            # Create upload session request body
            request_body = {
                "AttachmentItem": {
                    "attachmentType": "file",
                    "name": filename,
                    "size": file_size,
                    "contentType": content_type
                }
            }
            
            # Make direct HTTP request to create upload session
            url = f"https://graph.microsoft.com/v1.0/users/sales@powertrans.vn/messages/{draft_id}/attachments/createUploadSession"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=request_body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Prefer": "IdType=\"ImmutableId\""
                    },
                    timeout=30.0
                )
                
                # Accept both 200 OK and 201 Created as success
                if response.status_code not in [200, 201]:
                    error_msg = f"Failed to create upload session: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                result = response.json()
                upload_url = result.get("uploadUrl")
                
                if not upload_url:
                    raise Exception("Failed to create upload session: no upload URL in response")
                
                logger.info(f"Created upload session for {filename} ({file_size} bytes)")
                return upload_url

        except Exception as e:
            logger.error(f"Error creating upload session: {e}")
            raise

    async def upload_chunk(
        self,
        upload_url: str,
        chunk_data: bytes,
        range_start: int,
        range_end: int,
        total_size: int
    ) -> bool:
        """
        Upload a chunk of data to the upload session

        Args:
            upload_url: The upload URL from the upload session (includes authtoken)
            chunk_data: The chunk of data to upload
            range_start: Start byte position (0-based)
            range_end: End byte position (inclusive)
            total_size: Total size of the file

        Returns:
            True if successful
        """
        try:
            # Content-Range header format: bytes start-end/total
            content_range = f"bytes {range_start}-{range_end}/{total_size}"

            # Note: The upload_url already contains an authtoken query parameter
            # We should NOT send an Authorization header - the authtoken in the URL is sufficient
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    upload_url,
                    content=chunk_data,
                    headers={
                        "Content-Length": str(len(chunk_data)),
                        "Content-Range": content_range
                    },
                    timeout=60.0
                )

                if response.status_code not in [200, 201, 202]:
                    error_msg = f"Upload chunk failed: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)

                # When uploading the final chunk, Microsoft Graph returns 201 Created
                # with the attachment information, confirming the attachment was created
                is_final_chunk = range_end >= total_size - 1
                if is_final_chunk and response.status_code == 201:
                    logger.info(f"Final chunk uploaded successfully. Attachment committed to message.")
                    # Optionally parse response to verify attachment was created
                    try:
                        result = response.json()
                        if result.get("id"):
                            logger.info(f"Attachment ID: {result.get('id')}")
                    except:
                        pass  # Response might not be JSON

                logger.debug(f"Uploaded chunk {range_start}-{range_end}/{total_size}")
                return True

        except Exception as e:
            logger.error(f"Error uploading chunk: {e}")
            raise

    async def upload_large_file_to_draft(
        self,
        draft_id: str,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
        chunk_size: int = 3 * 1024 * 1024,  # 3MB chunks (safe for Vercel)
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Upload a large file to a draft using upload session API with chunked uploads

        Args:
            draft_id: The immutable ID of the draft message
            file_content: The file content as bytes
            filename: Name of the file
            content_type: MIME type of the file
            chunk_size: Size of each chunk in bytes (default 3MB)
            progress_callback: Optional callback function(bytes_uploaded, total_size)

        Returns:
            True if successful
        """
        try:
            file_size = len(file_content)

            # Create upload session
            upload_url = await self.create_upload_session(
                draft_id=draft_id,
                filename=filename,
                file_size=file_size,
                content_type=content_type
            )

            # Upload file in chunks
            bytes_uploaded = 0
            chunk_number = 0
            total_chunks = (file_size + chunk_size - 1) // chunk_size  # Ceiling division

            while bytes_uploaded < file_size:
                # Calculate chunk boundaries
                range_start = bytes_uploaded
                range_end = min(bytes_uploaded + chunk_size - 1, file_size - 1)
                chunk_data = file_content[range_start:range_end + 1]

                # Upload chunk
                await self.upload_chunk(
                    upload_url=upload_url,
                    chunk_data=chunk_data,
                    range_start=range_start,
                    range_end=range_end,
                    total_size=file_size
                )

                bytes_uploaded = range_end + 1
                chunk_number += 1

                # Call progress callback if provided (update after each chunk)
                if progress_callback:
                    progress_callback(bytes_uploaded, file_size)

                logger.info(f"Uploaded chunk {chunk_number}/{total_chunks}: {bytes_uploaded}/{file_size} bytes ({bytes_uploaded * 100 // file_size}%)")

            logger.info(f"Successfully uploaded large file {filename} ({file_size} bytes) in {chunk_number} chunks")
            return True

        except Exception as e:
            logger.error(f"Error uploading large file: {e}")
            raise

    async def add_attachments_to_draft(self, draft_id: str, attachments: List[Dict[str, str]]) -> bool:
        """
        Add attachments to an existing draft email message

        Args:
            draft_id: The immutable ID of the draft message
            attachments: List of attachment dictionaries with 'name', 'content' (base64), and 'content_type'

        Returns:
            True if successful
        """
        try:
            for attachment in attachments:
                file_attachment = FileAttachment()
                file_attachment.name = attachment.get("name")
                file_attachment.content_type = attachment.get("content_type")
                
                # Decode base64 content
                content_bytes = base64.b64decode(attachment.get("content"))
                file_attachment.content_bytes = content_bytes
                # Use provided size if available, otherwise calculate from decoded content
                file_attachment.size = attachment.get("size") or len(content_bytes)
                file_attachment.is_inline = False

                # Add attachment with ImmutableId preference
                request_config = RequestConfiguration()
                request_config.headers.add("Prefer", "IdType=\"ImmutableId\"")

                await self.user_client.users.by_user_id('sales@powertrans.vn').messages.by_message_id(draft_id).attachments.post(
                    body=file_attachment,
                    request_configuration=request_config
                )

            logger.info(f"Added {len(attachments)} attachment(s) to draft {draft_id}")
            return True
        except ODataError as e:
            logger.error(f"OData error adding attachments to draft: {e}")
            raise
        except Exception as e:
            logger.error(f"Error adding attachments to draft: {e}")
            raise

    async def send_draft(self, draft_id: str) -> Optional[str]:
        """
        Send a draft email by its ID

        Args:
        draft_id: The immutable ID of the draft message

        Returns:
        The immutable ID of the sent message (same as draft_id if using ImmutableId)
        """

        try:
            # Send with ImmutableId preference
            request_config = RequestConfiguration()
            request_config.headers.add("Prefer", "IdType=\"ImmutableId\"")

            await self.user_client.users.by_user_id('sales@powertrans.vn').messages.by_message_id(draft_id).send.post(request_configuration=request_config)

            logger.info(f"Draft {draft_id} sent successfully")
            # The sent message should have the same ImmutableId as the draft
            return draft_id

        except ODataError as e:
            logger.error(f"OData error sending draft: {e}")

            raise
        except Exception as e:
            logger.error(f"Error sending draft: {e}")
            raise


    async def get_all_messages(self, inbox_top: int = 50, sent_top: int = 50):
        """Get messages from both inbox and sent folders"""
        try:
            # Fetch messages from both folders concurrently
            inbox_task = self.get_inbox(inbox_top)
            sent_task = self.get_sent(sent_top)

            inbox_messages, sent_messages = await asyncio.gather(inbox_task, sent_task)

            all_messages = []
            if inbox_messages and inbox_messages.value:
                all_messages.extend(inbox_messages.value)
            if sent_messages and sent_messages.value:
                all_messages.extend(sent_messages.value)

            return all_messages
        except Exception as e:
            logger.error(f"Error getting all messages: {e}")
            raise


    def group_messages_by_conversation(self, inbox_messages: List, sent_messages: List) -> Dict[str, List]:
        """
        Group messages by conversation ID based on sent folder conversation IDs

        Args:
            inbox_messages: List of inbox message objects from Microsoft Graph
            sent_messages: List of sent message objects from Microsoft Graph

        Returns:
            Dictionary where keys are conversation IDs from sent messages and values are lists of all related messages
        """
        # First, collect all conversation IDs from sent messages
        sent_conversation_ids = set()
        for message in sent_messages:
            conversation_id = self._get_conversation_id(message)
            sent_conversation_ids.add(conversation_id)

        # Now find all messages (both inbox and sent) that match these conversation IDs
        conversations = {}

        for conversation_id in sent_conversation_ids:
            conversation_messages = []

            # Add all sent messages with this conversation ID
            for message in sent_messages:
                if self._get_conversation_id(message) == conversation_id:
                    conversation_messages.append(message)

            # Add all inbox messages with this conversation ID
            for message in inbox_messages:
                if self._get_conversation_id(message) == conversation_id:
                    conversation_messages.append(message)

            # Only include conversations that have at least one sent message
            if conversation_messages:
                # Sort messages within each conversation by received/sent date
                conversation_messages.sort(
                    key=lambda msg: getattr(msg, 'received_date_time', None) or getattr(msg, 'sent_date_time', None) or '',
                    reverse=False  # Oldest first for conversation flow
                )

                conversations[conversation_id] = conversation_messages

        return conversations

    def group_messages_by_conversation_single_folder(self, messages: List) -> Dict[str, List]:
        """
        Group messages from a single folder by conversation ID

        Args:
            messages: List of message objects from Microsoft Graph

        Returns:
            Dictionary where keys are conversation IDs and values are lists of messages in that conversation
        """
        conversations = {}
        
        for message in messages:
            conversation_id = self._get_conversation_id(message)
            if conversation_id:
                if conversation_id not in conversations:
                    conversations[conversation_id] = []
                conversations[conversation_id].append(message)
        
        # Sort messages within each conversation by received/sent date
        for conversation_id in conversations:
            conversations[conversation_id].sort(
                key=lambda msg: getattr(msg, 'received_date_time', None) or getattr(msg, 'sent_date_time', None) or '',
                reverse=False  # Oldest first for conversation flow
            )
        
        return conversations

    def _get_conversation_id(self, message) -> str:
        """
        Extract conversation ID from a message, with fallbacks

        Args:
            message: Message object from Microsoft Graph

        Returns:
            Conversation ID string
        """
        # Get conversation ID, fallback to internet message ID if conversation ID is not available
        conversation_id = getattr(message, 'conversation_id', None)
        if not conversation_id:
            conversation_id = getattr(message, 'internet_message_id', None)

        # If still no ID, create a unique ID based on subject and participants
        if not conversation_id:
            subject = getattr(message, 'subject', 'No Subject')
            from_email = ''
            if hasattr(message, 'from_') and message.from_ and hasattr(message.from_, 'email_address'):
                from_email = getattr(message.from_.email_address, 'address', '')
            conversation_id = f"subject_{hash(subject + from_email)}"

        return conversation_id


    async def get_conversations(self, inbox_top: int = 50, sent_top: int = 50) -> Dict[str, List]:
        """
        Get conversations based on conversation IDs from sent folder, including all related messages

        Args:
            inbox_top: Maximum number of inbox messages to fetch
            sent_top: Maximum number of sent messages to fetch

        Returns:
            Dictionary where keys are conversation IDs from sent messages and values are lists of all related messages
        """
        try:
            # Get messages from both folders separately
            inbox_task = self.get_inbox(inbox_top)
            sent_task = self.get_sent(sent_top)

            inbox_response, sent_response = await asyncio.gather(inbox_task, sent_task)

            # Extract message lists
            inbox_messages = inbox_response.value if inbox_response and inbox_response.value else []
            sent_messages = sent_response.value if sent_response and sent_response.value else []

            # Group messages by conversation (only those with messages in both folders)
            conversations = self.group_messages_by_conversation(inbox_messages, sent_messages)

            total_messages = len(inbox_messages) + len(sent_messages)
            logger.info(
                f"Found {len(conversations)} conversations based on sent folder conversation IDs (from {total_messages} total messages)")
            return conversations

        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            raise
