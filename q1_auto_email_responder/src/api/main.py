"""
FastAPI main application for the Intelligent Email Response System.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import get_settings
from ..models.email import Email, EmailResponse, EmailBatch, EmailProcessingResult
from ..models.policy import Policy, PolicyCreate, PolicyUpdate, PolicyCategory
from ..models.template import ResponseTemplate, TemplateCreate, TemplateUpdate
from ..services.gmail_service import GmailService
from ..services.policy_service import policy_service
from ..services.response_service import response_service
from ..services.cache_service import cache_service
from ..main import EmailResponseSystem


# Create FastAPI app
app = FastAPI(
    title="Intelligent Email Response System",
    description="AI-powered email response system with Gmail MCP integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global system instance
email_system = EmailResponseSystem()
gmail_service = GmailService()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        cache_healthy = await cache_service.health_check()
        policy_stats = await policy_service.get_policy_stats()
        
        return {
            "status": "healthy" if cache_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "cache": "healthy" if cache_healthy else "unhealthy",
                "policy": "healthy" if policy_stats else "unhealthy",
                "gmail": "connected"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )


# System status endpoint
@app.get("/api/status")
async def get_system_status():
    """Get detailed system status."""
    return await email_system.get_system_status()


# Email processing endpoints
@app.post("/api/emails/process")
async def process_emails(background_tasks: BackgroundTasks):
    """Process unread emails in background."""
    try:
        emails = await gmail_service.get_emails(
            query="is:unread",
            max_results=get_settings().batch_size
        )
        
        if not emails:
            return {"message": "No unread emails found", "processed": 0}
        
        background_tasks.add_task(process_email_batch, emails)
        
        return {
            "message": f"Processing {len(emails)} emails in background",
            "emails_count": len(emails)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def process_email_batch(emails: List[Email]):
    """Background task to process email batch."""
    try:
        batch = EmailBatch(
            emails=emails,
            batch_id=f"api_batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            priority="normal"
        )
        
        results = await email_system._process_batch(batch)
        successful = sum(1 for r in results if r.success)
        print(f"API batch processing completed: {successful}/{len(results)} successful")
        
    except Exception as e:
        print(f"Error in background email processing: {e}")


@app.post("/api/emails/{email_id}/process")
async def process_single_email(email_id: str):
    """Process a single email by ID."""
    try:
        result = await email_system.process_single_email(email_id)
        
        if not result.success:
            raise HTTPException(status_code=404, detail=result.error_message)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/emails")
async def get_emails(query: str = "is:unread", max_results: int = 10):
    """Get emails from Gmail."""
    try:
        emails = await gmail_service.get_emails(query=query, max_results=max_results)
        return {"emails": emails, "count": len(emails)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Policy management endpoints
@app.get("/api/policies")
async def get_policies(category: Optional[PolicyCategory] = None):
    """Get all policies or policies by category."""
    try:
        if category:
            policies = await policy_service.get_policies_by_category(category)
        else:
            policies = await policy_service.get_all_policies()
        
        return {"policies": policies, "count": len(policies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/{policy_id}")
async def get_policy(policy_id: str):
    """Get a specific policy by ID."""
    try:
        policy = await policy_service.get_policy(policy_id)
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/policies")
async def create_policy(policy_data: PolicyCreate):
    """Create a new policy."""
    try:
        policy = await policy_service.add_policy(policy_data)
        return policy
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/policies/{policy_id}")
async def update_policy(policy_id: str, updates: PolicyUpdate):
    """Update an existing policy."""
    try:
        policy = await policy_service.update_policy(policy_id, updates)
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/policies/{policy_id}")
async def delete_policy(policy_id: str):
    """Delete a policy."""
    try:
        success = await policy_service.delete_policy(policy_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        return {"message": "Policy deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/search")
async def search_policies(
    query: str,
    category: Optional[PolicyCategory] = None,
    limit: int = 5
):
    """Search policies using semantic search."""
    try:
        results = await policy_service.search_policies(
            query=query,
            category=category,
            limit=limit
        )
        
        return {"results": results, "count": len(results)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/policies/stats")
async def get_policy_stats():
    """Get policy statistics."""
    try:
        stats = await policy_service.get_policy_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Response generation endpoint
@app.post("/api/responses/generate")
async def generate_response(email_data: Email):
    """Generate response for an email."""
    try:
        response = await response_service.generate_response(email_data)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/responses/batch")
async def generate_batch_responses(emails: List[Email]):
    """Generate responses for multiple emails."""
    try:
        responses = await response_service.batch_generate_responses(emails)
        return {"responses": responses, "count": len(responses)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Intelligent Email Response System",
        "version": "1.0.0",
        "description": "AI-powered email response system with Gmail MCP integration",
        "endpoints": {
            "health": "/health",
            "status": "/api/status",
            "docs": "/docs",
            "emails": "/api/emails",
            "policies": "/api/policies",
            "responses": "/api/responses"
        }
    } 