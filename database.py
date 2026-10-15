"""
Database manager for Subscription & Membership Management System.
Handles MySQL connections, queries, schema creation, seeding, and auto-status updates.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error, errorcode
# Lazy-load pandas in fetch_dataframe to prevent DLL blocking on restricted systems

# Load environment variables from .env if present
load_dotenv()

# Global default config (can be updated dynamically at runtime via update_config)
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "subscription_management"),
}


def update_db_config(host=None, port=None, user=None, password=None, database=None):
    """Dynamically update database connection parameters."""
    if host is not None:
        DB_CONFIG["host"] = host
    if port is not None:
        DB_CONFIG["port"] = int(port)
    if user is not None:
        DB_CONFIG["user"] = user
    if password is not None:
        DB_CONFIG["password"] = password
    if database is not None:
        DB_CONFIG["database"] = database


def get_connection(use_database: bool = True):
    """
    Establish and return a MySQL connection.
    If use_database is False, connects to the MySQL server without selecting a DB
    (useful for CREATE DATABASE operations).
    """
    config = {
        "host": DB_CONFIG["host"],
        "port": DB_CONFIG["port"],
        "user": DB_CONFIG["user"],
        "password": DB_CONFIG["password"],
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "autocommit": False,
    }
    if use_database:
        config["database"] = DB_CONFIG["database"]

    try:
        conn = mysql.connector.connect(**config)
        return conn
    except Error as e:
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise ConnectionError(
                f"MySQL Access Denied for user '{DB_CONFIG['user']}'. Please check DB_USER and DB_PASSWORD in Settings or .env."
            ) from e
        elif e.errno == errorcode.ER_BAD_DB_ERROR and use_database:
            raise ConnectionError(
                f"Database '{DB_CONFIG['database']}' does not exist yet. Please use the Settings page to Initialize the Database."
            ) from e
        elif e.errno == errorcode.CR_CONN_HOST_ERROR or e.errno == 2003:
            raise ConnectionError(
                f"Cannot connect to MySQL server at {DB_CONFIG['host']}:{DB_CONFIG['port']}. Ensure the MySQL service is running."
            ) from e
        else:
            raise ConnectionError(f"Database error: {str(e)}") from e


def check_connection() -> Tuple[bool, str]:
    """Test MySQL connection and return (success, message)."""
    try:
        conn = get_connection(use_database=True)
        if conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return True, f"Connected to MySQL {version} (Database: {DB_CONFIG['database']})"
    except Exception as e:
        # Check if server itself is reachable without DB
        try:
            conn_server = get_connection(use_database=False)
            if conn_server.is_connected():
                conn_server.close()
                return False, f"MySQL server reachable, but database '{DB_CONFIG['database']}' is not yet initialized."
        except Exception:
            pass
        return False, str(e)
    return False, "Unknown connection error"


def execute_query(query: str, params: Optional[Tuple] = None, commit: bool = True) -> int:
    """
    Execute an INSERT, UPDATE, or DELETE query with parameterized inputs.
    Returns the lastrowid for INSERT, or rowcount for UPDATE/DELETE.
    """
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        result_id = cursor.lastrowid
        row_count = cursor.rowcount
        if commit:
            conn.commit()
        return result_id if result_id else row_count
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_one(query: str, params: Optional[Tuple] = None) -> Optional[Dict[str, Any]]:
    """Execute a query and fetch a single record as a dictionary."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        row = cursor.fetchone()
        return row
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_all(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
    """Execute a query and fetch all records as a list of dictionaries."""
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        rows = cursor.fetchall()
        return rows or []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def fetch_dataframe(query: str, params: Optional[Tuple] = None):
    """Execute query and return results as a Pandas DataFrame (or list-of-dicts fallback)."""
    conn = None
    try:
        import pandas as pd
        conn = get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        # Fallback to fetch_all if pandas or connection has an issue
        try:
            rows = fetch_all(query, params)
            import pandas as pd
            return pd.DataFrame(rows)
        except Exception:
            # If pandas DLL cannot load on restricted systems, return rows directly
            rows = fetch_all(query, params)
            return rows
    finally:
        if conn:
            conn.close()


def init_database(include_seed: bool = True) -> Tuple[bool, str]:
    """
    Initialize MySQL schema and seed data by executing sql/database.sql.
    Creates the database if it doesn't exist.
    """
    sql_path = Path(__file__).parent / "sql" / "database.sql"
    if not sql_path.exists():
        return False, f"SQL file not found at {sql_path}"

    with open(sql_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split commands by semicolon while respecting strings
    statements = []
    current_stmt = []
    in_delimiter = False
    
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("--") or trimmed.startswith("/*"):
            continue
        current_stmt.append(line)
        if trimmed.endswith(";"):
            statements.append("\n".join(current_stmt))
            current_stmt = []

    conn = None
    cursor = None
    try:
        # First connect without DB to ensure DB exists
        conn = get_connection(use_database=False)
        cursor = conn.cursor()
        
        # Execute create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        cursor.execute(f"USE {DB_CONFIG['database']};")
        
        for stmt in statements:
            stmt_clean = stmt.strip()
            # If not including seed data, skip INSERT statements
            if not include_seed and stmt_clean.upper().startswith("INSERT INTO"):
                continue
            if stmt_clean:
                try:
                    cursor.execute(stmt_clean)
                except Error as e:
                    # Ignore duplicate key warnings during re-seeding
                    if e.errno != 1062 and e.errno != 1050:
                        raise e
                        
        conn.commit()
        return True, "Database initialized and schema created successfully!"
    except Exception as e:
        if conn:
            conn.rollback()
        return False, f"Failed to initialize database: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def auto_update_subscription_statuses():
    """
    Smart status synchronizer:
    Runs automatically to keep subscription statuses accurate based on expiry_date vs current date:
    - If expiry_date < today and status != 'Cancelled' -> 'Expired'
    - If expiry_date >= today and days_remaining <= 7 and status == 'Active' -> 'Expiring Soon'
    - If expiry_date >= today and days_remaining > 7 and status == 'Expiring Soon' -> 'Active'
    """
    try:
        # 1. Update expired subscriptions
        q_expired = """
            UPDATE subscriptions
            SET status = 'Expired'
            WHERE expiry_date < CURDATE()
              AND status NOT IN ('Expired', 'Cancelled');
        """
        execute_query(q_expired)

        # 2. Update expiring soon subscriptions (within 7 days)
        q_expiring_soon = """
            UPDATE subscriptions
            SET status = 'Expiring Soon'
            WHERE expiry_date >= CURDATE()
              AND DATEDIFF(expiry_date, CURDATE()) <= 7
              AND status = 'Active';
        """
        execute_query(q_expiring_soon)

        # 3. Update active subscriptions that were pushed beyond 7 days (e.g. after renewal)
        q_reactivated = """
            UPDATE subscriptions
            SET status = 'Active'
            WHERE expiry_date >= CURDATE()
              AND DATEDIFF(expiry_date, CURDATE()) > 7
              AND status = 'Expiring Soon';
        """
        execute_query(q_reactivated)
    except Exception:
        # Fail silently if DB is not yet initialized so app doesn't crash on boot
        pass


if __name__ == "__main__":
    print(f"Testing MySQL connection to {DB_CONFIG['host']}:{DB_CONFIG['port']} with user '{DB_CONFIG['user']}'...")
    connected, msg = check_connection()
    if connected:
        print(f"[SUCCESS] {msg}")
        print("Initializing schema and seeding demo data...")
        ok, init_msg = init_database(include_seed=True)
        print(f"[{'SUCCESS' if ok else 'ERROR'}] {init_msg}")
    else:
        print(f"[WARNING] {msg}")
        print("Please check your .env file or use the web Settings interface to configure MySQL credentials.")
