"""
Core Accounting Functions

Integrates AI analysis and database operations for complete accounting workflow
"""

from datetime import date
from typing import Optional

from database import (
    init_database, add_transaction, add_asset, get_transactions,
    get_assets, run_monthly_depreciation, get_asset_by_id
)
from models import TransactionType, AIAnalysisResult
from ai_service import analyze_expense, estimate_purchase_impact


def record_expense(
    description: str,
    amount: float,
    transaction_date: date = None,
    use_ai: bool = True
) -> dict:
    """
    Record an expense

    Args:
        description: Expense description (e.g., "bought a wok")
        amount: Amount
        transaction_date: Transaction date (defaults to today)
        use_ai: Whether to use AI analysis (default True)

    Returns:
        Recording result
    """
    if transaction_date is None:
        transaction_date = date.today()

    # Use AI analysis
    if use_ai:
        analysis = analyze_expense(description, amount)
    else:
        # Without AI, default to operating expense
        analysis = AIAnalysisResult(
            is_capital=False,
            category="Other",
            item_name=description,
            useful_life_years=0,
            reasoning="AI analysis not used"
        )

    result = {
        "description": description,
        "amount": amount,
        "date": transaction_date.isoformat(),
        "analysis": {
            "is_capital": analysis.is_capital,
            "category": analysis.category,
            "item_name": analysis.item_name,
            "useful_life_years": analysis.useful_life_years,
            "reasoning": analysis.reasoning
        }
    }

    if analysis.is_capital:
        # Capital expenditure: create asset and record transaction
        useful_life_months = int(analysis.useful_life_years * 12)

        asset_id = add_asset(
            name=analysis.item_name,
            original_cost=amount,
            useful_life_months=useful_life_months,
            purchase_date=transaction_date,
            category=analysis.category
        )

        transaction_id = add_transaction(
            description=description,
            amount=amount,
            transaction_type=TransactionType.CAPITAL,
            category=analysis.category,
            transaction_date=transaction_date,
            asset_id=asset_id
        )

        # Calculate cost impact
        impact = estimate_purchase_impact(amount, analysis.useful_life_years)

        result["transaction_id"] = transaction_id
        result["asset_id"] = asset_id
        result["impact"] = impact
        result["message"] = (
            f"Recorded capital expenditure: {analysis.item_name}\n"
            f"Original cost: ${amount}, Useful life: {analysis.useful_life_years} years\n"
            f"Monthly cost: ${impact['monthly_cost']}, Daily cost: ${impact['daily_cost']}"
        )

    else:
        # Operating expense: record transaction directly
        transaction_id = add_transaction(
            description=description,
            amount=amount,
            transaction_type=TransactionType.EXPENSE,
            category=analysis.category,
            transaction_date=transaction_date
        )

        result["transaction_id"] = transaction_id
        result["message"] = f"Recorded operating expense: {description}, Amount: ${amount}"

    return result


def record_income(
    description: str,
    amount: float,
    category: str = "Income",
    transaction_date: date = None
) -> dict:
    """
    Record income

    Args:
        description: Income description
        amount: Amount
        category: Category
        transaction_date: Date

    Returns:
        Recording result
    """
    if transaction_date is None:
        transaction_date = date.today()

    transaction_id = add_transaction(
        description=description,
        amount=amount,
        transaction_type=TransactionType.INCOME,
        category=category,
        transaction_date=transaction_date
    )

    return {
        "transaction_id": transaction_id,
        "description": description,
        "amount": amount,
        "category": category,
        "date": transaction_date.isoformat(),
        "message": f"Recorded income: {description}, Amount: ${amount}"
    }


def record_capital_expense_manual(
    description: str,
    amount: float,
    useful_life_years: float,
    category: str = "Other",
    transaction_date: date = None
) -> dict:
    """
    Manually record capital expenditure (without AI)

    Args:
        description: Description
        amount: Amount
        useful_life_years: Useful life
        category: Category
        transaction_date: Date

    Returns:
        Recording result
    """
    if transaction_date is None:
        transaction_date = date.today()

    useful_life_months = int(useful_life_years * 12)

    asset_id = add_asset(
        name=description,
        original_cost=amount,
        useful_life_months=useful_life_months,
        purchase_date=transaction_date,
        category=category
    )

    transaction_id = add_transaction(
        description=description,
        amount=amount,
        transaction_type=TransactionType.CAPITAL,
        category=category,
        transaction_date=transaction_date,
        asset_id=asset_id
    )

    impact = estimate_purchase_impact(amount, useful_life_years)

    return {
        "transaction_id": transaction_id,
        "asset_id": asset_id,
        "description": description,
        "amount": amount,
        "useful_life_years": useful_life_years,
        "category": category,
        "date": transaction_date.isoformat(),
        "impact": impact,
        "message": (
            f"Recorded capital expenditure: {description}\n"
            f"Original cost: ${amount}, Useful life: {useful_life_years} years\n"
            f"Monthly cost: ${impact['monthly_cost']}"
        )
    }


def get_asset_details(asset_id: int) -> Optional[dict]:
    """
    Get asset details

    Returns complete asset information including:
    - Basic info
    - Depreciation status
    - Remaining value
    """
    asset = get_asset_by_id(asset_id)
    if not asset:
        return None

    return {
        "id": asset.id,
        "name": asset.name,
        "category": asset.category,
        "original_cost": asset.original_cost,
        "purchase_date": asset.purchase_date.isoformat(),
        "useful_life_months": asset.useful_life_months,
        "useful_life_years": asset.useful_life_months / 12,
        "monthly_depreciation": round(asset.monthly_depreciation, 2),
        "accumulated_depreciation": round(asset.accumulated_depreciation, 2),
        "current_value": round(asset.current_value, 2),
        "remaining_months": asset.remaining_months,
        "depreciation_progress": round(
            asset.accumulated_depreciation / (asset.original_cost - asset.residual_value) * 100
            if asset.original_cost > asset.residual_value else 100,
            1
        ),
        "is_disposed": asset.is_disposed
    }


def process_monthly_depreciation(period: str = None) -> dict:
    """
    Process monthly depreciation

    Args:
        period: Period (e.g., "2024-01"), defaults to current month

    Returns:
        Processing result
    """
    if period is None:
        today = date.today()
        period = f"{today.year}-{today.month:02d}"

    total = run_monthly_depreciation(period)

    return {
        "period": period,
        "total_depreciation": round(total, 2),
        "message": f"{period} monthly depreciation completed, Total: ${round(total, 2)}"
    }


if __name__ == "__main__":
    # Initialize database
    init_database()

    # Test accounting
    print("=" * 50)
    print("Testing Accounting Functions")
    print("=" * 50)

    # Test operating expense
    result = record_expense("lunch at restaurant", 28)
    print(f"\n{result['message']}")

    # Test capital expenditure
    result = record_expense("bought a new wok", 299)
    print(f"\n{result['message']}")

    # Test income
    result = record_income("December salary", 15000)
    print(f"\n{result['message']}")
