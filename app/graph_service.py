from configparser import SectionProxy
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GraphService:
    """Enhanced Graph service for API usage"""
    
    def __init__(self, client_id: str, tenant_id: str, scopes: str):
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.graph_scopes = scopes.split(' ')
        
        self.device_code_credential = DeviceCodeCredential(
            client_id=client_id, 
            tenant_id=tenant_id
        )
        self.user_client = GraphServiceClient(
            self.device_code_credential, 
            self.graph_scopes
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

            user = await self.user_client.me.get(request_configuration=request_config)
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
                select=['from', 'isRead', 'receivedDateTime', 'subject', 'body'],
                top=top,
                orderby=['receivedDateTime DESC']
            )
            request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
                query_parameters=query_params
            )

            messages = await self.user_client.me.mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config)
            return messages
        except ODataError as e:
            logger.error(f"OData error getting inbox: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting inbox: {e}")
            raise

    async def send_mail(self, subject: str, body: str, recipient: str, body_type: str = "text"):
        """Send an email message"""
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

            request_body = SendMailPostRequestBody()
            request_body.message = message

            await self.user_client.me.send_mail.post(body=request_body)
            return True
        except ODataError as e:
            logger.error(f"OData error sending mail: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending mail: {e}")
            raise
