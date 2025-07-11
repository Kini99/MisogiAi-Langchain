"""
Email data models for the Intelligent Email Response System.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class Email(BaseModel):
    """Email model for processing incoming emails."""
    
    id: str = Field(..., description="Unique email identifier")
    subject: str = Field(..., description="Email subject line")
    sender: EmailStr = Field(..., description="Sender email address")
    recipients: List[EmailStr] = Field(default_factory=list, description="Recipient email addresses")
    cc: List[EmailStr] = Field(default_factory=list, description="CC recipients")
    bcc: List[EmailStr] = Field(default_factory=list, description="BCC recipients")
    body: str = Field(..., description="Email body content")
    html_body: Optional[str] = Field(None, description="HTML version of email body")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="Email received timestamp")
    thread_id: Optional[str] = Field(None, description="Email thread identifier")
    labels: List[str] = Field(default_factory=list, description="Gmail labels")
    attachments: List[str] = Field(default_factory=list, description="Attachment file names")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailResponse(BaseModel):
    """Response model for generated email responses."""
    
    email_id: str = Field(..., description="Original email ID")
    response_subject: str = Field(..., description="Response subject line")
    response_body: str = Field(..., description="Response body content")
    response_html_body: Optional[str] = Field(None, description="HTML version of response body")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")
    policy_references: List[str] = Field(default_factory=list, description="Referenced policy IDs")
    template_used: Optional[str] = Field(None, description="Template ID used for response")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence score for the response")
    auto_send: bool = Field(default=False, description="Whether to automatically send the response")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailBatch(BaseModel):
    """Batch processing model for multiple emails."""
    
    emails: List[Email] = Field(..., description="List of emails to process")
    batch_id: str = Field(..., description="Unique batch identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Batch creation timestamp")
    priority: str = Field(default="normal", description="Processing priority")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class EmailProcessingResult(BaseModel):
    """Result model for email processing."""
    
    email_id: str = Field(..., description="Processed email ID")
    success: bool = Field(..., description="Processing success status")
    response: Optional[EmailResponse] = Field(None, description="Generated response")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 