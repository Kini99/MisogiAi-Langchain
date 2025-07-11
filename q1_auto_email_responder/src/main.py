"""
Main application entry point for the Intelligent Email Response System.
"""

import asyncio
import signal
import sys
from datetime import datetime
from typing import List

from loguru import logger

from .config import get_settings, ensure_directories
from .models.email import Email, EmailBatch, EmailProcessingResult
from .services.gmail_service import GmailService
from .services.policy_service import policy_service
from .services.response_service import response_service
from .services.cache_service import cache_service


class EmailResponseSystem:
    """Main orchestrator for the intelligent email response system."""
    
    def __init__(self):
        """Initialize the email response system."""
        self.settings = get_settings()
        self.gmail_service = GmailService()
        self.running = False
        
        # Ensure directories exist
        ensure_directories()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start(self):
        """Start the email response system."""
        try:
            logger.info("Starting Intelligent Email Response System...")
            
            # Health checks
            await self._perform_health_checks()
            
            self.running = True
            
            # Main processing loop
            while self.running:
                try:
                    await self._process_email_batch()
                    await asyncio.sleep(60)  # Wait 1 minute between batches
                    
                except Exception as e:
                    logger.error(f"Error in main processing loop: {e}")
                    await asyncio.sleep(30)  # Wait 30 seconds on error
            
            logger.info("Email response system stopped")
            
        except Exception as e:
            logger.error(f"Failed to start email response system: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _perform_health_checks(self):
        """Perform health checks on all services."""
        logger.info("Performing health checks...")
        
        # Check cache service
        cache_healthy = await cache_service.health_check()
        if not cache_healthy:
            logger.warning("Cache service health check failed")
        
        # Check Gmail service (basic check)
        try:
            # This is a basic check - in production you might want to test API access
            logger.info("Gmail service initialized")
        except Exception as e:
            logger.error(f"Gmail service health check failed: {e}")
            raise
        
        # Check policy service
        try:
            stats = await policy_service.get_policy_stats()
            logger.info(f"Policy service healthy - {stats.get('total_policies', 0)} policies loaded")
        except Exception as e:
            logger.error(f"Policy service health check failed: {e}")
            raise
        
        logger.info("All health checks completed")
    
    async def _process_email_batch(self):
        """Process a batch of emails."""
        try:
            logger.info("Processing email batch...")
            
            # Get unread emails from Gmail
            emails = await self.gmail_service.get_emails(
                query="is:unread",
                max_results=self.settings.batch_size
            )
            
            if not emails:
                logger.info("No unread emails found")
                return
            
            logger.info(f"Found {len(emails)} unread emails")
            
            # Create batch
            batch = EmailBatch(
                emails=emails,
                batch_id=f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                priority="normal"
            )
            
            # Process batch
            results = await self._process_batch(batch)
            
            # Log results
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
            
            logger.info(f"Batch processing completed: {successful} successful, {failed} failed")
            
        except Exception as e:
            logger.error(f"Error processing email batch: {e}")
    
    async def _process_batch(self, batch: EmailBatch) -> List[EmailProcessingResult]:
        """Process a batch of emails and generate responses."""
        results = []
        
        for email in batch.emails:
            start_time = datetime.utcnow()
            
            try:
                # Generate response
                response = await response_service.generate_response(email)
                
                # Send response if auto-send is enabled
                if response.auto_send:
                    sent = await self.gmail_service.send_email(response, email)
                    if sent:
                        logger.info(f"Auto-sent response for email {email.id}")
                    else:
                        logger.warning(f"Failed to auto-send response for email {email.id}")
                
                # Mark email as processed
                await self.gmail_service.mark_email_as_read(email.id)
                await self.gmail_service.add_label(email.id, "AI_Processed")
                
                result = EmailProcessingResult(
                    email_id=email.id,
                    success=True,
                    response=response,
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
                
            except Exception as e:
                logger.error(f"Error processing email {email.id}: {e}")
                
                result = EmailProcessingResult(
                    email_id=email.id,
                    success=False,
                    error_message=str(e),
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            results.append(result)
        
        return results
    
    async def process_single_email(self, email_id: str) -> EmailProcessingResult:
        """Process a single email by ID."""
        try:
            # Get email from Gmail
            emails = await self.gmail_service.get_emails(
                query=f"id:{email_id}",
                max_results=1
            )
            
            if not emails:
                return EmailProcessingResult(
                    email_id=email_id,
                    success=False,
                    error_message="Email not found",
                    processing_time=0.0
                )
            
            email = emails[0]
            start_time = datetime.utcnow()
            
            # Generate response
            response = await response_service.generate_response(email)
            
            result = EmailProcessingResult(
                email_id=email_id,
                success=True,
                response=response,
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing single email {email_id}: {e}")
            return EmailProcessingResult(
                email_id=email_id,
                success=False,
                error_message=str(e),
                processing_time=0.0
            )
    
    async def get_system_status(self) -> dict:
        """Get system status and statistics."""
        try:
            # Get cache stats
            cache_stats = await cache_service.get_cache_stats()
            
            # Get policy stats
            policy_stats = await policy_service.get_policy_stats()
            
            # Get recent emails
            recent_emails = await self.gmail_service.get_emails(
                query="is:unread",
                max_results=5
            )
            
            return {
                "status": "running" if self.running else "stopped",
                "timestamp": datetime.utcnow().isoformat(),
                "cache": cache_stats,
                "policies": policy_stats,
                "recent_emails": len(recent_emails),
                "services": {
                    "gmail": "connected",
                    "cache": "healthy" if await cache_service.health_check() else "unhealthy",
                    "policy": "healthy",
                    "response": "ready"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _cleanup(self):
        """Cleanup resources on shutdown."""
        try:
            logger.info("Cleaning up resources...")
            
            # Close cache connection
            await cache_service.close()
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=get_settings().log_level
    )
    logger.add(
        "logs/email_system.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO"
    )
    
    # Create and start system
    system = EmailResponseSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 