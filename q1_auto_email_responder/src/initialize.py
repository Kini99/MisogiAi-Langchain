"""
Initialization script for the Intelligent Email Response System.
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

from .config import ensure_directories, get_settings
from .services.policy_service import policy_service
from .services.cache_service import cache_service
from .models.policy import PolicyCreate, PolicyCategory


async def initialize_system():
    """Initialize the email response system."""
    try:
        logger.info("Initializing Intelligent Email Response System...")
        
        # Ensure directories exist
        ensure_directories()
        logger.info("✓ Directories created")
        
        # Test cache connection
        cache_healthy = await cache_service.health_check()
        if cache_healthy:
            logger.info("✓ Cache service connected")
        else:
            logger.warning("⚠ Cache service not available")
        
        # Load sample policies
        await load_sample_policies()
        logger.info("✓ Sample policies loaded")
        
        # Get system stats
        stats = await policy_service.get_policy_stats()
        logger.info(f"✓ System initialized with {stats.get('total_policies', 0)} policies")
        
        logger.info("System initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)


async def load_sample_policies():
    """Load sample policies from the data directory."""
    try:
        settings = get_settings()
        policies_dir = settings.policies_dir
        
        # Sample policies to create
        sample_policies = [
            {
                "title": "Employee Vacation Policy",
                "content": """This policy outlines the vacation and time-off procedures for all employees.

Vacation Accrual:
- Full-time employees accrue 15 days of vacation per year
- Part-time employees accrue vacation on a pro-rated basis
- Vacation days roll over to the next year (maximum 30 days)

Requesting Vacation:
1. Submit vacation request at least 2 weeks in advance
2. Use the online vacation request system
3. Include start date, end date, and reason for vacation
4. Manager approval required for all requests

For questions about this policy, contact HR at hr@company.com.""",
                "category": PolicyCategory.HR,
                "tags": ["vacation", "time-off", "hr", "employee"],
                "author": "system"
            },
            {
                "title": "IT Support Policy",
                "content": """This policy covers IT support procedures and equipment management for all employees.

IT Support Hours:
- Monday to Friday: 8:00 AM - 6:00 PM
- Weekend support: 9:00 AM - 5:00 PM (emergency only)
- After-hours support available for critical issues

Requesting IT Support:
1. Submit ticket through the IT help desk portal
2. Include detailed description of the issue
3. Provide screenshots or error messages when possible
4. Include your contact information and preferred contact method

Response Times:
- Critical issues (system down): 2 hours
- High priority (work blocking): 4 hours
- Medium priority (feature request): 24 hours
- Low priority (general questions): 48 hours

Contact: it-support@company.com""",
                "category": PolicyCategory.IT,
                "tags": ["support", "it", "helpdesk", "equipment"],
                "author": "system"
            },
            {
                "title": "Expense Reimbursement Policy",
                "content": """This policy outlines the procedures for expense reimbursement and business travel.

Eligible Expenses:
- Business travel (airfare, hotel, meals)
- Office supplies and equipment
- Professional development and training
- Client entertainment (with approval)

Submission Requirements:
1. Submit expense report within 30 days of purchase
2. Include original receipts for all expenses
3. Provide business justification for each expense
4. Manager approval required for expenses over $500

Processing Time:
- Standard processing: 5-7 business days
- Rush processing: 2-3 business days (for urgent requests)

Contact: finance@company.com""",
                "category": PolicyCategory.FINANCE,
                "tags": ["expenses", "reimbursement", "travel", "finance"],
                "author": "system"
            },
            {
                "title": "Remote Work Policy",
                "content": """This policy establishes guidelines for remote work arrangements.

Remote Work Eligibility:
- Full-time employees with 6+ months of service
- Performance rating of "Meets Expectations" or higher
- Manager approval required
- IT equipment and security requirements must be met

Remote Work Guidelines:
- Maintain regular business hours
- Be available for meetings and calls
- Use company-approved communication tools
- Secure internet connection required
- Dedicated workspace recommended

Equipment and Security:
- Company laptop provided for remote work
- VPN connection required for company resources
- Two-factor authentication mandatory
- Regular security updates must be installed

Contact: hr@company.com""",
                "category": PolicyCategory.HR,
                "tags": ["remote", "work", "telecommute", "hr"],
                "author": "system"
            }
        ]
        
        # Create policies
        for policy_data in sample_policies:
            try:
                policy_create = PolicyCreate(**policy_data)
                await policy_service.add_policy(policy_create)
                logger.debug(f"Created policy: {policy_data['title']}")
            except Exception as e:
                logger.warning(f"Failed to create policy {policy_data['title']}: {e}")
        
    except Exception as e:
        logger.error(f"Error loading sample policies: {e}")
        raise


def main():
    """Main initialization function."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run initialization
    asyncio.run(initialize_system())


if __name__ == "__main__":
    main() 