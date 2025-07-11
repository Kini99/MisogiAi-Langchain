"""
Gmail MCP integration service for email processing.
"""

import asyncio
import base64
import email
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from loguru import logger

from ..config import get_settings
from ..models.email import Email, EmailResponse, EmailBatch, EmailProcessingResult


class GmailService:
    """Gmail MCP integration service for email operations."""
    
    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    def __init__(self):
        """Initialize Gmail service with authentication."""
        self.settings = get_settings()
        self.service = None
        self.credentials = None
        self._initialize_credentials()
    
    def _initialize_credentials(self):
        """Initialize Gmail API credentials."""
        try:
            # Create credentials from environment variables
            self.credentials = Credentials(
                token=None,
                refresh_token=self.settings.gmail_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.settings.gmail_client_id,
                client_secret=self.settings.gmail_client_secret,
                scopes=self.SCOPES
            )
            
            # Refresh token if needed
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.info("Gmail service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gmail service: {e}")
            raise
    
    async def get_emails(self, query: str = "is:unread", max_results: int = 10) -> List[Email]:
        """Retrieve emails from Gmail using MCP."""
        try:
            # Get messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                email_data = await self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"Retrieved {len(emails)} emails from Gmail")
            return emails
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise
        except Exception as e:
            logger.error(f"Error retrieving emails: {e}")
            raise
    
    async def _get_email_details(self, message_id: str) -> Optional[Email]:
        """Get detailed email information."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Parse email body
            body = self._extract_email_body(message['payload'])
            
            # Parse recipients
            to_header = next((h['value'] for h in headers if h['name'] == 'To'), '')
            recipients = [email.strip() for email in to_header.split(',') if email.strip()]
            
            # Parse CC
            cc_header = next((h['value'] for h in headers if h['name'] == 'Cc'), '')
            cc = [email.strip() for email in cc_header.split(',') if email.strip()] if cc_header else []
            
            # Parse date
            try:
                received_at = email.utils.parsedate_to_datetime(date_str)
            except:
                received_at = datetime.utcnow()
            
            return Email(
                id=message_id,
                subject=subject,
                sender=sender,
                recipients=recipients,
                cc=cc,
                body=body,
                received_at=received_at,
                thread_id=message.get('threadId'),
                labels=message.get('labelIds', [])
            )
            
        except Exception as e:
            logger.error(f"Error getting email details for {message_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict[str, Any]) -> str:
        """Extract email body from Gmail message payload."""
        if 'body' in payload and payload['body'].get('data'):
            return base64.urlsafe_b64decode(
                payload['body']['data'].encode('ASCII')
            ).decode('utf-8')
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if part['body'].get('data'):
                        return base64.urlsafe_b64decode(
                            part['body']['data'].encode('ASCII')
                        ).decode('utf-8')
        
        return ""
    
    async def send_email(self, response: EmailResponse, original_email: Email) -> bool:
        """Send email response using Gmail MCP."""
        try:
            # Create email message
            message = self._create_email_message(response, original_email)
            
            # Send email
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            logger.info(f"Email sent successfully: {sent_message['id']}")
            return True
            
        except HttpError as error:
            logger.error(f"Gmail API error sending email: {error}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    def _create_email_message(self, response: EmailResponse, original_email: Email) -> Dict[str, Any]:
        """Create Gmail message format."""
        # Create email content
        email_content = f"""From: {original_email.recipients[0] if original_email.recipients else 'me'}
To: {original_email.sender}
Subject: {response.response_subject}

{response.response_body}
"""
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(
            email_content.encode('utf-8')
        ).decode('utf-8')
        
        return {
            'raw': encoded_message
        }
    
    async def mark_email_as_read(self, email_id: str) -> bool:
        """Mark email as read in Gmail."""
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            logger.info(f"Email {email_id} marked as read")
            return True
            
        except Exception as e:
            logger.error(f"Error marking email as read: {e}")
            return False
    
    async def add_label(self, email_id: str, label_name: str) -> bool:
        """Add label to email in Gmail."""
        try:
            # Get or create label
            label_id = await self._get_or_create_label(label_name)
            
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'addLabelIds': [label_id]}
            ).execute()
            
            logger.info(f"Label '{label_name}' added to email {email_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding label: {e}")
            return False
    
    async def _get_or_create_label(self, label_name: str) -> str:
        """Get existing label or create new one."""
        try:
            # List existing labels
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            # Create new label
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            
            created_label = self.service.users().labels().create(
                userId='me',
                body=label_object
            ).execute()
            
            return created_label['id']
            
        except Exception as e:
            logger.error(f"Error getting/creating label: {e}")
            raise
    
    async def process_email_batch(self, batch: EmailBatch) -> List[EmailProcessingResult]:
        """Process a batch of emails."""
        results = []
        
        for email in batch.emails:
            start_time = datetime.utcnow()
            try:
                # Mark email as read
                await self.mark_email_as_read(email.id)
                
                # Add processing label
                await self.add_label(email.id, "AI_Processed")
                
                result = EmailProcessingResult(
                    email_id=email.id,
                    success=True,
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
                
            except Exception as e:
                result = EmailProcessingResult(
                    email_id=email.id,
                    success=False,
                    error_message=str(e),
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            results.append(result)
        
        logger.info(f"Processed batch {batch.batch_id} with {len(results)} results")
        return results 