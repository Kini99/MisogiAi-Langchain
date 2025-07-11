"""
Basic tests for the Intelligent Email Response System.
"""

import pytest
import asyncio
from datetime import datetime

from src.config import get_settings
from src.models.email import Email
from src.models.policy import PolicyCreate, PolicyCategory
from src.services.policy_service import policy_service
from src.services.response_service import response_service
from src.services.cache_service import cache_service


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        id="test_email_123",
        subject="Vacation Request",
        sender="employee@company.com",
        body="I would like to request vacation time for next month. How do I submit a request?",
        recipients=["hr@company.com"]
    )


@pytest.fixture
def sample_policy_data():
    """Create sample policy data for testing."""
    return PolicyCreate(
        title="Test Vacation Policy",
        content="Employees can request vacation through the online portal with 2 weeks notice.",
        category=PolicyCategory.HR,
        tags=["vacation", "time-off", "hr"],
        author="test_user"
    )


@pytest.mark.asyncio
async def test_config_loading():
    """Test that configuration loads correctly."""
    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, 'gmail_client_id')
    assert hasattr(settings, 'redis_url')


@pytest.mark.asyncio
async def test_cache_service():
    """Test cache service basic operations."""
    # Test setting and getting values
    await cache_service.set("test_key", "test_value")
    value = await cache_service.get("test_key")
    assert value == "test_value"
    
    # Test cache existence
    exists = await cache_service.exists("test_key")
    assert exists is True
    
    # Test cache deletion
    await cache_service.delete("test_key")
    value = await cache_service.get("test_key")
    assert value is None


@pytest.mark.asyncio
async def test_policy_service_basic():
    """Test basic policy service operations."""
    # Test adding a policy
    policy_data = PolicyCreate(
        title="Test Policy",
        content="This is a test policy for unit testing.",
        category=PolicyCategory.GENERAL,
        tags=["test"],
        author="test_user"
    )
    
    policy = await policy_service.add_policy(policy_data)
    assert policy is not None
    assert policy.title == "Test Policy"
    assert policy.category == PolicyCategory.GENERAL
    
    # Test getting the policy
    retrieved_policy = await policy_service.get_policy(policy.id)
    assert retrieved_policy is not None
    assert retrieved_policy.title == policy.title
    
    # Test searching policies
    search_results = await policy_service.search_policies("test policy")
    assert len(search_results) > 0
    
    # Clean up
    await policy_service.delete_policy(policy.id)


@pytest.mark.asyncio
async def test_response_service_basic(sample_email):
    """Test basic response generation."""
    response = await response_service.generate_response(sample_email)
    
    assert response is not None
    assert response.email_id == sample_email.id
    assert response.response_subject is not None
    assert response.response_body is not None
    assert 0.0 <= response.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_batch_response_generation(sample_email):
    """Test batch response generation."""
    emails = [sample_email]
    responses = await response_service.batch_generate_responses(emails)
    
    assert len(responses) == 1
    assert responses[0].email_id == sample_email.id


@pytest.mark.asyncio
async def test_policy_search_with_category():
    """Test policy search with category filter."""
    # Add a policy with specific category
    policy_data = PolicyCreate(
        title="IT Support Policy",
        content="IT support is available Monday to Friday 8 AM to 6 PM.",
        category=PolicyCategory.IT,
        tags=["support", "it"],
        author="test_user"
    )
    
    policy = await policy_service.add_policy(policy_data)
    
    # Search with category filter
    results = await policy_service.search_policies(
        query="IT support",
        category=PolicyCategory.IT
    )
    
    assert len(results) > 0
    assert results[0].policy.category == PolicyCategory.IT
    
    # Clean up
    await policy_service.delete_policy(policy.id)


def test_email_model_validation():
    """Test email model validation."""
    email = Email(
        id="test_123",
        subject="Test Subject",
        sender="test@example.com",
        body="Test body",
        recipients=["recipient@example.com"]
    )
    
    assert email.id == "test_123"
    assert email.subject == "Test Subject"
    assert email.sender == "test@example.com"


if __name__ == "__main__":
    pytest.main([__file__]) 