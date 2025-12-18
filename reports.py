"""
Report Generation Module

Provides two sets of reports:
1. Cash Flow Report (Cash Basis) - Actual money spent
2. Accrual Report (Accrual Basis) - True living cost
3. Balance Sheet - What your belongings are worth
4. Daily Living Cost Statistics
"""

from datetime import date, timedelta
from typing import List, Optional
from collections import defaultdict

from database import (
    get_transactions, get_assets, get_depreciation_records,
    run_monthly_depreciation
)
from models import TransactionType


def get_cash_flow_report(
    start_date: date = None,
    end_date: date = None,
    period: str = "month"
) -> dict:
    """
    Cash Flow Report (Cash Basis)

    Statistics of actual cash income and expenditure

    Args:
        start_date: Start date
        end_date: End date
        period: Period type ("day", "month", "year")

    Returns:
        Cash flow report data
    """
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        if period == "month":
            start_date = date(end_date.year, end_date.month, 1)
        elif period == "year":
            start_date = date(end_date.year, 1, 1)
        else:
            start_date = end_date

    transactions = get_transactions(start_date=start_date, end_date=end_date)

    # Statistics
    total_income = 0
    total_expense = 0  # Operating expenses
    total_capital = 0  # Capital expenditures

    income_by_category = defaultdict(float)
    expense_by_category = defaultdict(float)

    for t in transactions:
        if t.transaction_type == TransactionType.INCOME:
            total_income += t.amount
            income_by_category[t.category] += t.amount
        elif t.transaction_type == TransactionType.EXPENSE:
            total_expense += t.amount
            expense_by_category[t.category] += t.amount
        elif t.transaction_type == TransactionType.CAPITAL:
            total_capital += t.amount
            expense_by_category[t.category] += t.amount

    total_outflow = total_expense + total_capital
    net_cash_flow = total_income - total_outflow

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "summary": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_capital": round(total_capital, 2),
            "total_outflow": round(total_outflow, 2),
            "net_cash_flow": round(net_cash_flow, 2)
        },
        "income_by_category": dict(income_by_category),
        "expense_by_category": dict(expense_by_category),
        "transaction_count": len(transactions)
    }


def get_accrual_report(
    year: int = None,
    month: int = None
) -> dict:
    """
    Accrual Basis Report

    Statistics of "true living cost":
    - Operating expenses: Fully recognized in current period
    - Capital expenditures: Recognized through depreciation

    Args:
        year: Year
        month: Month

    Returns:
        Accrual report data
    """
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    period = f"{year}-{month:02d}"

    # Run depreciation first (ensure current period depreciation is calculated)
    run_monthly_depreciation(period)

    # Get current month transactions
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    transactions = get_transactions(start_date=start_date, end_date=end_date)

    # Statistics for income and operating expenses
    total_income = 0
    total_expense = 0  # Operating expenses (recognized in current period)
    expense_by_category = defaultdict(float)

    for t in transactions:
        if t.transaction_type == TransactionType.INCOME:
            total_income += t.amount
        elif t.transaction_type == TransactionType.EXPENSE:
            total_expense += t.amount
            expense_by_category[t.category] += t.amount

    # Get current period depreciation
    depreciation_records = get_depreciation_records(period=period)
    total_depreciation = sum(r.amount for r in depreciation_records)

    # Depreciation by asset category
    assets = {a.id: a for a in get_assets(include_disposed=True)}
    depreciation_by_category = defaultdict(float)
    for r in depreciation_records:
        if r.asset_id in assets:
            category = assets[r.asset_id].category
            depreciation_by_category[category] += r.amount

    # True living cost = Operating expenses + Depreciation
    true_cost = total_expense + total_depreciation

    # Calculate daily cost
    days_in_month = (end_date - start_date).days + 1
    daily_cost = true_cost / days_in_month if days_in_month > 0 else 0

    return {
        "period": period,
        "summary": {
            "total_income": round(total_income, 2),
            "total_expense": round(total_expense, 2),
            "total_depreciation": round(total_depreciation, 2),
            "true_living_cost": round(true_cost, 2),
            "daily_cost": round(daily_cost, 2),
            "net_result": round(total_income - true_cost, 2)
        },
        "expense_by_category": dict(expense_by_category),
        "depreciation_by_category": dict(depreciation_by_category),
        "depreciation_count": len(depreciation_records)
    }


