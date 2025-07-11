"""
Main FastAPI application for the Code Interpreter
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from backend.api.code_execution import router as CodeExecutionRouter
from backend.api.websocket_manager import WebSocketManager
from backend.core.config import settings
from backend.services.e2b_service import E2BService
from backend.services.rag_service import RAGService
from backend.services.code_analyzer import CodeAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Code Interpreter API",
    description="Full-stack code interpreter with real-time streaming and RAG-powered explanations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
websocket_manager = WebSocketManager()
e2b_service = E2BService()
rag_service = RAGService()
code_analyzer = CodeAnalyzer()

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend/public"), name="static")

# Include routers
app.include_router(CodeExecutionRouter, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page"""
    with open("frontend/public/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket, client_id)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(websocket, client_id, message)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        websocket_manager.disconnect(client_id)

async def handle_websocket_message(websocket: WebSocket, client_id: str, message: Dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "code_execution":
        await handle_code_execution(websocket, client_id, message)
    elif message_type == "code_analysis":
        await handle_code_analysis(websocket, client_id, message)
    elif message_type == "rag_query":
        await handle_rag_query(websocket, client_id, message)
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))

async def handle_code_execution(websocket: WebSocket, client_id: str, message: Dict):
    """Handle code execution requests"""
    try:
        code = message.get("code", "")
        language = message.get("language", "python")
        execution_id = str(uuid4())
        
        # Send execution start message
        await websocket.send_text(json.dumps({
            "type": "execution_start",
            "execution_id": execution_id,
            "message": "Starting code execution..."
        }))
        
        # Execute code in E2B sandbox
        if language == "python":
            result = await e2b_service.execute_python_code(code, execution_id)
        elif language == "javascript":
            result = await e2b_service.execute_javascript_code(code, execution_id)
        else:
            raise ValueError(f"Unsupported language: {language}")
        
        # Stream results
        async for chunk in result:
            await websocket.send_text(json.dumps({
                "type": "execution_output",
                "execution_id": execution_id,
                "data": chunk
            }))
        
        # Send execution completion
        await websocket.send_text(json.dumps({
            "type": "execution_complete",
            "execution_id": execution_id,
            "message": "Code execution completed"
        }))
        
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        await websocket.send_text(json.dumps({
            "type": "execution_error",
            "execution_id": execution_id if 'execution_id' in locals() else None,
            "error": str(e)
        }))

async def handle_code_analysis(websocket: WebSocket, client_id: str, message: Dict):
    """Handle code analysis requests"""
    try:
        code = message.get("code", "")
        language = message.get("language", "python")
        
        # Analyze code
        analysis = await code_analyzer.analyze_code(code, language)
        
        # Send analysis results
        await websocket.send_text(json.dumps({
            "type": "analysis_result",
            "data": analysis
        }))
        
    except Exception as e:
        logger.error(f"Code analysis error: {e}")
        await websocket.send_text(json.dumps({
            "type": "analysis_error",
            "error": str(e)
        }))

async def handle_rag_query(websocket: WebSocket, client_id: str, message: Dict):
    """Handle RAG query requests"""
    try:
        query = message.get("query", "")
        context = message.get("context", "")
        
        # Get RAG response
        response = await rag_service.get_explanation(query, context)
        
        # Stream RAG response
        async for chunk in response:
            await websocket.send_text(json.dumps({
                "type": "rag_response",
                "data": chunk
            }))
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        await websocket.send_text(json.dumps({
            "type": "rag_error",
            "error": str(e)
        }))

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Code Interpreter API...")
    await rag_service.initialize()
    await e2b_service.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Code Interpreter API...")
    await e2b_service.cleanup()

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 