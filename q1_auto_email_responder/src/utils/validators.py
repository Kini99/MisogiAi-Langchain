"""
Validation utility functions for the Intelligent Email Response System.
"""

import re
from typing import List, Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not email:
        return False, "Email address is required"
    
    if not re.match(pattern, email):
        return False, "Invalid email address format"
    
    return True, "Valid email address"


def validate_policy_content(content: str) -> Tuple[bool, str]:
    """Validate policy content."""
    if not content:
        return False, "Policy content is required"
    
    if len(content.strip()) < 10:
        return False, "Policy content must be at least 10 characters long"
    
    if len(content) > 10000:
        return False, "Policy content must be less than 10,000 characters"
    
    return True, "Valid policy content"


def validate_policy_title(title: str) -> Tuple[bool, str]:
    """Validate policy title."""
    if not title:
        return False, "Policy title is required"
    
    if len(title.strip()) < 3:
        return False, "Policy title must be at least 3 characters long"
    
    if len(title) > 200:
        return False, "Policy title must be less than 200 characters"
    
    return True, "Valid policy title"


def validate_email_subject(subject: str) -> Tuple[bool, str]:
    """Validate email subject."""
    if not subject:
        return False, "Email subject is required"
    
    if len(subject.strip()) < 1:
        return False, "Email subject cannot be empty"
    
    if len(subject) > 500:
        return False, "Email subject must be less than 500 characters"
    
    return True, "Valid email subject"


def validate_email_body(body: str) -> Tuple[bool, str]:
    """Validate email body."""
    if not body:
        return False, "Email body is required"
    
    if len(body.strip()) < 1:
        return False, "Email body cannot be empty"
    
    if len(body) > 50000:
        return False, "Email body must be less than 50,000 characters"
    
    return True, "Valid email body"


def sanitize_text(text: str) -> str:
    """Sanitize text by removing potentially harmful characters."""
    if not text:
        return ""
    
    # Remove null bytes and control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text."""
    if not text:
        return []
    
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Split into words
    words = text.split()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Filter out stop words and short words
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequency
    word_count = {}
    for word in keywords:
        word_count[word] = word_count.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    
    return [word for word, count in sorted_keywords[:max_keywords]] 