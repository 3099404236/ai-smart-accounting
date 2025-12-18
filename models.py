"""
Data Model Definitions

Core Concepts:
1. Transaction - Records each actual income/expense
2. Asset - Items that need depreciation
3. Depreciation Record - Monthly depreciation entries
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from enum import Enum


class TransactionType(Enum):
    """Transaction Types"""
    INCOME = "income"           # Income
    EXPENSE = "expense"         # Operating expense (recognized immediately)
    CAPITAL = "capital"         # Capital expenditure (needs depreciation)


@dataclass
class Transaction:
    """Transaction Record"""
    id: Optional[int]
    description: str            # Description (e.g., "bought a wok")
    amount: float               # Amount
    transaction_type: TransactionType  # Type
    category: str               # Category (AI identified)
    transaction_date: date      # Transaction date
    created_at: datetime        # Creation time
    asset_id: Optional[int] = None  # Associated asset ID (for capital expenses)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "transaction_type": self.transaction_type.value,
            "category": self.category,
            "transaction_date": self.transaction_date.isoformat(),
            "created_at": self.created_at.isoformat(),
            "asset_id": self.asset_id
        }


@dataclass
class Asset:
    """Asset (items that need depreciation)"""
    id: Optional[int]
    name: str                   # Asset name
    original_cost: float        # Original cost
    useful_life_months: int     # Useful life (months)
    purchase_date: date         # Purchase date
    residual_value: float       # Residual value (usually 0)
    category: str               # Category
    monthly_depreciation: float # Monthly depreciation
    accumulated_depreciation: float  # Accumulated depreciation
    is_disposed: bool           # Whether disposed
    created_at: datetime

    @property
    def current_value(self) -> float:
        """Current book value"""
        return max(0, self.original_cost - self.accumulated_depreciation)

    @property
    def remaining_months(self) -> int:
        """Remaining depreciation months"""
        today = date.today()
        months_passed = (today.year - self.purchase_date.year) * 12 + (today.month - self.purchase_date.month)
        return max(0, self.useful_life_months - months_passed)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "original_cost": self.original_cost,
            "useful_life_months": self.useful_life_months,
            "purchase_date": self.purchase_date.isoformat(),
            "residual_value": self.residual_value,
            "category": self.category,
            "monthly_depreciation": self.monthly_depreciation,
            "accumulated_depreciation": self.accumulated_depreciation,
            "current_value": self.current_value,
            "remaining_months": self.remaining_months,
            "is_disposed": self.is_disposed
        }


@dataclass
class DepreciationRecord:
    """Depreciation Record (monthly)"""
    id: Optional[int]
    asset_id: int               # Associated asset
    period: str                 # Period (e.g., "2024-01")
    amount: float               # Depreciation for this period
    accumulated: float          # Accumulated depreciation to date
    created_at: datetime


@dataclass
class AIAnalysisResult:
    """AI Analysis Result"""
    is_capital: bool            # Is capital expenditure
    category: str               # Category
    item_name: str              # Item name
    useful_life_years: float    # Suggested useful life (years)
    reasoning: str              # AI's reasoning
