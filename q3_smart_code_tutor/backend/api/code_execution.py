"""
REST API endpoints for code execution
"""
import asyncio
import json
import logging
from typing import Dict, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.services.e2b_service import E2BService
from backend.services.code_analyzer import CodeAnalyzer
from backend.core.config import settings

logger = logging.getLogger(__name__)

# Initialize services
e2b_service = E2BService()
code_analyzer = CodeAnalyzer()

# Create router
router = APIRouter()


class CodeExecutionRequest(BaseModel):
    """Request model for code execution"""
    code: str
    language: str = "python"
    timeout: Optional[int] = None


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""
    code: str
    language: str = "python"


class CodeExecutionResponse(BaseModel):
    """Response model for code execution"""
    execution_id: str
    status: str
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest, background_tasks: BackgroundTasks):
    """Execute code in a secure sandbox"""
    try:
        execution_id = str(uuid4())
        
        # Validate language
        if request.language not in ["python", "javascript"]:
            raise HTTPException(status_code=400, detail="Unsupported language")
            
        # Set timeout
        timeout = request.timeout or settings.max_execution_time
        
        # Execute code asynchronously
        if request.language == "python":
            result = await e2b_service.execute_python_code(request.code, execution_id)
        else:
            result = await e2b_service.execute_javascript_code(request.code, execution_id)
            
        # Collect output
        output_chunks = []
        async for chunk in result:
            output_chunks.append(chunk)
            
        output = "".join(output_chunks)
        
        return CodeExecutionResponse(
            execution_id=execution_id,
            status="completed",
            output=output
        )
        
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code and provide insights"""
    try:
        analysis = await code_analyzer.analyze_code(request.code, request.language)
        return {"analysis": analysis}
        
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "e2b": e2b_service.is_available(),
            "code_analyzer": True
        }
    }


@router.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "languages": [
            {
                "name": "Python",
                "id": "python",
                "version": "3.11",
                "features": ["execution", "analysis", "linting"]
            },
            {
                "name": "JavaScript",
                "id": "javascript", 
                "version": "Node.js 18",
                "features": ["execution", "analysis"]
            }
        ]
    } 