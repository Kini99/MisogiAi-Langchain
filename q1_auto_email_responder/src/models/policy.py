"""
Policy data models for the Intelligent Email Response System.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PolicyCategory(str, Enum):
    """Enumeration of policy categories."""
    
    HR = "hr"
    IT = "it"
    FINANCE = "finance"
    LEGAL = "legal"
    OPERATIONS = "operations"
    CUSTOMER_SERVICE = "customer_service"
    GENERAL = "general"
    FAQ = "faq"


class Policy(BaseModel):
    """Company policy model."""
    
    id: str = Field(..., description="Unique policy identifier")
    title: str = Field(..., description="Policy title")
    content: str = Field(..., description="Policy content")
    category: PolicyCategory = Field(..., description="Policy category")
    tags: List[str] = Field(default_factory=list, description="Policy tags for search")
    version: str = Field(default="1.0", description="Policy version")
    effective_date: datetime = Field(default_factory=datetime.utcnow, description="Policy effective date")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    author: str = Field(..., description="Policy author")
    is_active: bool = Field(default=True, description="Whether policy is active")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PolicySearchResult(BaseModel):
    """Search result model for policy queries."""
    
    policy: Policy = Field(..., description="Matched policy")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    matched_terms: List[str] = Field(default_factory=list, description="Matched search terms")
    context: str = Field(..., description="Relevant context from policy")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PolicyUpdate(BaseModel):
    """Model for updating policies."""
    
    title: Optional[str] = Field(None, description="Policy title")
    content: Optional[str] = Field(None, description="Policy content")
    category: Optional[PolicyCategory] = Field(None, description="Policy category")
    tags: Optional[List[str]] = Field(None, description="Policy tags")
    version: Optional[str] = Field(None, description="Policy version")
    is_active: Optional[bool] = Field(None, description="Whether policy is active")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class PolicyCreate(BaseModel):
    """Model for creating new policies."""
    
    title: str = Field(..., description="Policy title")
    content: str = Field(..., description="Policy content")
    category: PolicyCategory = Field(..., description="Policy category")
    tags: List[str] = Field(default_factory=list, description="Policy tags")
    author: str = Field(..., description="Policy author")
    version: str = Field(default="1.0", description="Policy version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata") 