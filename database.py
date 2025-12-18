"""
Database Operations Layer - SQLite
"""

import sqlite3
from datetime import datetime, date
from typing import List, Optional
from contextlib import contextmanager

from config import DATABASE_PATH
from models import Transaction, TransactionType, Asset, DepreciationRecord


def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Database connection context manager"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize database tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL,
                category TEXT,
                transaction_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                asset_id INTEGER,
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        ''')

        # Assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                original_cost REAL NOT NULL,
                useful_life_months INTEGER NOT NULL,
                purchase_date DATE NOT NULL,
                residual_value REAL DEFAULT 0,
                category TEXT,
                monthly_depreciation REAL NOT NULL,
                accumulated_depreciation REAL DEFAULT 0,
                is_disposed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Depreciation records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS depreciation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                amount REAL NOT NULL,
                accumulated REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets(id)
            )
        ''')

        print("Database initialized successfully!")


# ==================== Transaction Operations ====================

def add_transaction(
    description: str,
    amount: float,
    transaction_type: TransactionType,
    category: str,
    transaction_date: date = None,
    asset_id: int = None
) -> int:
    """Add a transaction record"""
    if transaction_date is None:
        transaction_date = date.today()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (description, amount, transaction_type, category, transaction_date, asset_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (description, amount, transaction_type.value, category, transaction_date.isoformat(), asset_id))
        return cursor.lastrowid


def get_transactions(
    start_date: date = None,
    end_date: date = None,
    transaction_type: TransactionType = None
) -> List[Transaction]:
    """Get transaction records"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM transactions WHERE 1=1"
        params = []

        if start_date:
            query += " AND transaction_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND transaction_date <= ?"
            params.append(end_date.isoformat())
        if transaction_type:
            query += " AND transaction_type = ?"
            params.append(transaction_type.value)

        query += " ORDER BY transaction_date DESC, id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            Transaction(
                id=row['id'],
                description=row['description'],
                amount=row['amount'],
                transaction_type=TransactionType(row['transaction_type']),
                category=row['category'],
                transaction_date=date.fromisoformat(row['transaction_date']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
                asset_id=row['asset_id']
            )
            for row in rows
        ]


# ==================== Asset Operations ====================

def add_asset(
    name: str,
    original_cost: float,
    useful_life_months: int,
    purchase_date: date,
    category: str,
    residual_value: float = 0
) -> int:
    """Add an asset"""
    # Calculate monthly depreciation (straight-line method)
    depreciable_amount = original_cost - residual_value
    monthly_depreciation = depreciable_amount / useful_life_months if useful_life_months > 0 else 0

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assets (name, original_cost, useful_life_months, purchase_date,
                              residual_value, category, monthly_depreciation, accumulated_depreciation)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        ''', (name, original_cost, useful_life_months, purchase_date.isoformat(),
              residual_value, category, monthly_depreciation))
        return cursor.lastrowid


def get_assets(include_disposed: bool = False) -> List[Asset]:
    """Get all assets"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM assets"
        if not include_disposed:
            query += " WHERE is_disposed = 0"
        query += " ORDER BY purchase_date DESC"

        cursor.execute(query)
        rows = cursor.fetchall()

        return [
            Asset(
                id=row['id'],
                name=row['name'],
                original_cost=row['original_cost'],
                useful_life_months=row['useful_life_months'],
                purchase_date=date.fromisoformat(row['purchase_date']),
                residual_value=row['residual_value'],
                category=row['category'],
                monthly_depreciation=row['monthly_depreciation'],
                accumulated_depreciation=row['accumulated_depreciation'],
                is_disposed=bool(row['is_disposed']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
            )
            for row in rows
        ]


def get_asset_by_id(asset_id: int) -> Optional[Asset]:
    """Get asset by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE id = ?", (asset_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return Asset(
            id=row['id'],
            name=row['name'],
            original_cost=row['original_cost'],
            useful_life_months=row['useful_life_months'],
            purchase_date=date.fromisoformat(row['purchase_date']),
            residual_value=row['residual_value'],
            category=row['category'],
            monthly_depreciation=row['monthly_depreciation'],
            accumulated_depreciation=row['accumulated_depreciation'],
            is_disposed=bool(row['is_disposed']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
        )


def update_asset_depreciation(asset_id: int, accumulated: float):
    """Update asset accumulated depreciation"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assets SET accumulated_depreciation = ? WHERE id = ?
        ''', (accumulated, asset_id))


def dispose_asset(asset_id: int):
    """Dispose an asset"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assets SET is_disposed = 1 WHERE id = ?
        ''', (asset_id,))


