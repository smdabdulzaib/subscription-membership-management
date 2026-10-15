"""
Customer management operations: CRUD, validation, search, filter, and safe deletion.
"""

from datetime import date
from typing import Dict, List, Optional, Tuple
from database import execute_query, fetch_all, fetch_one
from utils import validate_email, validate_phone


def get_all_customers(search_term: Optional[str] = None, status_filter: Optional[str] = None) -> List[Dict]:
    """Retrieve all customers with optional search and status filter."""
    query = """
        SELECT 
            c.customer_id,
            c.name,
            c.email,
            c.phone,
            c.registration_date,
            c.account_status,
            c.created_at,
            COUNT(DISTINCT s.subscription_id) AS total_subscriptions,
            COUNT(DISTINCT CASE WHEN s.status = 'Active' THEN s.subscription_id END) AS active_subscriptions
        FROM customers c
        LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
        WHERE 1=1
    """
    params = []
    if search_term:
        term = f"%{search_term.strip()}%"
        query += " AND (c.name LIKE %s OR c.email LIKE %s OR c.phone LIKE %s)"
        params.extend([term, term, term])

    if status_filter and status_filter != "All":
        query += " AND c.account_status = %s"
        params.append(status_filter)

    query += " GROUP BY c.customer_id ORDER BY c.customer_id DESC"
    return fetch_all(query, tuple(params))


def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """Retrieve single customer by ID."""
    query = "SELECT * FROM customers WHERE customer_id = %s"
    return fetch_one(query, (customer_id,))


def validate_customer_fields(
    name: str, email: str, phone: str, customer_id: Optional[int] = None
) -> Tuple[bool, str]:
    """Validate customer inputs and ensure email uniqueness."""
    name = (name or "").strip()
    email = (email or "").strip()
    phone = (phone or "").strip()

    if not name:
        return False, "Customer Name is required."
    if len(name) < 2:
        return False, "Customer Name must be at least 2 characters long."
    if not validate_email(email):
        return False, f"Invalid email format: '{email}'."
    if not validate_phone(phone):
        return False, f"Invalid phone number: '{phone}'. Must be 7-15 digits."

    # Check for duplicate email
    if customer_id:
        existing = fetch_one(
            "SELECT customer_id FROM customers WHERE email = %s AND customer_id != %s",
            (email, customer_id),
        )
    else:
        existing = fetch_one(
            "SELECT customer_id FROM customers WHERE email = %s",
            (email,),
        )

    if existing:
        return False, f"A customer with email '{email}' already exists."

    return True, ""


def add_customer(
    name: str,
    email: str,
    phone: str,
    registration_date: date,
    account_status: str = "Active",
) -> Tuple[bool, str, Optional[int]]:
    """Add a new customer to the database."""
    is_valid, err_msg = validate_customer_fields(name, email, phone)
    if not is_valid:
        return False, err_msg, None

    query = """
        INSERT INTO customers (name, email, phone, registration_date, account_status)
        VALUES (%s, %s, %s, %s, %s)
    """
    try:
        new_id = execute_query(
            query,
            (name.strip(), email.strip(), phone.strip(), registration_date, account_status),
        )
        return True, "Customer registered successfully!", new_id
    except Exception as e:
        return False, f"Failed to add customer: {str(e)}", None


def update_customer(
    customer_id: int,
    name: str,
    email: str,
    phone: str,
    account_status: str,
) -> Tuple[bool, str]:
    """Update existing customer details."""
    is_valid, err_msg = validate_customer_fields(name, email, phone, customer_id=customer_id)
    if not is_valid:
        return False, err_msg

    query = """
        UPDATE customers
        SET name = %s, email = %s, phone = %s, account_status = %s
        WHERE customer_id = %s
    """
    try:
        execute_query(
            query,
            (name.strip(), email.strip(), phone.strip(), account_status, customer_id),
        )
        return True, "Customer details updated successfully!"
    except Exception as e:
        return False, f"Failed to update customer: {str(e)}"


def delete_customer(customer_id: int) -> Tuple[bool, str]:
    """
    Safely delete or deactivate customer:
    If the customer has related subscription or payment records, soft-delete (set status to 'Inactive')
    to preserve historical and billing data integrity.
    """
    # Check for existing subscriptions
    sub_count = fetch_one(
        "SELECT COUNT(*) as count FROM subscriptions WHERE customer_id = %s",
        (customer_id,),
    )
    has_history = sub_count and sub_count["count"] > 0

    if has_history:
        # Soft delete / deactivate
        execute_query(
            "UPDATE customers SET account_status = 'Inactive' WHERE customer_id = %s",
            (customer_id,),
        )
        return (
            True,
            f"Customer has {sub_count['count']} linked subscriptions. Preserved audit history and marked status as 'Inactive'.",
        )
    else:
        try:
            execute_query("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
            return True, "Customer deleted permanently."
        except Exception as e:
            return False, f"Failed to delete customer: {str(e)}"
