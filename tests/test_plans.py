"""
Unit tests for membership plans and pricing validation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from plans import validate_plan_fields
from utils import validate_positive_amount


def test_positive_amount():
    assert validate_positive_amount(499.00) is True
    assert validate_positive_amount(0) is True
    assert validate_positive_amount("999.50") is True
    assert validate_positive_amount(-10) is False
    assert validate_positive_amount("invalid") is False


def test_validate_plan_fields_valid():
    is_valid, msg = validate_plan_fields("Premium Annual", 1999.0, 365)
    assert is_valid is True
    assert msg == ""


def test_validate_plan_fields_invalid_name():
    is_valid, msg = validate_plan_fields("", 1999.0, 365)
    assert is_valid is False
    assert "Plan Name cannot be empty" in msg


def test_validate_plan_fields_invalid_price():
    is_valid, msg = validate_plan_fields("Basic", -50.0, 30)
    assert is_valid is False
    assert "non-negative" in msg


def test_validate_plan_fields_invalid_duration():
    is_valid, msg = validate_plan_fields("Basic", 499.0, 0)
    assert is_valid is False
    assert "Duration must be at least 1 day" in msg
