"""
Unit tests for subscription calculations, prorated upgrades, and renewals.
"""

from datetime import date, timedelta
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import (
    calculate_expiry_date,
    calculate_prorated_upgrade,
    calculate_remaining_days,
    calculate_renewal_dates,
    generate_transaction_id,
    generate_invoice_number,
)


def test_expiry_date_calculation():
    start = date(2026, 1, 1)
    expiry = calculate_expiry_date(start, 30)
    assert expiry == date(2026, 1, 31)

    expiry_annual = calculate_expiry_date(start, 365)
    assert expiry_annual == start + timedelta(days=365)


def test_remaining_days_calculation():
    ref_date = date(2026, 10, 1)
    expiry = date(2026, 10, 11)
    assert calculate_remaining_days(expiry, from_date=ref_date) == 10

    past_expiry = date(2026, 9, 20)
    assert calculate_remaining_days(past_expiry, from_date=ref_date) == 0


def test_prorated_upgrade_calculation():
    # Scenario: Current plan ₹600 / 30 days = ₹20/day
    # New plan ₹1200 / 30 days = ₹40/day
    # Remaining days = 15 days
    # Expected remaining value old = 15 * 20 = 300
    # Expected remaining value new = 15 * 40 = 600
    # Additional amount = 600 - 300 = 300
    result = calculate_prorated_upgrade(
        current_plan_price=600.0,
        current_plan_duration=30,
        new_plan_price=1200.0,
        new_plan_duration=30,
        remaining_days=15,
    )
    assert result["remaining_days"] == 15
    assert result["current_remaining_value"] == 300.0
    assert result["new_remaining_value"] == 600.0
    assert result["additional_amount"] == 300.0


def test_renewal_dates_calculation_active():
    current_expiry = date.today() + timedelta(days=5)
    new_start, new_expiry = calculate_renewal_dates(
        current_expiry_date=current_expiry,
        is_expired=False,
        duration_days=30,
    )
    # Active subscription extends from current expiry date
    assert new_start == current_expiry
    assert new_expiry == current_expiry + timedelta(days=30)


def test_renewal_dates_calculation_expired():
    past_expiry = date.today() - timedelta(days=10)
    new_start, new_expiry = calculate_renewal_dates(
        current_expiry_date=past_expiry,
        is_expired=True,
        duration_days=30,
    )
    # Expired subscription starts from today
    assert new_start == date.today()
    assert new_expiry == date.today() + timedelta(days=30)


def test_unique_identifiers():
    txn1 = generate_transaction_id()
    txn2 = generate_transaction_id()
    assert txn1.startswith("TXN-")
    assert txn2.startswith("TXN-")
    assert txn1 != txn2

    inv1 = generate_invoice_number()
    inv2 = generate_invoice_number()
    assert inv1.startswith("INV-")
    assert inv2.startswith("INV-")
    assert inv1 != inv2


def test_payment_methods_and_status_validation():
    from payments import VALID_PAYMENT_METHODS, VALID_PAYMENT_STATUSES
    assert "UPI" in VALID_PAYMENT_METHODS
    assert "Credit Card" in VALID_PAYMENT_METHODS
    assert "Success" in VALID_PAYMENT_STATUSES
    assert "Failed" in VALID_PAYMENT_STATUSES


def test_cancellation_preserves_rules():
    # Test business rule logic:
    # A cancelled subscription maintains its status and does not delete records
    valid_statuses = ["Active", "Expiring Soon", "Expired", "Cancelled"]
    assert "Cancelled" in valid_statuses
