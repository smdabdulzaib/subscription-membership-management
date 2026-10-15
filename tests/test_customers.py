"""
Unit tests for customer validation and operations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import validate_email, validate_phone


def test_valid_email():
    assert validate_email("john.doe@example.com") is True
    assert validate_email("customer+tag@domain.co.in") is True
    assert validate_email("user.name123@sub.domain.org") is True


def test_invalid_email():
    assert validate_email("invalid-email") is False
    assert validate_email("@example.com") is False
    assert validate_email("user@") is False
    assert validate_email("") is False
    assert validate_email(None) is False


def test_valid_phone():
    assert validate_phone("+91 9876543210") is True
    assert validate_phone("9876543210") is True
    assert validate_phone("(123) 456-7890") is True


def test_invalid_phone():
    assert validate_phone("123") is False  # Too short
    assert validate_phone("abcdefghijk") is False
    assert validate_phone("") is False
    assert validate_phone(None) is False
