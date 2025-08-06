import uuid
import re
from typing import Optional

def validate_uuid(uuid_string: str) -> bool:
    """
    Validate if a string is a valid UUID format.
    
    Args:
        uuid_string: String to validate
        
    Returns:
        bool: True if valid UUID, False otherwise
    """
    try:
        # Try to create UUID object - will raise ValueError if invalid
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False

def is_valid_user_id(user_id: str) -> bool:
    """
    Validate if a user_id is in the correct UUID format.
    
    Args:
        user_id: User ID string to validate
        
    Returns:
        bool: True if valid format, False otherwise
    """
    if not user_id or not isinstance(user_id, str):
        return False
    
    # Check if it's a valid UUID
    return validate_uuid(user_id.strip())

def sanitize_user_id(user_id: str) -> Optional[str]:
    """
    Sanitize and validate user ID input.
    
    Args:
        user_id: Raw user ID input
        
    Returns:
        str: Cleaned user ID if valid, None if invalid
    """
    if not user_id:
        return None
        
    cleaned_id = user_id.strip()
    
    if is_valid_user_id(cleaned_id):
        return cleaned_id
    
    return None