def get_balance_sheet() -> dict:
    """
    Balance Sheet

    Statistics of the "book value" of all your belongings

    Returns:
        Balance sheet data
    """
    assets = get_assets(include_disposed=False)

    total_original_cost = 0
    total_accumulated_depreciation = 0
    total_current_value = 0

    assets_by_category = defaultdict(list)

    for asset in assets:
        total_original_cost += asset.original_cost
        total_accumulated_depreciation += asset.accumulated_depreciation
        total_current_value += asset.current_value

        assets_by_category[asset.category].append({
            "id": asset.id,
            "name": asset.name,
            "original_cost": round(asset.original_cost, 2),
            "accumulated_depreciation": round(asset.accumulated_depreciation, 2),
            "current_value": round(asset.current_value, 2),
            "purchase_date": asset.purchase_date.isoformat(),
            "remaining_months": asset.remaining_months
        })

    # Summary by category
    summary_by_category = {}
    for category, items in assets_by_category.items():
        category_original = sum(i["original_cost"] for i in items)
        category_current = sum(i["current_value"] for i in items)
        summary_by_category[category] = {
            "original_cost": round(category_original, 2),
            "current_value": round(category_current, 2),
            "item_count": len(items)
        }

    return {
        "date": date.today().isoformat(),
        "summary": {
            "total_original_cost": round(total_original_cost, 2),
            "total_accumulated_depreciation": round(total_accumulated_depreciation, 2),
            "total_current_value": round(total_current_value, 2),
            "asset_count": len(assets)
        },
        "by_category": summary_by_category,
        "assets_detail": dict(assets_by_category)
    }


def get_daily_living_cost(days: int = 30) -> dict:
    """
    Calculate daily living cost

    Args:
        days: Number of days to analyze

    Returns:
        Daily living cost statistics
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    # Get transactions in the period
    transactions = get_transactions(start_date=start_date, end_date=end_date)

    # Statistics for operating expenses
    total_expense = sum(
        t.amount for t in transactions
        if t.transaction_type == TransactionType.EXPENSE
    )

    # Get monthly depreciation for all assets (daily allocation)
    assets = get_assets(include_disposed=False)
    daily_depreciation = sum(a.monthly_depreciation for a in assets) / 30

    # Daily average operating expenses
    daily_expense = total_expense / days if days > 0 else 0

    # True daily living cost
    true_daily_cost = daily_expense + daily_depreciation

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "daily_expense": round(daily_expense, 2),
        "daily_depreciation": round(daily_depreciation, 2),
        "true_daily_cost": round(true_daily_cost, 2),
        "monthly_estimate": round(true_daily_cost * 30, 2),
        "yearly_estimate": round(true_daily_cost * 365, 2)
    }


def compare_reports(year: int = None, month: int = None) -> dict:
    """
    Compare Cash Basis and Accrual Basis

    Args:
        year: Year
        month: Month

    Returns:
        Comparison report
    """
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    end_date = end_date - timedelta(days=1)

    cash_flow = get_cash_flow_report(start_date=start_date, end_date=end_date)
    accrual = get_accrual_report(year=year, month=month)

    # Calculate difference
    cash_outflow = cash_flow["summary"]["total_outflow"]
    accrual_cost = accrual["summary"]["true_living_cost"]
    difference = cash_outflow - accrual_cost

    return {
        "period": f"{year}-{month:02d}",
        "cash_flow": {
            "total_outflow": cash_flow["summary"]["total_outflow"],
            "description": "Actual money spent (including big purchases)"
        },
        "accrual": {
            "true_living_cost": accrual["summary"]["true_living_cost"],
            "description": "True living cost (big items spread monthly)"
        },
        "difference": {
            "amount": round(difference, 2),
            "explanation": (
                f"This month's actual spending is ${abs(round(difference, 2))} {'more' if difference > 0 else 'less'} than true cost. "
                + ("This is because you made big purchases this month, and their cost will be spread over the coming years."
                   if difference > 0 else
                   "This means no major capital expenditures this month, mostly daily expenses.")
            )
        }
    }


def print_monthly_summary(year: int = None, month: int = None):
    """
    Print monthly summary report
    """
    if year is None:
        year = date.today().year
    if month is None:
        month = date.today().month

    print(f"\n{'='*60}")
    print(f"Financial Report - {year}/{month}")
    print(f"{'='*60}")

    # Cash flow
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    cash = get_cash_flow_report(start_date=start_date, end_date=end_date)
    print(f"\nCash Flow (Cash Basis)")
    print(f"   Income: ${cash['summary']['total_income']:,.2f}")
    print(f"   Expenses: ${cash['summary']['total_outflow']:,.2f}")
    print(f"      - Daily expenses: ${cash['summary']['total_expense']:,.2f}")
    print(f"      - Big purchases: ${cash['summary']['total_capital']:,.2f}")
    print(f"   Net Cash Flow: ${cash['summary']['net_cash_flow']:,.2f}")

    # Accrual
    accrual = get_accrual_report(year=year, month=month)
    print(f"\nTrue Cost (Accrual Basis)")
    print(f"   Daily expenses: ${accrual['summary']['total_expense']:,.2f}")
    print(f"   Depreciation: ${accrual['summary']['total_depreciation']:,.2f}")
    print(f"   True Living Cost: ${accrual['summary']['true_living_cost']:,.2f}")
    print(f"   Daily Cost: ${accrual['summary']['daily_cost']:,.2f}")

    # Assets
    balance = get_balance_sheet()
    print(f"\nAssets")
    print(f"   Asset Count: {balance['summary']['asset_count']} items")
    print(f"   Original Value: ${balance['summary']['total_original_cost']:,.2f}")
    print(f"   Current Value: ${balance['summary']['total_current_value']:,.2f}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    print_monthly_summary()
