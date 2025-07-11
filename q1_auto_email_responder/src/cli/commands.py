"""
CLI commands for the Intelligent Email Response System.
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from ..config import get_settings, ensure_directories
from ..models.policy import PolicyCreate, PolicyCategory
from ..services.gmail_service import GmailService
from ..services.policy_service import policy_service
from ..services.response_service import response_service
from ..services.cache_service import cache_service
from ..main import EmailResponseSystem


async def process_emails_command(args):
    """Process emails in batch."""
    try:
        logger.info("Starting email processing...")
        
        # Initialize system
        system = EmailResponseSystem()
        
        # Get emails from Gmail
        gmail_service = GmailService()
        emails = await gmail_service.get_emails(
            query=args.query,
            max_results=args.batch_size
        )
        
        if not emails:
            logger.info("No emails found matching the query")
            return
        
        logger.info(f"Found {len(emails)} emails to process")
        
        # Process emails
        results = await system._process_batch(
            emails=emails,
            batch_id=f"cli_batch_{args.batch_size}"
        )
        
        # Display results
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        logger.info(f"Processing completed: {successful} successful, {failed} failed")
        
        if args.verbose:
            for result in results:
                if result.success:
                    logger.info(f"✓ Email {result.email_id}: {result.processing_time:.2f}s")
                else:
                    logger.error(f"✗ Email {result.email_id}: {result.error_message}")
        
    except Exception as e:
        logger.error(f"Error processing emails: {e}")
        sys.exit(1)


async def add_policy_command(args):
    """Add a new policy."""
    try:
        logger.info("Adding new policy...")
        
        # Read policy content from file
        if args.file:
            with open(args.file, 'r') as f:
                content = f.read()
        else:
            content = args.content
        
        # Create policy data
        policy_data = PolicyCreate(
            title=args.title,
            content=content,
            category=PolicyCategory(args.category),
            tags=args.tags.split(',') if args.tags else [],
            author=args.author
        )
        
        # Add policy
        policy = await policy_service.add_policy(policy_data)
        
        logger.info(f"Policy added successfully: {policy.id}")
        logger.info(f"Title: {policy.title}")
        logger.info(f"Category: {policy.category.value}")
        
    except Exception as e:
        logger.error(f"Error adding policy: {e}")
        sys.exit(1)


async def list_policies_command(args):
    """List all policies."""
    try:
        logger.info("Fetching policies...")
        
        if args.category:
            policies = await policy_service.get_policies_by_category(
                PolicyCategory(args.category)
            )
        else:
            policies = await policy_service.get_all_policies()
        
        if not policies:
            logger.info("No policies found")
            return
        
        logger.info(f"Found {len(policies)} policies:")
        logger.info("-" * 80)
        
        for policy in policies:
            logger.info(f"ID: {policy.id}")
            logger.info(f"Title: {policy.title}")
            logger.info(f"Category: {policy.category.value}")
            logger.info(f"Author: {policy.author}")
            logger.info(f"Active: {policy.is_active}")
            logger.info(f"Last Updated: {policy.last_updated}")
            logger.info("-" * 80)
        
    except Exception as e:
        logger.error(f"Error listing policies: {e}")
        sys.exit(1)


async def search_policies_command(args):
    """Search policies."""
    try:
        logger.info(f"Searching policies for: {args.query}")
        
        category = PolicyCategory(args.category) if args.category else None
        
        results = await policy_service.search_policies(
            query=args.query,
            category=category,
            limit=args.limit
        )
        
        if not results:
            logger.info("No policies found matching the query")
            return
        
        logger.info(f"Found {len(results)} matching policies:")
        logger.info("-" * 80)
        
        for result in results:
            policy = result.policy
            logger.info(f"Title: {policy.title}")
            logger.info(f"Category: {policy.category.value}")
            logger.info(f"Relevance Score: {result.relevance_score:.3f}")
            logger.info(f"Context: {result.context}")
            logger.info("-" * 80)
        
    except Exception as e:
        logger.error(f"Error searching policies: {e}")
        sys.exit(1)


async def generate_response_command(args):
    """Generate response for an email."""
    try:
        logger.info("Generating response...")
        
        # Create mock email for testing
        from ..models.email import Email
        
        email = Email(
            id=args.email_id or "test_email",
            subject=args.subject or "Test Email",
            sender=args.sender or "test@example.com",
            body=args.body or "This is a test email body.",
            recipients=["recipient@example.com"]
        )
        
        # Generate response
        response = await response_service.generate_response(email)
        
        logger.info("Generated response:")
        logger.info("-" * 80)
        logger.info(f"Subject: {response.response_subject}")
        logger.info(f"Confidence: {response.confidence_score:.3f}")
        logger.info(f"Auto-send: {response.auto_send}")
        logger.info("-" * 80)
        logger.info("Response Body:")
        logger.info(response.response_body)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(response.dict(), f, indent=2, default=str)
            logger.info(f"Response saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        sys.exit(1)


async def system_status_command(args):
    """Show system status."""
    try:
        logger.info("Checking system status...")
        
        system = EmailResponseSystem()
        status = await system.get_system_status()
        
        logger.info("System Status:")
        logger.info("-" * 80)
        logger.info(f"Status: {status['status']}")
        logger.info(f"Timestamp: {status['timestamp']}")
        
        if 'cache' in status:
            cache = status['cache']
            logger.info(f"Cache Hit Rate: {cache.get('hit_rate', 0):.3f}")
            logger.info(f"Cache Memory: {cache.get('used_memory_human', 'N/A')}")
        
        if 'policies' in status:
            policies = status['policies']
            logger.info(f"Total Policies: {policies.get('total_policies', 0)}")
            logger.info(f"Active Policies: {policies.get('active_policies', 0)}")
        
        if 'services' in status:
            services = status['services']
            logger.info("Services:")
            for service, health in services.items():
                logger.info(f"  {service}: {health}")
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        sys.exit(1)


async def cache_stats_command(args):
    """Show cache statistics."""
    try:
        logger.info("Fetching cache statistics...")
        
        stats = await cache_service.get_cache_stats()
        
        logger.info("Cache Statistics:")
        logger.info("-" * 80)
        logger.info(f"Hit Rate: {stats.get('hit_rate', 0):.3f}")
        logger.info(f"Total Commands: {stats.get('total_commands_processed', 0)}")
        logger.info(f"Memory Usage: {stats.get('used_memory_human', 'N/A')}")
        logger.info(f"Connected Clients: {stats.get('connected_clients', 0)}")
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        sys.exit(1)


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    logger.remove()
    
    if verbose:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG"
        )
    else:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO"
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Intelligent Email Response System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli process-emails --batch-size 10
  python -m src.cli add-policy --file policy.md --category hr --title "HR Policy"
  python -m src.cli search-policies --query "vacation policy"
  python -m src.cli generate-response --subject "Test" --body "Test email body"
  python -m src.cli status
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Process emails command
    process_parser = subparsers.add_parser('process-emails', help='Process emails in batch')
    process_parser.add_argument('--query', default='is:unread', help='Gmail query')
    process_parser.add_argument('--batch-size', type=int, default=10, help='Batch size')
    process_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # Add policy command
    add_policy_parser = subparsers.add_parser('add-policy', help='Add a new policy')
    add_policy_parser.add_argument('--title', required=True, help='Policy title')
    add_policy_parser.add_argument('--file', help='Policy file path')
    add_policy_parser.add_argument('--content', help='Policy content')
    add_policy_parser.add_argument('--category', required=True, choices=[c.value for c in PolicyCategory], help='Policy category')
    add_policy_parser.add_argument('--tags', help='Comma-separated tags')
    add_policy_parser.add_argument('--author', required=True, help='Policy author')
    
    # List policies command
    list_policies_parser = subparsers.add_parser('list-policies', help='List all policies')
    list_policies_parser.add_argument('--category', choices=[c.value for c in PolicyCategory], help='Filter by category')
    
    # Search policies command
    search_policies_parser = subparsers.add_parser('search-policies', help='Search policies')
    search_policies_parser.add_argument('--query', required=True, help='Search query')
    search_policies_parser.add_argument('--category', choices=[c.value for c in PolicyCategory], help='Filter by category')
    search_policies_parser.add_argument('--limit', type=int, default=5, help='Maximum results')
    
    # Generate response command
    generate_parser = subparsers.add_parser('generate-response', help='Generate response for email')
    generate_parser.add_argument('--email-id', help='Email ID')
    generate_parser.add_argument('--subject', help='Email subject')
    generate_parser.add_argument('--sender', help='Sender email')
    generate_parser.add_argument('--body', help='Email body')
    generate_parser.add_argument('--output', help='Output file for response')
    
    # System status command
    subparsers.add_parser('status', help='Show system status')
    
    # Cache stats command
    subparsers.add_parser('cache-stats', help='Show cache statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Ensure directories exist
    ensure_directories()
    
    # Run command
    try:
        if args.command == 'process-emails':
            asyncio.run(process_emails_command(args))
        elif args.command == 'add-policy':
            asyncio.run(add_policy_command(args))
        elif args.command == 'list-policies':
            asyncio.run(list_policies_command(args))
        elif args.command == 'search-policies':
            asyncio.run(search_policies_command(args))
        elif args.command == 'generate-response':
            asyncio.run(generate_response_command(args))
        elif args.command == 'status':
            asyncio.run(system_status_command(args))
        elif args.command == 'cache-stats':
            asyncio.run(cache_stats_command(args))
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 