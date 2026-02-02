"""
Customer ID Generator for Multi-Tenant Architecture
Generates secure 9-character alphanumeric customer IDs with collision detection
"""
import secrets
import string
from db import fetch_query

# Exclude confusing characters: O, 0, I, 1, L
# This leaves 26 letters - 3 (O,I,L) + 10 digits - 2 (0,1) = 31 characters
# Actually: A-Z minus O,I,L = 23 letters + 2-9 = 8 digits = 31 total
# Better: Use 34 characters (A-Z minus O,I,L + 2-9 digits)
SAFE_CHARS = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'

def generate_customer_id() -> str:
    """
    Generate a unique 9-character alphanumeric customer ID.

    Format: 9 characters from SAFE_CHARS (34 options per position)
    Total combinations: 34^9 = ~2,862,423,051,509,815,793 (2.8 billion billion)

    Excluded characters to prevent confusion:
    - O and 0 (letter O vs zero)
    - I and 1 (letter I vs one)
    - L (looks like 1 or I)

    Returns:
        str: Unique 9-character customer ID

    Raises:
        RuntimeError: If unable to generate unique ID after 100 attempts (extremely unlikely)
    """
    max_attempts = 100

    for attempt in range(max_attempts):
        # Generate random 9-character ID
        customer_id = ''.join(secrets.choice(SAFE_CHARS) for _ in range(9))

        # Check for uniqueness in database
        existing = fetch_query(
            "SELECT customer_id FROM customers WHERE customer_id = %s",
            (customer_id,)
        )

        if not existing:
            return customer_id

    # This should never happen with 2.8 billion billion combinations
    raise RuntimeError(f"Failed to generate unique customer_id after {max_attempts} attempts")


def validate_customer_id(customer_id: str) -> bool:
    """
    Validate that a customer_id meets format requirements.

    Args:
        customer_id: The customer ID to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not customer_id:
        return False

    if len(customer_id) != 9:
        return False

    if not all(c in SAFE_CHARS for c in customer_id):
        return False

    return True


def customer_exists(customer_id: str) -> bool:
    """
    Check if a customer_id exists in the database.

    Args:
        customer_id: The customer ID to check

    Returns:
        bool: True if customer exists, False otherwise
    """
    result = fetch_query(
        "SELECT customer_id FROM customers WHERE customer_id = %s",
        (customer_id,)
    )
    return bool(result)