def delete_transaction(transaction_id: int) -> bool:
    """Delete a transaction record"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Get transaction info, check if there's an associated asset
        cursor.execute("SELECT asset_id FROM transactions WHERE id = ?", (transaction_id,))
        row = cursor.fetchone()
        if not row:
            return False

        asset_id = row['asset_id']

        # Delete transaction
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

        # If there's an associated asset, delete it and related depreciation records
        if asset_id:
            cursor.execute("DELETE FROM depreciation_records WHERE asset_id = ?", (asset_id,))
            cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))

        return True


def delete_asset(asset_id: int) -> bool:
    """Delete an asset and related records"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Delete related depreciation records
        cursor.execute("DELETE FROM depreciation_records WHERE asset_id = ?", (asset_id,))

        # Delete related transactions
        cursor.execute("DELETE FROM transactions WHERE asset_id = ?", (asset_id,))

        # Delete asset
        cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))

        return True


def clear_all_data():
    """Clear all data (for removing sample data)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM depreciation_records")
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM assets")
        return True


def update_transaction(transaction_id: int, description: str = None, amount: float = None, category: str = None) -> bool:
    """Update a transaction record"""
    with get_db() as conn:
        cursor = conn.cursor()

        updates = []
        params = []

        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if amount is not None:
            updates.append("amount = ?")
            params.append(amount)
        if category is not None:
            updates.append("category = ?")
            params.append(category)

        if not updates:
            return False

        params.append(transaction_id)
        query = f"UPDATE transactions SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)

        return cursor.rowcount > 0


# ==================== Depreciation Record Operations ====================

def add_depreciation_record(asset_id: int, period: str, amount: float, accumulated: float) -> int:
    """Add a depreciation record"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO depreciation_records (asset_id, period, amount, accumulated)
            VALUES (?, ?, ?, ?)
        ''', (asset_id, period, amount, accumulated))
        return cursor.lastrowid


def get_depreciation_records(asset_id: int = None, period: str = None) -> List[DepreciationRecord]:
    """Get depreciation records"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM depreciation_records WHERE 1=1"
        params = []

        if asset_id:
            query += " AND asset_id = ?"
            params.append(asset_id)
        if period:
            query += " AND period = ?"
            params.append(period)

        query += " ORDER BY period DESC, id DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [
            DepreciationRecord(
                id=row['id'],
                asset_id=row['asset_id'],
                period=row['period'],
                amount=row['amount'],
                accumulated=row['accumulated'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now()
            )
            for row in rows
        ]


def check_depreciation_exists(asset_id: int, period: str) -> bool:
    """Check if depreciation has been recorded for an asset in a period"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM depreciation_records WHERE asset_id = ? AND period = ?
        ''', (asset_id, period))
        count = cursor.fetchone()[0]
        return count > 0


def run_monthly_depreciation(period: str = None):
    """Run monthly depreciation"""
    if period is None:
        today = date.today()
        period = f"{today.year}-{today.month:02d}"

    assets = get_assets(include_disposed=False)
    depreciation_total = 0

    for asset in assets:
        # Check if already depreciated
        if check_depreciation_exists(asset.id, period):
            continue

        # Check if still needs depreciation (remaining months > 0)
        if asset.remaining_months <= 0:
            continue

        # Calculate depreciation
        new_accumulated = asset.accumulated_depreciation + asset.monthly_depreciation

        # Cannot exceed depreciable amount
        max_depreciation = asset.original_cost - asset.residual_value
        if new_accumulated > max_depreciation:
            new_accumulated = max_depreciation
            depreciation_amount = max_depreciation - asset.accumulated_depreciation
        else:
            depreciation_amount = asset.monthly_depreciation

        if depreciation_amount > 0:
            # Add depreciation record
            add_depreciation_record(asset.id, period, depreciation_amount, new_accumulated)
            # Update asset accumulated depreciation
            update_asset_depreciation(asset.id, new_accumulated)
            depreciation_total += depreciation_amount

    return depreciation_total


if __name__ == "__main__":
    init_database()
