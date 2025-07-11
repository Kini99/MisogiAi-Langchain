"""
E2B service for secure code execution in sandboxed environments
"""
import asyncio
import json
import logging
import os
from typing import AsyncGenerator, Dict, Optional
from uuid import uuid4

from e2b import AsyncSandbox
from backend.core.config import settings

logger = logging.getLogger(__name__)


class E2BService:
    """Service for executing code in E2B sandboxed environments"""
    
    def __init__(self):
        self.api_key = settings.e2b_api_key
        self.project_id = settings.e2b_project_id
        self.active_sessions: Dict[str, AsyncSandbox] = {}
        self.max_sessions = 10
        
    async def initialize(self):
        """Initialize the E2B service"""
        if not self.api_key:
            logger.warning("E2B API key not provided. Code execution will be limited.")
            return
            
        try:
            # Test connection
            session = await self._create_session("test")
            await session.close()
            logger.info("E2B service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize E2B service: {e}")
            
    async def cleanup(self):
        """Cleanup all active sessions"""
        for session_id, session in self.active_sessions.items():
            try:
                await session.close()
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")
                
        self.active_sessions.clear()
        logger.info("E2B service cleanup completed")
        
    def is_available(self) -> bool:
        """Check if E2B service is available"""
        return bool(self.api_key)
        
    async def _create_session(self, session_id: str) -> AsyncSandbox:
        """Create a new E2B session"""
        if len(self.active_sessions) >= self.max_sessions:
            # Close oldest session
            oldest_session_id = next(iter(self.active_sessions))
            await self._close_session(oldest_session_id)
            
        session = await AsyncSandbox.create(
            api_key=self.api_key
        )
        
        self.active_sessions[session_id] = session
        return session
        
    async def _close_session(self, session_id: str):
        """Close a specific session"""
        if session_id in self.active_sessions:
            try:
                await self.active_sessions[session_id].close()
                del self.active_sessions[session_id]
            except Exception as e:
                logger.error(f"Error closing session {session_id}: {e}")
                
    async def execute_python_code(self, code: str, execution_id: str) -> AsyncGenerator[str, None]:
        """Execute Python code in E2B sandbox"""
        if not self.is_available():
            yield "E2B service not available. Please configure E2B API key."
            return
            
        session = None
        try:
            # Create session
            session = await self._create_session(execution_id)
            
            # Prepare code with proper output handling
            wrapped_code = self._wrap_python_code(code)
            
            # Execute code
            process = await session.process.start(
                cmd=f"python3 -c '{wrapped_code}'"
            )
            
            # Stream output
            async for output in process.output:
                if output.line:
                    yield output.line + "\n"
                    
            # Check for errors
            if process.exit_code != 0:
                yield f"Execution completed with exit code: {process.exit_code}\n"
                
        except Exception as e:
            logger.error(f"Python execution error: {e}")
            yield f"Execution error: {str(e)}\n"
            
        finally:
            if session:
                await self._close_session(execution_id)
                
    async def execute_javascript_code(self, code: str, execution_id: str) -> AsyncGenerator[str, None]:
        """Execute JavaScript code in E2B sandbox"""
        if not self.is_available():
            yield "E2B service not available. Please configure E2B API key."
            return
            
        session = None
        try:
            # Create session
            session = await self._create_session(execution_id)
            
            # Prepare code with proper output handling
            wrapped_code = self._wrap_javascript_code(code)
            
            # Execute code
            process = await session.process.start(
                cmd=f"node -e '{wrapped_code}'"
            )
            
            # Stream output
            async for output in process.output:
                if output.line:
                    yield output.line + "\n"
                    
            # Check for errors
            if process.exit_code != 0:
                yield f"Execution completed with exit code: {process.exit_code}\n"
                
        except Exception as e:
            logger.error(f"JavaScript execution error: {e}")
            yield f"Execution error: {str(e)}\n"
            
        finally:
            if session:
                await self._close_session(execution_id)
                
    def _wrap_python_code(self, code: str) -> str:
        """Wrap Python code with proper output handling"""
        # Escape single quotes in the code
        escaped_code = code.replace("'", "\\'")
        
        # Wrap with try-catch and proper output handling
        wrapped = f"""
import sys
import traceback

try:
    {escaped_code}
except Exception as e:
    print(f"Error: {{e}}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
"""
        return wrapped.replace("\n", "; ")
        
    def _wrap_javascript_code(self, code: str) -> str:
        """Wrap JavaScript code with proper output handling"""
        # Escape single quotes in the code
        escaped_code = code.replace("'", "\\'")
        
        # Wrap with try-catch and proper output handling
        wrapped = f"""
try {{
    {escaped_code}
}} catch (error) {{
    console.error('Error:', error.message);
    console.error(error.stack);
}}
"""
        return wrapped.replace("\n", " ")
        
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a specific session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            return {
                "session_id": session_id,
                "status": "active",
                "created_at": getattr(session, 'created_at', None)
            }
        return None
        
    async def list_active_sessions(self) -> Dict[str, Dict]:
        """List all active sessions"""
        sessions = {}
        for session_id in self.active_sessions:
            sessions[session_id] = await self.get_session_info(session_id)
        return sessions 