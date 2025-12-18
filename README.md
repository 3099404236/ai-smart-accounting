# AI Smart Accounting - Accrual Basis Personal Finance

An AI-powered personal accounting app using **accrual basis accounting** to help you see your "true living cost".

## Why This?

Traditional personal finance uses **cash basis** accounting - you record what you spend when you spend it. The problem: if you buy an $8,000 computer this month, your books show "I spent way too much this month!" But you'll use that computer for 4 years, so the real monthly cost is only $167.

**Accrual basis** shows you more accurate numbers:
- Big purchases are spread over their useful life
- Your monthly "true living cost" is smoother
- You know exactly how much you need to maintain your lifestyle

## Features

- **AI-Powered Recognition**: Enter "bought a wok for $300", AI automatically determines it's a capital expenditure, categorizes it as cookware, and estimates 9-year useful life
- **Dual Reports**: Cash flow report vs Accrual basis report
- **Asset Management**: What are your belongings worth? How much have they depreciated?
- **Daily Cost**: How much do you need per day to maintain your current lifestyle?

## Tech Stack

- **Backend**: Python + Flask
- **Frontend**: HTML + CSS + JavaScript
- **Database**: SQLite
- **AI**: Xiaomi MiMo API (Anthropic format compatible)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `config.py` and set your Xiaomi MiMo API key:

```python
XIAOMI_API_KEY = "your-api-key"
```

### 3. Run the App

```bash
python app.py
```

Visit http://127.0.0.1:5000

## Project Structure

```
├── app.py              # Flask web server
├── templates/
│   └── index.html      # Frontend page
├── config.py           # Configuration
├── models.py           # Data models
├── database.py         # SQLite database operations
├── ai_service.py       # AI service (Xiaomi MiMo API)
├── accounting.py       # Core accounting logic
├── reports.py          # Report generation
└── requirements.txt    # Dependencies
```

## Usage Examples

### Recording Expenses

Enter expense description and amount, AI will analyze automatically:

| Input | AI Analysis | Processing |
|-------|-------------|------------|
| bought a wok $300 | Capital, Cookware, 9 years | Monthly cost $2.77 |
| lunch today $35 | Operating, Food | Recognized in full |
| bought iPhone 16 $8999 | Capital, Phone, 3 years | Monthly cost $250 |

### Report Comparison

Say you bought an iPhone for $8,999 + daily expenses $500 this month:

- **Cash Basis**: Spent $9,499 (looks like a lot!)
- **Accrual Basis**: True cost $750 ($250 depreciation + $500 expenses)

## Screenshots

(Start the app and visit http://127.0.0.1:5000 to see)

## License

MIT
