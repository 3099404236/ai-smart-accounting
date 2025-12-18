"""
AI Service - Xiaomi MiMo API Integration

Uses Anthropic API compatible format with requests library

Features:
1. Automatic item type recognition
2. Determine operating vs capital expenditure
3. Estimate asset useful life
"""

import json
import requests
from datetime import date

from config import XIAOMI_API_KEY, XIAOMI_MODEL, DEFAULT_LIFESPAN, EXPENSE_KEYWORDS
from models import AIAnalysisResult

# Anthropic API compatible endpoint
API_URL = "https://api.xiaomimimo.com/anthropic/v1/messages"


def call_mimo_api(system_prompt: str, user_message: str) -> str:
    """
    Call Xiaomi MiMo API (Anthropic format)

    Args:
        system_prompt: System prompt
        user_message: User message

    Returns:
        AI response text
    """
    headers = {
        "api-key": XIAOMI_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model": XIAOMI_MODEL,
        "max_tokens": 1024,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_message
                    }
                ]
            }
        ],
        "temperature": 0.3,
        "top_p": 0.95,
        "stream": False
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    result = response.json()

    # Extract text from Anthropic format response
    content = result.get("content", [])
    if content and len(content) > 0:
        return content[0].get("text", "")

    return ""


def analyze_expense(description: str, amount: float) -> AIAnalysisResult:
    """
    Analyze expense, determine type and estimate useful life

    Args:
        description: Expense description (e.g., "bought a wok")
        amount: Amount

    Returns:
        AIAnalysisResult: Analysis result
    """
    today = date.today()
    date_str = today.strftime("%B %d, %Y")
    weekday = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][today.weekday()]

    # Build system prompt
    system_prompt = f"""You are MiMo, a professional personal finance analysis assistant developed by Xiaomi.
Today's date: {weekday}, {date_str}. Your knowledge cutoff date is December 2024.

Your task is to analyze the user's expense record and determine:
1. Is this an "operating expense" or "capital expenditure"?
   - Operating expense: Consumed immediately, such as food, transportation, entertainment, phone bills
   - Capital expenditure: Items that can be used for a long time, such as appliances, furniture, electronics

2. If it's a capital expenditure, estimate the reasonable useful life of the item

Please return in JSON format as follows:
{{
    "is_capital": true or false,
    "category": "item category",
    "item_name": "item name",
    "useful_life_years": useful life in years (0 for operating expenses),
    "reasoning": "brief reasoning"
}}

Reference useful life:
- Phone: 3 years
- Computer/Laptop: 4-5 years
- TV: 8 years
- Refrigerator/Washing machine/AC: 10-12 years
- Cookware/Pans: 8-10 years
- Furniture: 10 years
- Clothes/Shoes: 2 years
- Bicycle: 8 years
- Car: 10 years

Notes:
- Low-value items (under $50) are usually treated as operating expenses
- Subscription services (like annual memberships) are spread over the subscription period
- Rent is spread over the lease term
- Return only JSON, no other text"""

    user_prompt = f"Please analyze this expense: {description}, amount: ${amount}"

    try:
        response_text = call_mimo_api(system_prompt, user_prompt)

        # Try to parse JSON
        # Sometimes AI adds ```json and ```, need to handle
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        return AIAnalysisResult(
            is_capital=result.get("is_capital", False),
            category=result.get("category", "Other"),
            item_name=result.get("item_name", description),
            useful_life_years=result.get("useful_life_years", 0),
            reasoning=result.get("reasoning", "")
        )

    except json.JSONDecodeError as e:
        print(f"AI response parsing failed: {e}")
        print(f"Raw response: {response_text}")
        # Fallback to rule-based analysis
        return fallback_analysis(description, amount)

    except requests.exceptions.RequestException as e:
        print(f"AI service network error: {e}")
        # Fallback to rule-based analysis
        return fallback_analysis(description, amount)

    except Exception as e:
        print(f"AI service call failed: {e}")
        # Fallback to rule-based analysis
        return fallback_analysis(description, amount)


def fallback_analysis(description: str, amount: float) -> AIAnalysisResult:
    """
    Fallback analysis (when AI service is unavailable)
    Uses simple rule-based judgment
    """
    description_lower = description.lower()

    # Check if it's an operating expense
    for keyword in EXPENSE_KEYWORDS:
        if keyword in description_lower:
            return AIAnalysisResult(
                is_capital=False,
                category="Daily Expense",
                item_name=description,
                useful_life_years=0,
                reasoning=f"Contains keyword '{keyword}', classified as operating expense"
            )

    # Check if it matches default lifespan
    for item, years in DEFAULT_LIFESPAN.items():
        if item in description_lower:
            return AIAnalysisResult(
                is_capital=True,
                category=item.title(),
                item_name=description,
                useful_life_years=years,
                reasoning=f"Matches '{item}', using default lifespan of {years} years"
            )

    # Judge by amount
    if amount < 50:
        return AIAnalysisResult(
            is_capital=False,
            category="Daily Expense",
            item_name=description,
            useful_life_years=0,
            reasoning="Low amount, treated as operating expense"
        )

    # Default as capital expenditure, use 3 years
    return AIAnalysisResult(
        is_capital=True,
        category="Other",
        item_name=description,
        useful_life_years=3,
        reasoning="Default as capital expenditure, 3 years"
    )


def estimate_purchase_impact(amount: float, useful_life_years: float) -> dict:
    """
    Estimate the impact of a purchase on living costs

    Returns:
        {
            "monthly_cost": monthly cost,
            "daily_cost": daily cost,
            "yearly_cost": yearly cost
        }
    """
    if useful_life_years <= 0:
        # Operating expense, recognized immediately
        return {
            "monthly_cost": amount,
            "daily_cost": amount / 30,
            "yearly_cost": amount * 12
        }

    months = useful_life_years * 12
    monthly_cost = amount / months
    daily_cost = amount / (useful_life_years * 365)
    yearly_cost = amount / useful_life_years

    return {
        "monthly_cost": round(monthly_cost, 2),
        "daily_cost": round(daily_cost, 2),
        "yearly_cost": round(yearly_cost, 2)
    }


if __name__ == "__main__":
    # Test
    test_cases = [
        ("bought a wok", 300),
        ("lunch today", 35),
        ("bought an iPhone 16", 7999),
        ("paid annual rent", 36000),
        ("taxi to office", 25),
        ("bought a washing machine", 2500),
    ]

    for desc, amount in test_cases:
        print(f"\nAnalyzing: {desc} (${amount})")
        result = analyze_expense(desc, amount)
        print(f"  Type: {'Capital' if result.is_capital else 'Operating'} expenditure")
        print(f"  Category: {result.category}")
        print(f"  Item: {result.item_name}")
        if result.is_capital:
            print(f"  Useful life: {result.useful_life_years} years")
            impact = estimate_purchase_impact(amount, result.useful_life_years)
            print(f"  Monthly cost: ${impact['monthly_cost']}")
        print(f"  Reasoning: {result.reasoning}")
