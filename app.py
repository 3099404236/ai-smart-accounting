"""
AI Smart Accounting - Web Version
Flask Backend API
"""

from flask import Flask, request, jsonify, render_template
from datetime import date, datetime

from database import init_database, get_transactions, get_assets
from accounting import record_expense, record_income, record_capital_expense_manual, get_asset_details, process_monthly_depreciation
from reports import (
    get_cash_flow_report, get_accrual_report, get_balance_sheet,
    get_daily_living_cost, compare_reports
)
from models import TransactionType

app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize database
init_database()


# ==================== Page Routes ====================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


# ==================== API Routes ====================

@app.route('/api/expense', methods=['POST'])
def api_record_expense():
    """Record expense"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        amount = float(data.get('amount', 0))
        date_str = data.get('date')
        use_ai = data.get('use_ai', True)

        if not description:
            return jsonify({'success': False, 'error': 'Description cannot be empty'}), 400
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be greater than 0'}), 400

        transaction_date = None
        if date_str:
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        result = record_expense(description, amount, transaction_date, use_ai)
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/income', methods=['POST'])
def api_record_income():
    """Record income"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        amount = float(data.get('amount', 0))
        category = data.get('category', 'Income')
        date_str = data.get('date')

        if not description:
            return jsonify({'success': False, 'error': 'Description cannot be empty'}), 400
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be greater than 0'}), 400

        transaction_date = None
        if date_str:
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        result = record_income(description, amount, category, transaction_date)
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/capital', methods=['POST'])
def api_record_capital():
    """Manually record capital expenditure"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        amount = float(data.get('amount', 0))
        useful_life_years = float(data.get('useful_life_years', 3))
        category = data.get('category', 'Other')
        date_str = data.get('date')

        if not description:
            return jsonify({'success': False, 'error': 'Description cannot be empty'}), 400
        if amount <= 0:
            return jsonify({'success': False, 'error': 'Amount must be greater than 0'}), 400

        transaction_date = None
        if date_str:
            transaction_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        result = record_capital_expense_manual(description, amount, useful_life_years, category, transaction_date)
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transactions', methods=['GET'])
def api_get_transactions():
    """Get transaction records"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = None
        end_date = None

        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        transactions = get_transactions(start_date=start_date, end_date=end_date)
        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in transactions]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets', methods=['GET'])
def api_get_assets():
    """Get asset list"""
    try:
        assets = get_assets()
        return jsonify({
            'success': True,
            'data': [a.to_dict() for a in assets]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/asset/<int:asset_id>', methods=['GET'])
def api_get_asset(asset_id):
    """Get asset details"""
    try:
        asset = get_asset_details(asset_id)
        if not asset:
            return jsonify({'success': False, 'error': 'Asset not found'}), 404
        return jsonify({'success': True, 'data': asset})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report/cash-flow', methods=['GET'])
def api_cash_flow_report():
    """Cash flow report"""
    try:
        year = request.args.get('year', type=int) or date.today().year
        month = request.args.get('month', type=int) or date.today().month

        from datetime import timedelta
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        report = get_cash_flow_report(start_date=start_date, end_date=end_date)
        return jsonify({'success': True, 'data': report})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report/accrual', methods=['GET'])
def api_accrual_report():
    """Accrual basis report"""
    try:
        year = request.args.get('year', type=int) or date.today().year
        month = request.args.get('month', type=int) or date.today().month

        report = get_accrual_report(year=year, month=month)
        return jsonify({'success': True, 'data': report})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report/balance', methods=['GET'])
def api_balance_sheet():
    """Balance sheet"""
    try:
        report = get_balance_sheet()
        return jsonify({'success': True, 'data': report})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report/daily-cost', methods=['GET'])
def api_daily_cost():
    """Daily living cost"""
    try:
        days = request.args.get('days', type=int) or 30
        report = get_daily_living_cost(days=days)
        return jsonify({'success': True, 'data': report})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report/compare', methods=['GET'])
def api_compare_reports():
    """Compare reports"""
    try:
        year = request.args.get('year', type=int) or date.today().year
        month = request.args.get('month', type=int) or date.today().month

        report = compare_reports(year=year, month=month)
        return jsonify({'success': True, 'data': report})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/depreciation', methods=['POST'])
def api_run_depreciation():
    """Run monthly depreciation"""
    try:
        data = request.get_json() or {}
        period = data.get('period')

        result = process_monthly_depreciation(period)
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("AI Smart Accounting - Web Version")
    print("Visit: http://127.0.0.1:5000")
    print("=" * 50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
