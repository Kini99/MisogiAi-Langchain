"""
Response template data models for the Intelligent Email Response System.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ResponseTemplate(BaseModel):
    """Email response template model."""
    
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    subject_template: str = Field(..., description="Subject line template")
    body_template: str = Field(..., description="Body content template")
    html_body_template: Optional[str] = Field(None, description="HTML body template")
    category: str = Field(..., description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    is_active: bool = Field(default=True, description="Whether template is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    author: str = Field(..., description="Template author")
    usage_count: int = Field(default=0, description="Number of times template was used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TemplateCreate(BaseModel):
    """Model for creating new response templates."""
    
    name: str = Field(..., description="Template name")
    subject_template: str = Field(..., description="Subject line template")
    body_template: str = Field(..., description="Body content template")
    html_body_template: Optional[str] = Field(None, description="HTML body template")
    category: str = Field(..., description="Template category")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    author: str = Field(..., description="Template author")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class TemplateUpdate(BaseModel):
    """Model for updating response templates."""
    
    name: Optional[str] = Field(None, description="Template name")
    subject_template: Optional[str] = Field(None, description="Subject line template")
    body_template: Optional[str] = Field(None, description="Body content template")
    html_body_template: Optional[str] = Field(None, description="HTML body template")
    category: Optional[str] = Field(None, description="Template category")
    tags: Optional[List[str]] = Field(None, description="Template tags")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    is_active: Optional[bool] = Field(None, description="Whether template is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TemplateRenderRequest(BaseModel):
    """Model for rendering template with variables."""
    
    template_id: str = Field(..., description="Template ID to render")
    variables: Dict[str, str] = Field(..., description="Variables to substitute in template")
    email_context: Optional[Dict[str, Any]] = Field(None, description="Email context for rendering")


class TemplateRenderResult(BaseModel):
    """Result model for template rendering."""
    
    template_id: str = Field(..., description="Rendered template ID")
    subject: str = Field(..., description="Rendered subject line")
    body: str = Field(..., description="Rendered body content")
    html_body: Optional[str] = Field(None, description="Rendered HTML body")
    variables_used: List[str] = Field(..., description="Variables that were used")
    missing_variables: List[str] = Field(default_factory=list, description="Missing variables")
    render_time: float = Field(..., description="Template rendering time in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 